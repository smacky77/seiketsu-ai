"""
Circuit Breaker Pattern Implementation
Fault tolerance for external service calls
"""

import asyncio
import logging
import time
from typing import Any, Callable, Optional, Type, Union
from enum import Enum
from dataclasses import dataclass
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 3  # For half-open state
    timeout: int = 30

class CircuitBreakerException(Exception):
    """Raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 3,
        timeout: int = 30,
        expected_exception: Optional[Type[Exception]] = None
    ):
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            timeout=timeout
        )
        
        self.expected_exception = expected_exception or Exception
        
        # State tracking
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0
        self._lock = asyncio.Lock()
        
        logger.info(f"Circuit breaker initialized: threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    @property
    def state(self) -> str:
        return self._state.value
    
    @property
    def failure_count(self) -> int:
        return self._failure_count
    
    @property
    def is_closed(self) -> bool:
        return self._state == CircuitBreakerState.CLOSED
    
    @property
    def is_open(self) -> bool:
        return self._state == CircuitBreakerState.OPEN
    
    @property
    def is_half_open(self) -> bool:
        return self._state == CircuitBreakerState.HALF_OPEN
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._check_state()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if exc_type is None:
            await self._record_success()
        elif issubclass(exc_type, self.expected_exception):
            await self._record_failure()
        # Re-raise the exception
        return False
    
    async def _check_state(self):
        """Check and potentially update circuit breaker state"""
        async with self._lock:
            now = time.time()
            
            if self._state == CircuitBreakerState.OPEN:
                # Check if recovery timeout has passed
                if now - self._last_failure_time >= self.config.recovery_timeout:
                    self._state = CircuitBreakerState.HALF_OPEN
                    self._success_count = 0
                    logger.info("Circuit breaker moved to HALF_OPEN state")
                else:
                    # Still in open state, fail fast
                    remaining_time = self.config.recovery_timeout - (now - self._last_failure_time)
                    raise CircuitBreakerException(
                        f"Circuit breaker is OPEN. Recovery in {remaining_time:.1f}s"
                    )
    
    async def _record_success(self):
        """Record a successful operation"""
        async with self._lock:
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._success_count += 1
                
                if self._success_count >= self.config.success_threshold:
                    # Enough successes, close the circuit
                    self._state = CircuitBreakerState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info("Circuit breaker moved to CLOSED state after successful recovery")
            
            elif self._state == CircuitBreakerState.CLOSED:
                # Reset failure count on success
                self._failure_count = max(0, self._failure_count - 1)
    
    async def _record_failure(self):
        """Record a failed operation"""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitBreakerState.HALF_OPEN:
                # Failure during half-open, go back to open
                self._state = CircuitBreakerState.OPEN
                self._success_count = 0
                logger.warning("Circuit breaker moved back to OPEN state after failure during recovery")
            
            elif (self._state == CircuitBreakerState.CLOSED and 
                  self._failure_count >= self.config.failure_threshold):
                # Too many failures, open the circuit
                self._state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker moved to OPEN state after {self._failure_count} failures")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call a function through the circuit breaker
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerException: When circuit is open
        """
        async with self:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }
    
    def reset(self):
        """Reset circuit breaker to closed state"""
        with asyncio.Lock():
            self._state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = 0
            logger.info("Circuit breaker reset to CLOSED state")


class MultiServiceCircuitBreaker:
    """
    Circuit breaker manager for multiple services
    """
    
    def __init__(self):
        self.breakers: dict[str, CircuitBreaker] = {}
    
    def get_breaker(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Optional[Type[Exception]] = None
    ) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self.breakers:
            self.breakers[service_name] = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exception=expected_exception
            )
        return self.breakers[service_name]
    
    def get_all_stats(self) -> dict:
        """Get stats for all circuit breakers"""
        return {
            name: breaker.get_stats()
            for name, breaker in self.breakers.items()
        }
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            breaker.reset()
        logger.info("All circuit breakers reset")


# Global circuit breaker manager
circuit_breaker_manager = MultiServiceCircuitBreaker()
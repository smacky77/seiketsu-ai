"""
Rate Limiter Implementation
Token bucket and sliding window rate limiting
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    pass

@dataclass
class RateLimitConfig:
    requests_per_second: float
    burst_size: int
    window_size: int = 60  # seconds

class RateLimiterType(Enum):
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"

class TokenBucketRateLimiter:
    """
    Token bucket rate limiter implementation
    """
    
    def __init__(
        self,
        requests_per_second: float,
        burst_size: Optional[int] = None
    ):
        self.rate = requests_per_second
        self.capacity = burst_size or int(requests_per_second * 2)
        self.tokens = float(self.capacity)
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
        
        logger.debug(f"Token bucket rate limiter: {requests_per_second}/s, burst: {self.capacity}")
    
    async def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens from bucket
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired, False otherwise
            
        Raises:
            RateLimitExceeded: When rate limit is exceeded
        """
        async with self._lock:
            now = time.time()
            
            # Refill bucket based on elapsed time
            time_passed = now - self.last_refill
            new_tokens = time_passed * self.rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now
            
            # Check if enough tokens available
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            else:
                # Calculate wait time for tokens
                needed_tokens = tokens - self.tokens
                wait_time = needed_tokens / self.rate
                
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Need {tokens} tokens, have {self.tokens:.2f}. "
                    f"Wait {wait_time:.2f}s"
                )
    
    async def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without raising exception
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if acquired, False if rate limited
        """
        try:
            return await self.acquire(tokens)
        except RateLimitExceeded:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            "type": "token_bucket",
            "rate": self.rate,
            "capacity": self.capacity,
            "current_tokens": self.tokens,
            "last_refill": self.last_refill
        }

class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter implementation
    """
    
    def __init__(
        self,
        requests_per_window: int,
        window_size: int = 60  # seconds
    ):
        self.limit = requests_per_window
        self.window_size = window_size
        self.requests = []
        self._lock = asyncio.Lock()
        
        logger.debug(f"Sliding window rate limiter: {requests_per_window}/{window_size}s")
    
    async def acquire(self, requests: int = 1) -> bool:
        """
        Acquire request slots in sliding window
        
        Args:
            requests: Number of requests to acquire
            
        Returns:
            True if acquired
            
        Raises:
            RateLimitExceeded: When rate limit is exceeded
        """
        async with self._lock:
            now = time.time()
            cutoff_time = now - self.window_size
            
            # Remove old requests outside window
            self.requests = [req_time for req_time in self.requests if req_time > cutoff_time]
            
            # Check if we can accommodate new requests
            if len(self.requests) + requests <= self.limit:
                # Add new request timestamps
                for _ in range(requests):
                    self.requests.append(now)
                return True
            else:
                # Calculate when oldest request will expire
                if self.requests:
                    oldest_request = min(self.requests)
                    wait_time = oldest_request + self.window_size - now
                else:
                    wait_time = self.window_size
                
                raise RateLimitExceeded(
                    f"Rate limit exceeded. {len(self.requests)}/{self.limit} requests in window. "
                    f"Wait {wait_time:.2f}s"
                )
    
    async def try_acquire(self, requests: int = 1) -> bool:
        """Try to acquire without raising exception"""
        try:
            return await self.acquire(requests)
        except RateLimitExceeded:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        now = time.time()
        cutoff_time = now - self.window_size
        active_requests = [req for req in self.requests if req > cutoff_time]
        
        return {
            "type": "sliding_window",
            "limit": self.limit,
            "window_size": self.window_size,
            "current_requests": len(active_requests),
            "requests_remaining": max(0, self.limit - len(active_requests))
        }

class RateLimiter:
    """
    Unified rate limiter interface
    """
    
    def __init__(
        self,
        requests_per_second: float,
        burst_size: Optional[int] = None,
        limiter_type: RateLimiterType = RateLimiterType.TOKEN_BUCKET
    ):
        self.limiter_type = limiter_type
        
        if limiter_type == RateLimiterType.TOKEN_BUCKET:
            self.limiter = TokenBucketRateLimiter(
                requests_per_second=requests_per_second,
                burst_size=burst_size
            )
        else:  # SLIDING_WINDOW
            window_limit = int(requests_per_second * 60)  # Convert to per-minute
            self.limiter = SlidingWindowRateLimiter(
                requests_per_window=window_limit,
                window_size=60
            )
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens/requests"""
        return await self.limiter.acquire(tokens)
    
    async def try_acquire(self, tokens: int = 1) -> bool:
        """Try to acquire without exception"""
        return await self.limiter.try_acquire(tokens)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        return self.limiter.get_stats()

class MultiKeyRateLimiter:
    """
    Rate limiter with per-key limits
    """
    
    def __init__(
        self,
        requests_per_second: float,
        burst_size: Optional[int] = None,
        limiter_type: RateLimiterType = RateLimiterType.TOKEN_BUCKET,
        cleanup_interval: int = 300  # 5 minutes
    ):
        self.config = RateLimitConfig(
            requests_per_second=requests_per_second,
            burst_size=burst_size or int(requests_per_second * 2)
        )
        self.limiter_type = limiter_type
        self.limiters: Dict[str, RateLimiter] = {}
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
        self._lock = asyncio.Lock()
    
    def _get_or_create_limiter(self, key: str) -> RateLimiter:
        """Get or create rate limiter for key"""
        if key not in self.limiters:
            self.limiters[key] = RateLimiter(
                requests_per_second=self.config.requests_per_second,
                burst_size=self.config.burst_size,
                limiter_type=self.limiter_type
            )
        return self.limiters[key]
    
    async def acquire(self, key: str, tokens: int = 1) -> bool:
        """
        Acquire tokens for specific key
        
        Args:
            key: Rate limit key (e.g., client_id, IP address)
            tokens: Number of tokens to acquire
            
        Returns:
            True if acquired
            
        Raises:
            RateLimitExceeded: When rate limit exceeded for key
        """
        async with self._lock:
            # Periodic cleanup of old limiters
            await self._cleanup_if_needed()
            
            limiter = self._get_or_create_limiter(key)
            
        # Acquire outside of global lock to avoid blocking other keys
        return await limiter.acquire(tokens)
    
    async def try_acquire(self, key: str, tokens: int = 1) -> bool:
        """Try to acquire for key without exception"""
        try:
            return await self.acquire(key, tokens)
        except RateLimitExceeded:
            return False
    
    async def _cleanup_if_needed(self):
        """Clean up unused rate limiters periodically"""
        now = time.time()
        
        if now - self.last_cleanup > self.cleanup_interval:
            # Simple cleanup - remove limiters that haven't been used recently
            # In production, you might want more sophisticated cleanup logic
            keys_to_remove = []
            
            for key, limiter in self.limiters.items():
                stats = limiter.get_stats()
                
                # Remove if token bucket is full (unused) or sliding window is empty
                if (stats.get("current_tokens", 0) >= stats.get("capacity", 0) or
                    stats.get("current_requests", 0) == 0):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.limiters[key]
            
            self.last_cleanup = now
            
            if keys_to_remove:
                logger.debug(f"Cleaned up {len(keys_to_remove)} unused rate limiters")
    
    def get_stats(self, key: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for key or all keys"""
        if key:
            if key in self.limiters:
                return {key: self.limiters[key].get_stats()}
            else:
                return {key: "no_limiter"}
        else:
            return {
                "total_keys": len(self.limiters),
                "config": {
                    "requests_per_second": self.config.requests_per_second,
                    "burst_size": self.config.burst_size,
                    "limiter_type": self.limiter_type.value
                },
                "per_key_stats": {
                    key: limiter.get_stats()
                    for key, limiter in self.limiters.items()
                }
            }

# Decorator for rate limiting functions
def rate_limit(
    requests_per_second: float,
    burst_size: Optional[int] = None,
    key_func: Optional[callable] = None
):
    """
    Decorator for rate limiting function calls
    
    Args:
        requests_per_second: Rate limit
        burst_size: Burst capacity
        key_func: Function to extract rate limit key from args
    """
    limiter = RateLimiter(requests_per_second, burst_size)
    multi_limiter = MultiKeyRateLimiter(requests_per_second, burst_size) if key_func else None
    
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            if key_func and multi_limiter:
                key = key_func(*args, **kwargs)
                await multi_limiter.acquire(key)
            else:
                await limiter.acquire()
            
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we'd need to run in an event loop
            # This is a simplified implementation
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
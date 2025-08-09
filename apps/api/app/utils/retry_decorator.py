"""
Retry Decorator with Exponential Backoff
Handles transient failures with configurable retry logic
"""

import asyncio
import logging
import random
import time
from typing import Any, Callable, Optional, Type, Tuple, Union
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RetryConfig:
    max_attempts: int = 3
    backoff_factor: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    exceptions: Tuple[Type[Exception], ...] = (Exception,)

class RetryExhausted(Exception):
    """Raised when all retry attempts have been exhausted"""
    def __init__(self, attempts: int, last_exception: Exception):
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(f"Retry exhausted after {attempts} attempts. Last error: {last_exception}")

def calculate_backoff_delay(
    attempt: int,
    backoff_factor: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """
    Calculate delay for retry attempt with exponential backoff
    
    Args:
        attempt: Current attempt number (0-based)
        backoff_factor: Multiplier for exponential backoff
        max_delay: Maximum delay in seconds
        jitter: Add random jitter to prevent thundering herd
        
    Returns:
        Delay in seconds
    """
    # Exponential backoff: backoff_factor * (2 ** attempt)
    delay = backoff_factor * (2 ** attempt)
    
    # Cap at max_delay
    delay = min(delay, max_delay)
    
    # Add jitter (random variation ±25%)
    if jitter:
        jitter_amount = delay * 0.25
        delay = delay + random.uniform(-jitter_amount, jitter_amount)
        # Ensure non-negative delay
        delay = max(0, delay)
    
    return delay

def should_retry(
    exception: Exception,
    retry_exceptions: Tuple[Type[Exception], ...],
    attempt: int,
    max_attempts: int
) -> bool:
    """
    Determine if we should retry based on exception type and attempt count
    
    Args:
        exception: Exception that was raised
        retry_exceptions: Tuple of exception types to retry on
        attempt: Current attempt number
        max_attempts: Maximum number of attempts
        
    Returns:
        True if should retry, False otherwise
    """
    # Check if we've exceeded max attempts
    if attempt >= max_attempts:
        return False
    
    # Check if exception type is retryable
    return isinstance(exception, retry_exceptions)

def retry_async(
    max_attempts: int = 3,
    backoff_factor: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    Async retry decorator with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Base delay multiplier for exponential backoff
        max_delay: Maximum delay between retries in seconds
        jitter: Add random jitter to delays
        exceptions: Tuple of exception types to retry on
        on_retry: Optional callback called on each retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    # Call the function
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    
                    # Success - return result
                    if attempt > 0:
                        logger.info(f"Function {func.__name__} succeeded on attempt {attempt + 1}")
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if not should_retry(e, exceptions, attempt + 1, max_attempts):
                        logger.error(f"Function {func.__name__} failed with non-retryable exception: {e}")
                        raise e
                    
                    # Calculate delay for next attempt
                    if attempt < max_attempts - 1:  # Don't delay after last attempt
                        delay = calculate_backoff_delay(
                            attempt=attempt,
                            backoff_factor=backoff_factor,
                            max_delay=max_delay,
                            jitter=jitter
                        )
                        
                        logger.warning(
                            f"Function {func.__name__} failed on attempt {attempt + 1}/{max_attempts}. "
                            f"Error: {e}. Retrying in {delay:.2f}s"
                        )
                        
                        # Call retry callback if provided
                        if on_retry:
                            try:
                                if asyncio.iscoroutinefunction(on_retry):
                                    await on_retry(attempt + 1, e)
                                else:
                                    on_retry(attempt + 1, e)
                            except Exception as callback_error:
                                logger.error(f"Retry callback failed: {callback_error}")
                        
                        # Wait before retrying
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts. "
                            f"Last error: {e}"
                        )
            
            # All attempts exhausted
            raise RetryExhausted(max_attempts, last_exception)
        
        return wrapper
    return decorator

def retry_sync(
    max_attempts: int = 3,
    backoff_factor: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    Synchronous retry decorator with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Base delay multiplier for exponential backoff
        max_delay: Maximum delay between retries in seconds
        jitter: Add random jitter to delays
        exceptions: Tuple of exception types to retry on
        on_retry: Optional callback called on each retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    # Call the function
                    result = func(*args, **kwargs)
                    
                    # Success - return result
                    if attempt > 0:
                        logger.info(f"Function {func.__name__} succeeded on attempt {attempt + 1}")
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if not should_retry(e, exceptions, attempt + 1, max_attempts):
                        logger.error(f"Function {func.__name__} failed with non-retryable exception: {e}")
                        raise e
                    
                    # Calculate delay for next attempt
                    if attempt < max_attempts - 1:  # Don't delay after last attempt
                        delay = calculate_backoff_delay(
                            attempt=attempt,
                            backoff_factor=backoff_factor,
                            max_delay=max_delay,
                            jitter=jitter
                        )
                        
                        logger.warning(
                            f"Function {func.__name__} failed on attempt {attempt + 1}/{max_attempts}. "
                            f"Error: {e}. Retrying in {delay:.2f}s"
                        )
                        
                        # Call retry callback if provided
                        if on_retry:
                            try:
                                on_retry(attempt + 1, e)
                            except Exception as callback_error:
                                logger.error(f"Retry callback failed: {callback_error}")
                        
                        # Wait before retrying
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts. "
                            f"Last error: {e}"
                        )
            
            # All attempts exhausted
            raise RetryExhausted(max_attempts, last_exception)
        
        return wrapper
    return decorator

class RetryContext:
    """
    Context manager for retry logic
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        backoff_factor: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable[[int, Exception], None]] = None
    ):
        self.config = RetryConfig(
            max_attempts=max_attempts,
            backoff_factor=backoff_factor,
            max_delay=max_delay,
            jitter=jitter,
            exceptions=exceptions
        )
        self.on_retry = on_retry
        self.attempt = 0
        self.last_exception = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False  # No exception, exit normally
        
        self.last_exception = exc_val
        self.attempt += 1
        
        # Check if we should retry
        if should_retry(exc_val, self.config.exceptions, self.attempt, self.config.max_attempts):
            # Calculate delay
            delay = calculate_backoff_delay(
                attempt=self.attempt - 1,
                backoff_factor=self.config.backoff_factor,
                max_delay=self.config.max_delay,
                jitter=self.config.jitter
            )
            
            logger.warning(
                f"Retry attempt {self.attempt}/{self.config.max_attempts}. "
                f"Error: {exc_val}. Retrying in {delay:.2f}s"
            )
            
            # Call retry callback
            if self.on_retry:
                try:
                    if asyncio.iscoroutinefunction(self.on_retry):
                        await self.on_retry(self.attempt, exc_val)
                    else:
                        self.on_retry(self.attempt, exc_val)
                except Exception as callback_error:
                    logger.error(f"Retry callback failed: {callback_error}")
            
            # Wait before retry
            await asyncio.sleep(delay)
            
            # Suppress the exception to retry
            return True
        
        # Don't suppress - let exception propagate
        return False

# Convenience function for programmatic retry
async def retry_call(
    func: Callable,
    *args,
    max_attempts: int = 3,
    backoff_factor: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    **kwargs
) -> Any:
    """
    Call a function with retry logic
    
    Args:
        func: Function to call
        *args: Function arguments
        max_attempts: Maximum retry attempts
        backoff_factor: Exponential backoff factor
        max_delay: Maximum delay between retries
        jitter: Add random jitter to delays
        exceptions: Exception types to retry on
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
        
    Raises:
        RetryExhausted: When all retry attempts fail
    """
    @retry_async(
        max_attempts=max_attempts,
        backoff_factor=backoff_factor,
        max_delay=max_delay,
        jitter=jitter,
        exceptions=exceptions
    )
    async def wrapper():
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    return await wrapper()

# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    # Example of using retry decorator
    @retry_async(max_attempts=3, backoff_factor=0.5)
    async def unreliable_function():
        """Simulates an unreliable function that fails randomly"""
        import random
        if random.random() < 0.7:  # 70% chance of failure
            raise Exception("Random failure")
        return "Success!"
    
    async def test_retry():
        try:
            result = await unreliable_function()
            print(f"Result: {result}")
        except RetryExhausted as e:
            print(f"All retries failed: {e}")
    
    # Run test
    asyncio.run(test_retry())
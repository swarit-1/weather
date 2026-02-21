"""Timer utilities for performance tracking."""

import time
from functools import wraps
from typing import Callable, Any
from app.utils.logging import logger

def timer(func: Callable) -> Callable:
    """Decorator to time function execution."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"{func.__name__} took {elapsed:.3f} seconds")
        return result
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"{func.__name__} took {elapsed:.3f} seconds")
        return result
    
    # Return async or sync wrapper based on function
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

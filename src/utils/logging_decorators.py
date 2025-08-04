import functools
import logging
import time
from typing import Callable, Any

def log_function_call(func: Callable) -> Callable:
    """
    Decorator to log function entry and exit, along with time taken.
    
    Args:
        func: The function to be decorated.
        
    Returns:
        The decorated function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        
        logger.info(f"Entering function: {func.__name__}")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Exiting function: {func.__name__} - Execution time: {execution_time:.4f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Exception in {func.__name__} after {execution_time:.4f}s: {str(e)}")
            raise
            
    return wrapper

def log_method_call(method: Callable) -> Callable:
    """
    Decorator specifically for class methods, which handles 'self' correctly.
    
    Args:
        method: The class method to be decorated.
        
    Returns:
        The decorated method.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        logger = logging.getLogger(self.__class__.__module__)
        method_name = f"{self.__class__.__name__}.{method.__name__}"
        
        logger.info(f"Entering method: {method_name}")
        start_time = time.time()
        
        try:
            result = method(self, *args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Exiting method: {method_name} - Execution time: {execution_time:.4f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Exception in {method_name} after {execution_time:.4f}s: {str(e)}")
            raise
            
    return wrapper
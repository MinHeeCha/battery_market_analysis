"""
Retry handler - implements exponential backoff and retry logic
"""
import time
from typing import Callable, Any, Optional
from shared.logger import get_logger
from config.settings import config

logger = get_logger(__name__)


class RetryHandler:
    """Handles retry logic for failed agent executions"""
    
    def __init__(self, max_retries: int = None, initial_delay: int = None):
        self.max_retries = max_retries or config.max_retries
        self.initial_delay = initial_delay or config.retry_delay
    
    def retry_with_backoff(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """
        Execute function with exponential backoff retry.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or None if all retries failed
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Attempt {attempt + 1}/{self.max_retries + 1} for {func.__name__}")
                result = func(*args, **kwargs)
                logger.info(f"Success on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.initial_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
        
        if last_exception:
            raise last_exception
        
        return None

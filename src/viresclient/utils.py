import time
from functools import wraps
from logging import getLogger

LOGGER = getLogger(__name__)

def retry_on_exception(retries=3, delay=1, exceptions=(Exception,), logger=LOGGER):
    """
    A decorator to retry a function if a specific exception is raised.

    Args:
        retries (int): Number of retries before giving up.
        delay (int): Delay in seconds between retries.
        exception (Exception): The exception to catch and retry on.

    Returns:
        Function wrapper that retries the function call.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts >= retries:
                        raise
                    logger.info(f"Retrying {func.__name__} due to {type(e).__name__}: {e}. Attempt {attempts} of {retries}.")
                    time.sleep(delay)
        return wrapper
    return decorator

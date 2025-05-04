"""Retry utilities for Azure service operations."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from azure.core.exceptions import AzureError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

T = TypeVar("T")


def azure_retry(
    max_attempts: int = 3, min_wait: int = 4, max_wait: int = 10
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying Azure operations with exponential backoff.

    This decorator provides resilient retry logic for Azure operations that may fail
    transiently. It uses exponential backoff to avoid overwhelming the service.

    Args:
        max_attempts (int): Maximum number of retry attempts. Defaults to 3.
        min_wait (int): Minimum wait time between retries in seconds. Defaults to 4.
        max_wait (int): Maximum wait time between retries in seconds. Defaults to 10.

    Returns:
        Callable: Decorated function with retry logic

    Example:
        ```python
        @azure_retry(max_attempts=5, min_wait=2, max_wait=30)
        def call_azure_service():
            # Make Azure API call
            pass
        ```
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(AzureError),
            reraise=True,
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return func(*args, **kwargs)

        return wrapper

    return decorator

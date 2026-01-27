"""Enhanced retry decorator with cache fallback integration.

Provides automatic retry with exponential backoff and cache fallback
for API and data fetching operations.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from functools import wraps
from typing import TYPE_CHECKING, TypeVar

from helper_functions.api_utils.cache import API_RESPONSE_TTL, get_cached, set_cached
from helper_functions.api_utils.exceptions import (
    ScoreboardError,
)
from helper_functions.logging.logger_config import logger, track_retry

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")


@dataclass
class BackoffConfig:
    """Backoff parameters for retry logic."""

    initial_delay: float = 1.0
    max_delay: float = 30.0
    backoff_multiplier: float = 2.0


def retry_with_fallback(
    max_attempts: int = 3,
    *,
    backoff: BackoffConfig | None = None,
    use_cache_fallback: bool = True,
    cache_ttl: int = API_RESPONSE_TTL,
    max_stale_age: int | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Automatically retry with exponential backoff and cache fallback.

    Checks exception.recoverable flag to determine if retry should be attempted.
    Falls back to cached data when all retries exhausted (if use_cache_fallback=True).

    :param max_attempts: Maximum retry attempts (default: 3)
    :param backoff: Backoff configuration (initial delay, max delay, multiplier)
    :param use_cache_fallback: Use cached data as fallback (default: True)
    :param cache_ttl: Cache TTL for successful responses (default: API_RESPONSE_TTL)
    :param max_stale_age: Maximum age of stale cache in seconds (None = unlimited)
    :return: Decorated function
    """
    backoff_cfg = backoff or BackoffConfig()
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> T:
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{':'.join(str(arg) for arg in args)}"
            last_exception: Exception | None = None

            for attempt in range(max_attempts):
                try:
                    # Execute function
                    result = func(*args, **kwargs)

                except Exception as e:
                    last_exception = e
                    is_recoverable = False

                    # Track retry attempt
                    track_retry(func.__name__, attempt + 1, max_attempts)

                    # Check if exception is recoverable
                    if isinstance(e, ScoreboardError):
                        is_recoverable = e.recoverable
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: "
                            f"{e.message} (recoverable={is_recoverable}, code={e.error_code})",
                        )
                    else:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {e!s} "
                            f"(non-recoverable)",
                        )

                    # If not recoverable or last attempt, break immediately
                    if not is_recoverable or attempt >= max_attempts - 1:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(
                        backoff_cfg.initial_delay * (backoff_cfg.backoff_multiplier ** attempt),
                        backoff_cfg.max_delay,
                    )
                    logger.info(f"Retrying {func.__name__} in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    if use_cache_fallback:
                        set_cached(cache_key, result, ttl=cache_ttl)
                        logger.debug(f"Cached successful result for {func.__name__}")

                    return result

            # All retries exhausted - try cache fallback
            if use_cache_fallback:
                cached_data = get_cached(cache_key, max_age=max_stale_age)
                if cached_data is not None:
                    logger.warning(
                        f"All retries failed for {func.__name__}. "
                        f"Using cached data as fallback.",
                    )
                    return cached_data
                if max_stale_age is not None:
                    logger.warning(
                        f"Cached data for {func.__name__} too old (>{max_stale_age}s). "
                        f"Not using stale fallback.",
                    )

            # No cache available - raise the last exception
            logger.error(
                f"All retries failed for {func.__name__} and no cache available. "
                f"Raising exception.",
            )
            if last_exception:
                raise last_exception
            msg = f"Retry logic failed for {func.__name__}"
            raise RuntimeError(msg)

        return wrapper
    return decorator


def retry_api_call(
    func: Callable[..., T] | None = None,
    *,
    max_attempts: int = 3,
    use_cache: bool = True,
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
    """Simplified retry decorator for API calls with sensible defaults.

    Can be used with or without arguments:
        @retry_api_call
        def my_function():
            ...

        @retry_api_call(max_attempts=5)
        def my_other_function():
            ...

    :param func: Function to decorate (when used without arguments)
    :param max_attempts: Maximum retry attempts
    :param use_cache: Whether to use cache fallback
    :return: Decorated function or decorator
    """
    def decorator(f: Callable[..., T]) -> Callable[..., T]:
        return retry_with_fallback(
            max_attempts=max_attempts,
            backoff=BackoffConfig(initial_delay=1.0, max_delay=30.0, backoff_multiplier=2.0),
            use_cache_fallback=use_cache,
        )(f)

    if func is None:
        # Called with arguments: @retry_api_call(max_attempts=5)
        return decorator
    # Called without arguments: @retry_api_call
    return decorator(func)

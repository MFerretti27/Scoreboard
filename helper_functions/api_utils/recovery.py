"""Recovery strategies for handling various failure scenarios.

Implements retry logic, exponential backoff, and fallback mechanisms
for network and API failures.
"""
from __future__ import annotations

import secrets
import time
from typing import TYPE_CHECKING, Any, TypeVar

from helper_functions.api_utils.exceptions import APIError, DataValidationError, NetworkError
from helper_functions.logging.logger_config import logger

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        *,
        jitter: bool = True,
    ) -> None:
        """Initialize RetryConfig.

        :param max_attempts: Maximum number of retry attempts
        :param initial_delay: Initial delay in seconds between retries
        :param max_delay: Maximum delay between retries
        :param exponential_base: Base for exponential backoff calculation
        :param jitter: Whether to add randomness to delays
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number.

        :param attempt: Current attempt number (0-indexed)
        :return: Delay in seconds
        """
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay,
        )

        if self.jitter:
            # Add random jitter: ±20% of delay
            jitter_amount = delay * 0.2
            # secrets.randbelow returns [0, n), so we map to [-jitter_amount, jitter_amount]
            delay += (secrets.randbelow(int(jitter_amount * 2000)) / 1000.0) - jitter_amount

        return max(0, delay)  # Ensure delay is non-negative


class RetryManager:
    """Manages retry logic with exponential backoff for API calls."""

    DEFAULT_CONFIG = RetryConfig(max_attempts=3, initial_delay=1.0, max_delay=30.0)

    def __init__(self, config: RetryConfig | None = None) -> None:
        """Initialize RetryManager.

        :param config: Retry configuration (uses defaults if None)
        """
        self.config = config or self.DEFAULT_CONFIG

    def retry_with_backoff(
        self,
        func: Callable[..., T],
        *args: object,
        **kwargs: object,
    ) -> T:
        """Execute function with automatic retry and exponential backoff.

        :param func: Function to execute
        :param args: Positional arguments for func
        :param kwargs: Keyword arguments for func
        :return: Result from func
        :raises NetworkError: If network connectivity fails after all retries
        :raises APIError: If API request fails after all retries
        """
        last_exception: Exception | None = None

        for attempt in range(self.config.max_attempts):
            try:
                return func(*args, **kwargs)
            except (NetworkError, APIError, DataValidationError) as e:
                last_exception = e
                if attempt < self.config.max_attempts - 1:
                    delay = self.config.get_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e.message}. "
                        f"Retrying in {delay:.1f}s...",
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.config.max_attempts} attempts failed: {e.message}")

        # If we exhausted all retries, raise the last exception
        if last_exception:
            raise last_exception

        # Should not reach here, but for type safety
        msg = "Retry logic failed unexpectedly"
        raise RuntimeError(msg)

    def is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable.

        :param error: Exception to check
        :return: True if the error is retryable
        """
        if isinstance(error, (NetworkError, APIError, DataValidationError)):
            return error.recoverable
        return False


class CircuitBreaker:
    """Circuit breaker pattern to prevent cascading failures.

    Stops making requests after repeated failures for a period of time.
    """

    def __init__(self, failure_threshold: int = 5, timeout_seconds: float = 300.0) -> None:
        """Initialize CircuitBreaker.

        :param failure_threshold: Number of failures before opening circuit
        :param timeout_seconds: Time to wait before attempting to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.is_open = False

    def call(self, func: Callable[..., T], *args: object, **kwargs: object) -> T:
        """Execute function with circuit breaker protection.

        :param func: Function to execute
        :param args: Positional arguments for func
        :param kwargs: Keyword arguments for func
        :return: Result from func
        :raises RuntimeError: If circuit is open
        """
        if self.is_open:
            if self._should_attempt_reset():
                self.is_open = False
                self.failure_count = 0
                logger.info("Circuit breaker attempting reset")
            else:
                msg = "Circuit breaker is open - service unavailable"
                raise RuntimeError(msg)

        try:
            result = func(*args, **kwargs)
            self._on_success()
        except Exception:
            self._on_failure()
            raise
        else:
            return result

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        self.last_failure_time = None

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.error(
                f"Circuit breaker opened after {self.failure_count} failures. "
                f"Halting requests for {self.timeout_seconds}s",
            )

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset.

        :return: True if reset should be attempted
        """
        if self.last_failure_time is None:
            return False
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.timeout_seconds


class FallbackDataProvider:
    """Provides fallback data when primary sources fail.

    Maintains a cache of the last successful response to use during outages.
    """

    def __init__(self) -> None:
        """Initialize FallbackDataProvider."""
        self.cache: dict[str, Any] = {}
        self.cache_timestamps: dict[str, float] = {}

    def cache_data(self, key: str, data: object) -> None:
        """Cache data with current timestamp.

        :param key: Cache key (e.g., team name or league)
        :param data: Data to cache
        """
        self.cache[key] = data
        self.cache_timestamps[key] = time.time()
        logger.debug(f"Cached data for key: {key}")

    def get_cached_data(self, key: str, max_age_seconds: float = 3600.0) -> object | None:
        """Retrieve cached data if it exists and is not too old.

        :param key: Cache key
        :param max_age_seconds: Maximum age of cached data in seconds
        :return: Cached data or None if not found or too old
        """
        if key not in self.cache:
            return None

        age = time.time() - self.cache_timestamps[key]
        if age > max_age_seconds:
            logger.info(f"Cached data for {key} is too old ({age:.0f}s > {max_age_seconds:.0f}s)")
            return None

        logger.debug(f"Using cached data for key: {key} (age: {age:.0f}s)")
        return self.cache[key]

    def clear_cache(self, key: str | None = None) -> None:
        """Clear cache for specific key or all keys.

        :param key: Cache key to clear (all if None)
        """
        if key is None:
            self.cache.clear()
            self.cache_timestamps.clear()
            logger.info("Cleared all cached data")
        else:
            self.cache.pop(key, None)
            self.cache_timestamps.pop(key, None)
            logger.info(f"Cleared cached data for key: {key}")

"""Circuit breaker pattern for preventing cascading failures.

Monitors endpoint health and automatically stops sending requests to failing endpoints
to preserve resources and enable faster recovery.

States:
- CLOSED (normal): Requests pass through, failures counted
- OPEN (circuit open): Requests fail immediately without calling endpoint
- HALF_OPEN (testing): Limited requests allowed to test endpoint recovery
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import TYPE_CHECKING, Any, TypeVar

from helper_functions.exceptions import APIError
from helper_functions.logger_config import logger

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Circuit open, requests fail immediately
    HALF_OPEN = "half_open"  # Testing recovery, limited requests allowed


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior.

    :param failure_threshold: Number of failures before opening circuit
    :param recovery_timeout: Seconds to wait before attempting recovery
    :param success_threshold: Successful requests needed in half-open state to close circuit
    :param name: Circuit breaker name for logging
    """

    failure_threshold: int = 5  # Open after 5 failures
    recovery_timeout: int = 60  # Try recovery after 60 seconds
    success_threshold: int = 2  # Need 2 successes to close
    name: str = "circuit"


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures.

    Monitors endpoint health and stops requests when failure rate exceeds threshold.

    Example:
        breaker = CircuitBreaker(config=CircuitBreakerConfig(name="nba_api"))
        result = breaker.call(get_nba_data, team)  # Auto-fails if circuit open

    """

    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        """Initialize circuit breaker.

        :param config: CircuitBreakerConfig with thresholds and timeouts
        """
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: float | None = None
        self.opened_at: float | None = None
        self._lock = Lock()

        logger.info(
            f"CircuitBreaker '{self.config.name}' initialized: "
            f"threshold={self.config.failure_threshold}, "
            f"timeout={self.config.recovery_timeout}s",
        )

    def call(self, func: Callable[..., T], *args: object, **kwargs: object) -> T:
        """Execute function with circuit breaker protection.

        :param func: Function to call
        :param args: Positional arguments for function
        :param kwargs: Keyword arguments for function
        :return: Function result
        :raises APIError: If circuit is open or function fails
        """
        with self._lock:
            # Check if circuit should transition from OPEN to HALF_OPEN
            if self.state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"CircuitBreaker '{self.config.name}': OPEN → HALF_OPEN (attempting recovery)")
                else:
                    msg = f"CircuitBreaker '{self.config.name}' is OPEN. Endpoint unavailable."
                    raise APIError(
                        msg,
                        error_code="CIRCUIT_OPEN",
                    )

        # Execute function
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.state == CircuitState.HALF_OPEN:
                    # Failure during recovery attempt
                    self.state = CircuitState.OPEN
                    self.opened_at = time.time()
                    logger.warning(
                        f"CircuitBreaker '{self.config.name}': "
                        f"HALF_OPEN → OPEN (recovery failed). "
                        f"Error: {e!s}",
                    )

                elif self.failure_count >= self.config.failure_threshold:
                    # Threshold exceeded, open circuit
                    self.state = CircuitState.OPEN
                    self.opened_at = time.time()
                    logger.error(
                        f"CircuitBreaker '{self.config.name}': "
                        f"CLOSED → OPEN (failure threshold {self.config.failure_threshold} exceeded). "
                        f"Error: {e!s}",
                    )
            raise
        else:
            with self._lock:
                self.failure_count = 0
                self.last_failure_time = None

                if self.state == CircuitState.HALF_OPEN:
                    self.success_count += 1

                    if self.success_count >= self.config.success_threshold:
                        self.state = CircuitState.CLOSED
                        logger.info(
                            "CircuitBreaker '%s': HALF_OPEN → CLOSED (recovery successful)",
                            self.config.name,
                        )

            return result

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery.

        :return: True if recovery timeout has elapsed
        """
        if self.opened_at is None:
            return False

        elapsed = time.time() - self.opened_at
        return elapsed >= self.config.recovery_timeout

    def get_state(self) -> dict[str, Any]:
        """Get current circuit breaker state for monitoring.

        :return: Dict with state, failure count, and timing info
        """
        with self._lock:
            state_dict = {
                "name": self.config.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time,
                "opened_at": self.opened_at,
            }

            if self.state == CircuitState.OPEN and self.opened_at:
                elapsed = time.time() - self.opened_at
                time_until_recovery = max(0, self.config.recovery_timeout - elapsed)
                state_dict["time_until_recovery_attempt"] = round(time_until_recovery, 1)

            return state_dict

    def reset(self) -> None:
        """Reset circuit breaker to closed state.

        Use after manual intervention or when endpoint is confirmed recovered.
        """
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            self.opened_at = None

        logger.info(f"CircuitBreaker '{self.config.name}' reset to CLOSED state")


# Global circuit breakers for each API
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
    """Get or create a circuit breaker for an endpoint.

    :param name: Unique name for the circuit breaker (e.g., 'nba_api', 'nhl_api')
    :param config: Optional configuration; uses defaults if not provided
    :return: CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        if config is None:
            config = CircuitBreakerConfig(name=name)
        else:
            config.name = name

        _circuit_breakers[name] = CircuitBreaker(config)

    return _circuit_breakers[name]


def reset_circuit_breaker(name: str) -> None:
    """Reset a specific circuit breaker.

    :param name: Name of circuit breaker to reset
    """
    if name in _circuit_breakers:
        _circuit_breakers[name].reset()


def get_all_circuit_states() -> dict[str, dict[str, Any]]:
    """Get state of all circuit breakers.

    Useful for monitoring and debugging.

    :return: Dict of {name: state_dict} for all active breakers
    """
    return {name: breaker.get_state() for name, breaker in _circuit_breakers.items()}

"""Custom exception classes for the Scoreboard application.

Provides structured error handling for different failure scenarios:
- Network connectivity issues
- API/data fetching failures
- Configuration/validation errors
"""
from __future__ import annotations


class ScoreboardError(Exception):
    """Base exception class for all Scoreboard application errors."""

    def __init__(self, message: str, error_code: str | None = None, *, recoverable: bool = False) -> None:
        """Initialize ScoreboardError.

        :param message: Human-readable error message
        :param error_code: Machine-readable error identifier
        :param recoverable: Whether automatic recovery is possible
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN"
        self.recoverable = recoverable


class NetworkError(ScoreboardError):
    """Raised when network connectivity is unavailable or fails.

    This error is recoverable - the application can retry with backoff.
    """

    def __init__(self, message: str, error_code: str | None = None) -> None:
        """Initialize NetworkError."""
        super().__init__(message, error_code or "NET_UNREACHABLE", recoverable=True)


class APIError(ScoreboardError):
    """Raised when API requests fail (timeouts, invalid responses, rate limits).

    This error is typically recoverable with exponential backoff.
    """

    def __init__(self, message: str, status_code: int | None = None, error_code: str | None = None) -> None:
        """Initialize APIError.

        :param message: Human-readable error message
        :param status_code: HTTP status code (if applicable)
        :param error_code: Specific API error identifier
        """
        super().__init__(message, error_code or f"API_ERROR_{status_code or 'UNKNOWN'}", recoverable=True)
        self.status_code = status_code


class DataValidationError(ScoreboardError):
    """Raised when API response data is invalid or missing required fields.

    This error may be recoverable by retrying the API call.
    """

    def __init__(self, message: str, missing_fields: list[str] | None = None) -> None:
        """Initialize DataValidationError.

        :param message: Human-readable error message
        :param missing_fields: List of missing required fields
        """
        super().__init__(message, "DATA_VALIDATION_FAILED", recoverable=True)
        self.missing_fields = missing_fields or []


class ConfigurationError(ScoreboardError):
    """Raised when configuration is invalid or missing.

    This error is NOT recoverable without user intervention.
    """

    def __init__(self, message: str, setting_name: str | None = None) -> None:
        """Initialize ConfigurationError.

        :param message: Human-readable error message
        :param setting_name: Name of the invalid setting
        """
        super().__init__(message, f"CONFIG_ERROR_{setting_name or 'UNKNOWN'}", recoverable=False)
        self.setting_name = setting_name


class DataFetchError(ScoreboardError):
    """Raised when data fetching fails for a specific team or league.

    This error is recoverable and is the primary error for missing team data.
    """

    def __init__(self, message: str, team: str | None = None, league: str | None = None) -> None:
        """Initialize DataFetchError.

        :param message: Human-readable error message
        :param team: Team that failed to fetch
        :param league: League that failed to fetch
        """
        super().__init__(message, f"DATA_FETCH_FAILED_{league or 'UNKNOWN'}", recoverable=True)
        self.team = team
        self.league = league

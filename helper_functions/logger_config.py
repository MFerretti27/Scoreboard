"""Create Logging config."""
from __future__ import annotations

import contextlib
import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

from .email import email_config_status, notify_email

THROTTLE_SECONDS = 60  # debounce identical error messages

# Context variables for structured logging
log_context: ContextVar[dict[str, Any] | None] = ContextVar("log_context", default=None)

# Performance metrics tracking
performance_metrics: dict[str, dict[str, Any]] = {
    "api_calls": {},
    "cache_stats": {"hits": 0, "misses": 0},
    "retry_stats": {},
    "validation_stats": {"passed": 0, "failed": 0},
}


class ThrottleFilter(logging.Filter):
    """Suppress identical messages within a time window to reduce log spam."""

    def __init__(self, window: float) -> None:
        """Docstring for __init__."""
        super().__init__()
        self.window = window
        self.last_emit: dict[tuple[int, str], float] = {}

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records to suppress identical messages within the time window.

        Params: the record should be logged, False if it should be suppressed.

        returns: bool
        """
        key = (record.levelno, record.getMessage())
        now = time.monotonic()
        last = self.last_emit.get(key)
        if last is not None and (now - last) < self.window:
            return False
        self.last_emit[key] = now
        return True


class ContextualFormatter(logging.Formatter):
    """Formatter that includes contextual information from ContextVar."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with contextual information."""
        context = log_context.get({})
        if context:
            # Add context to the record as extra fields
            for key, value in context.items():
                setattr(record, key, value)

            # Build context string for message
            context_parts = []
            if "team" in context:
                context_parts.append(f"team={context['team']}")
            if "league" in context:
                context_parts.append(f"league={context['league']}")
            if "endpoint" in context:
                context_parts.append(f"endpoint={context['endpoint']}")
            if "duration_ms" in context:
                context_parts.append(f"duration={context['duration_ms']:.0f}ms")

            if context_parts:
                record.msg = f"[{' | '.join(context_parts)}] {record.msg}"

        return super().format(record)


class EmailNotificationHandler(logging.Handler):
    """Custom handler that sends email notifications on exceptions."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record by sending an email."""
        if record.levelno >= logging.ERROR:
            try:
                enabled, ok, reason = email_config_status()
                if enabled and not ok:
                    logger.warning("Email notifications enabled but not configured: %s", reason)
                    return
                notify_email()
                logger.info("Diagnostic email sent to improve scoreboard functionality.")
            except Exception as e:
                logger.info("Failed to send diagnostic email: %s", e)


class SpacedErrorFormatter(logging.Formatter):
    """Custom formatter that adds whitespace between error entries."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with separator lines."""
        formatted = super().format(record)
        # Add separator lines before the error entry
        separator = "\n\n" + "=" * 80 + "\n\n"
        return separator + formatted + "\n\n"


class InfoLogHandler(logging.FileHandler):
    """File handler that maintains only the last 1000 lines of info logs."""

    MAX_LINES = 5000

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record and trim file to max lines."""
        super().emit(record)
        self.flush()  # Ensure written to disk
        with contextlib.suppress(Exception):
            self._trim_to_max_lines()

    def _trim_to_max_lines(self) -> None:
        """Keep only the last MAX_LINES lines in the log file."""
        log_path = Path(self.baseFilename)
        if not log_path.exists():
            return

        try:
            lines = log_path.read_text().splitlines(keepends=True)
            if len(lines) > self.MAX_LINES:
                trimmed = lines[-self.MAX_LINES :]
                log_path.write_text("".join(trimmed))
        except Exception as e:
            # Log trim errors to stderr to avoid recursion
            logging.getLogger(__name__).debug("Failed to trim log file %s: %s", log_path, e)


logging.getLogger("httpx").setLevel(logging.WARNING)  # Ignore httpx logging in terminal
logger = logging.getLogger("ScoreboardLogger")

# Remove all existing handlers
if logger.hasHandlers():
    logger.handlers.clear()

# Set up our custom stream handler
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)  # Show INFO and above in terminal
handler.setFormatter(ContextualFormatter("%(message)s"))
logger.addHandler(handler)

# Add a file handler for info logs (limited to last 500 lines)
log_dir = Path.cwd() / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

info_handler = InfoLogHandler(log_dir / "info.log")
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(ContextualFormatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(info_handler)


def _remove_empty_logs() -> None:
    """Delete any empty .log files to avoid clutter."""
    for log_file in log_dir.glob("*.log"):
        try:
            if log_file.name == "info.log":
                continue  # Keep info.log even if empty
            # Delete any empty log file including timestamped error logs
            if log_file.exists() and log_file.stat().st_size == 0:
                log_file.unlink()
                logger.debug("Deleted empty log file: %s", log_file.name)
        except Exception as e:
            # Log cleanup failures but don't break logging setup
            logger.debug("Failed to remove empty log file %s: %s", log_file, e)


def _build_error_handler() -> logging.Handler:
    """Build error handler with a fresh throttle filter per rotation."""
    handler = logging.FileHandler(log_dir / "error.log")
    handler.setLevel(logging.ERROR)
    handler.setFormatter(SpacedErrorFormatter("%(asctime)s - %(levelname)s - %(message)s"))
    handler.addFilter(ThrottleFilter(THROTTLE_SECONDS))  # Fresh filter per rotation
    return handler


_remove_empty_logs()

error_handler = _build_error_handler()
logger.addHandler(error_handler)

# Add email notification handler for errors (no filter; throttling handled by file handler)
email_handler = EmailNotificationHandler()
email_handler.setLevel(logging.ERROR)
logger.addHandler(email_handler)

logger.setLevel(logging.INFO)
logger.propagate = False

# Write a startup marker so info.log is always created
logger.info("Logger initialized")

def rotate_error_log() -> None:
    """Rotate error log file with timestamp to prevent it from getting too large."""
    log_dir.mkdir(parents=True, exist_ok=True)

    # First, clean up any empty timestamped error logs from previous runs
    _remove_empty_logs()

    error_log = log_dir / "error.log"
    if error_log.exists() and error_log.stat().st_size > 0:
        # Only rotate if error.log has content
        timestamp = datetime.now().strftime("%m-%d_%H-%M-%S")
        backup_log = log_dir / f"error_{timestamp}.log"
        error_log.rename(backup_log)
        logger.info("Rotated error log to %s", backup_log.name)
    elif error_log.exists():
        # Delete empty error.log instead of rotating it
        error_log.unlink()
        logger.debug("Deleted empty error.log")

    # Remove old error handler and create new one for fresh log file
    global error_handler
    if error_handler in logger.handlers:
        logger.removeHandler(error_handler)

    error_handler = _build_error_handler()
    logger.addHandler(error_handler)


# Context management and performance tracking helpers

def set_log_context(**kwargs: object) -> None:
    """Set contextual information for structured logging.

    Example: set_log_context(team='Lakers', league='NBA', endpoint='scoreboard')
    """
    context = (log_context.get({}) or {}).copy()
    context.update(kwargs)
    log_context.set(context)


def clear_log_context() -> None:
    """Clear all contextual logging information."""
    log_context.set({})


@contextmanager
def log_context_scope(**kwargs: object) -> Iterator[None]:
    """Context manager to set and restore logging context cleanly.

    Example:
        with log_context_scope(team='Lakers', league='NBA', endpoint='scoreboard'):
            ...

    """
    previous = (log_context.get({}) or {}).copy()
    set_log_context(**kwargs)
    try:
        yield
    finally:
        log_context.set(previous)


def track_api_call(endpoint: str, duration_ms: float, *, success: bool = True) -> None:
    """Track API call performance metrics.

    :param endpoint: API endpoint name (e.g., 'espn_scoreboard', 'nba_boxscore')
    :param duration_ms: Response time in milliseconds
    :param success: Whether the call succeeded
    """
    if endpoint not in performance_metrics["api_calls"]:
        performance_metrics["api_calls"][endpoint] = {
            "count": 0,
            "success": 0,
            "failed": 0,
            "total_time_ms": 0,
            "min_time_ms": float("inf"),
            "max_time_ms": 0,
        }

    stats = performance_metrics["api_calls"][endpoint]
    stats["count"] += 1
    if success:
        stats["success"] += 1
    else:
        stats["failed"] += 1
    stats["total_time_ms"] += duration_ms
    stats["min_time_ms"] = min(stats["min_time_ms"], duration_ms)
    stats["max_time_ms"] = max(stats["max_time_ms"], duration_ms)

    avg_time = stats["total_time_ms"] / stats["count"]
    logger.debug(
        "API call: %s - %.0fms (avg: %.0fms, success: %s/%s)",
        endpoint,
        duration_ms,
        avg_time,
        stats["success"],
        stats["count"],
    )


def track_cache_hit() -> None:
    """Track cache hit metric."""
    performance_metrics["cache_stats"]["hits"] += 1


def track_cache_miss() -> None:
    """Track cache miss metric."""
    performance_metrics["cache_stats"]["misses"] += 1


def track_retry(operation: str, attempt: int, max_attempts: int) -> None:
    """Track retry attempt metrics.

    :param operation: Name of the operation being retried
    :param attempt: Current attempt number
    :param max_attempts: Maximum number of attempts
    """
    if operation not in performance_metrics["retry_stats"]:
        performance_metrics["retry_stats"][operation] = {
            "total_retries": 0,
            "max_attempts_reached": 0,
        }

    stats = performance_metrics["retry_stats"][operation]
    stats["total_retries"] += 1
    if attempt >= max_attempts:
        stats["max_attempts_reached"] += 1


def track_validation(*, passed: bool) -> None:
    """Track validation result metrics.

    :param passed: Whether validation passed
    """
    if passed:
        performance_metrics["validation_stats"]["passed"] += 1
    else:
        performance_metrics["validation_stats"]["failed"] += 1


def get_performance_stats() -> dict[str, Any]:
    """Get current performance statistics.

    :return: Dictionary containing all performance metrics
    """
    # Calculate cache hit rate
    cache_stats = performance_metrics["cache_stats"]
    total_cache_requests = cache_stats["hits"] + cache_stats["misses"]
    hit_rate = (cache_stats["hits"] / total_cache_requests * 100) if total_cache_requests > 0 else 0

    # Calculate average API response times
    api_summary = {}
    for endpoint, stats in performance_metrics["api_calls"].items():
        if stats["count"] > 0:
            api_summary[endpoint] = {
                "avg_time_ms": stats["total_time_ms"] / stats["count"],
                "min_time_ms": stats["min_time_ms"],
                "max_time_ms": stats["max_time_ms"],
                "success_rate": (stats["success"] / stats["count"] * 100),
                "total_calls": stats["count"],
            }

    return {
        "cache": {
            "hits": cache_stats["hits"],
            "misses": cache_stats["misses"],
            "hit_rate_pct": hit_rate,
        },
        "api_calls": api_summary,
        "retries": performance_metrics["retry_stats"],
        "validation": performance_metrics["validation_stats"],
    }


def log_performance_summary() -> None:
    """Log a summary of performance metrics."""
    stats = get_performance_stats()

    logger.info("=" * 60)
    logger.info("Performance Summary")
    logger.info("=" * 60)

    # Cache stats
    cache = stats["cache"]
    logger.info(
        "Cache: %s hits, %s misses (%.1f%% hit rate)",
        cache["hits"],
        cache["misses"],
        cache["hit_rate_pct"],
    )

    # API call stats
    if stats["api_calls"]:
        logger.info("\nAPI Performance:")
        for endpoint, api_stats in stats["api_calls"].items():
            logger.info(
                "  %s: %.0fms avg (min: %.0fms, max: %.0fms) - %.1f%% success (%s calls)",
                endpoint,
                api_stats["avg_time_ms"],
                api_stats["min_time_ms"],
                api_stats["max_time_ms"],
                api_stats["success_rate"],
                api_stats["total_calls"],
            )

    # Retry stats
    if stats["retries"]:
        logger.info("\nRetry Statistics:")
        for operation, retry_stats in stats["retries"].items():
            logger.info(
                "  %s: %s retries, %s exhausted",
                operation,
                retry_stats["total_retries"],
                retry_stats["max_attempts_reached"],
            )

    # Validation stats
    val = stats["validation"]
    total_validations = val["passed"] + val["failed"]
    if total_validations > 0:
        pass_rate = (val["passed"] / total_validations * 100)
        logger.info(
            "\nValidation: %s passed, %s failed (%.1f%% pass rate)",
            val["passed"],
            val["failed"],
            pass_rate,
        )

    logger.info("=" * 60)


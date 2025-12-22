"""Create Logging config."""

import contextlib
import logging
import time
from datetime import datetime
from pathlib import Path

from .email import notify_email

THROTTLE_SECONDS = 60  # debounce identical error messages


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


class EmailNotificationHandler(logging.Handler):
    """Custom handler that sends email notifications on exceptions."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record by sending an email."""
        if record.levelno >= logging.ERROR:
            try:
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

    MAX_LINES = 1000

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
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

# Add a file handler for info logs (limited to last 500 lines)
log_dir = Path.cwd() / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

info_handler = InfoLogHandler(log_dir / "info.log")
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
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


"""Email Notification Module.

Configuration is loaded from environment variables (optionally via a `.env`):

- EMAIL_ENABLED: 'true'/'false' to enable/disable sending (default: false)
- SMTP_SERVER: SMTP host (default: smtp.gmail.com)
- SMTP_PORT: SMTP port (default: 587)
- SMTP_USER: Sender email address (required when enabled)
- SMTP_PASSWORD: SMTP/app password (required when enabled)
- TO_EMAILS: Comma-separated recipient list (required when enabled)
"""
from __future__ import annotations

import os
import smtplib
import socket
import tempfile
import zipfile
from contextlib import suppress
from email.message import EmailMessage
from pathlib import Path

from constants.file_paths import LOGS_DIR
from helper_functions.logging.logger_config import logger

# ---------------- Load .env explicitly ----------------
with suppress(Exception):  # optional dependency
    from dotenv import load_dotenv

    load_dotenv(override=True)

# ---------------- Config helpers ----------------
def _get_env_bool(name: str, *, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


EMAIL_ENABLED = _get_env_bool("EMAIL_ENABLED", default=False)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

SMTP_USER = (os.getenv("SMTP_USER") or "").strip()
SMTP_PASSWORD = (os.getenv("SMTP_PASSWORD") or "").replace(" ", "").strip()

_to_emails_env = os.getenv("TO_EMAILS") or ""
TO_EMAILS = [e.strip() for e in _to_emails_env.split(",") if e.strip()]

# -----------------------------------------------------

_last_error_sent: str | None = None


def email_config_status() -> tuple[bool, bool, str | None]:
    """Check email configuration status.

    :return: Tuple of (enabled, ok, reason)
    """
    enabled = EMAIL_ENABLED
    missing: list[str] = []

    if enabled:
        if not SMTP_USER:
            missing.append("SMTP_USER")
        if not SMTP_PASSWORD:
            missing.append("SMTP_PASSWORD")
        if not TO_EMAILS:
            missing.append("TO_EMAILS")

    ok = not missing
    reason = f"missing {', '.join(missing)}; set via environment or .env" if missing else None
    return enabled, ok, reason


def notify_email(subject: str = "", body: str = "") -> None:
    """Send diagnostic email notification."""
    enabled, ok, reason = email_config_status()

    if not enabled:
        return

    if not ok:
        msg = f"Email misconfigured: {reason}"
        return

    # Default subject
    if not subject:
        subject = f"Major League Scoreboard Error - {socket.gethostname()}"

    # Determine error log content
    log_dir = LOGS_DIR
    error_logs = sorted(log_dir.glob("error_*.log"), reverse=True)
    error_log_path = error_logs[0] if error_logs else log_dir / "error.log"

    error_text = (
        error_log_path.read_text(errors="replace")
        if error_log_path.exists()
        else "Error log file not found"
    )

    global _last_error_sent
    if error_text == _last_error_sent:
        logger.info("Duplicate error email detected; skipping send")
        return  # Avoid duplicate emails

    zip_path = _zip_logs(log_dir)

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(TO_EMAILS)
    msg["Subject"] = subject
    msg.set_content(body or "See attached logs for details.")

    if zip_path:
        with zip_path.open("rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="zip",
                filename=zip_path.name,
            )

    # Send email with exception handling
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception:
        logger.exception("Failed to send error notification email")
    finally:
        # Cleanup AFTER send (whether successful or not)
        with suppress(Exception):
            if zip_path:
                zip_path.unlink()

    _last_error_sent = error_text


def _zip_logs(log_dir: Path) -> Path | None:
    """Create a temporary zip containing all .log files in log_dir."""
    if not log_dir.exists():
        return None

    log_files = list(log_dir.glob("*.log"))
    if not log_files:
        return None

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        tmp_path = Path(tmp.name)

    try:
        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for log_file in log_files:
                zf.write(log_file, arcname=log_file.name)
    except Exception:
        with suppress(Exception):
            tmp_path.unlink()
        return None

    return tmp_path

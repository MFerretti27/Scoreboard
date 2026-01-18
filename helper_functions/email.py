"""Email Notification Module.

Now supports configuration via environment variables (from a `.env` file if present):

- EMAIL_ENABLED: 'true'/'false' to enable/disable sending (default: true)
- SMTP_SERVER: SMTP host (default: smtp.gmail.com)
- SMTP_PORT: SMTP port (default: 587)
- SMTP_USER: Sender email address
- SMTP_PASSWORD: SMTP/app password
- TO_EMAILS: Comma-separated recipient list
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

# Attempt to load .env if available
with suppress(Exception):  # pragma: no cover - optional dependency
    from dotenv import load_dotenv

    load_dotenv()

# ---------------- Config ----------------
def _get_env_bool(name: str, *, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


EMAIL_ENABLED = _get_env_bool("EMAIL_ENABLED", default=True)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "mattferretti27@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "ewrkxsc hpgw quai zmoo")
_to_emails_env = os.getenv("TO_EMAILS")
TO_EMAILS = (
    [e.strip() for e in _to_emails_env.split(",") if e.strip()] if _to_emails_env else ["ferretti7@yahoo.com"]
)
# ---------------------------------------


_last_error_sent: str | None = None


def notify_email(subject: str = "", body: str = "") -> None:
    """Send diagnostic email notification.

    :param subject: Email subject (optional; if empty, uses default with hostname)
    :param body: Email body (optional; if empty, reads from latest timestamped log or error.log)
    """
    # Respect EMAIL_ENABLED flag (no-op when disabled)
    if not EMAIL_ENABLED:
        return

    # If no subject provided, use default
    if not subject:
        subject = f"Major League Scoreboard Error - {socket.gethostname()}"

    # Read from the latest timestamped error log, fall back to error.log
    log_dir = Path("logs")
    error_logs = sorted(log_dir.glob("error_*.log"), reverse=True)

    # Use most recent timestamped log or fall back to error.log
    error_log_path = error_logs[0] if error_logs else log_dir / "error.log"
    global _last_error_sent

    error = error_log_path.read_text() if error_log_path.exists() else "Error log file not found"

    if error == _last_error_sent:
        return  # Avoid sending duplicate emails

    # Zip all log files to attach
    zip_path = _zip_logs(log_dir)

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(TO_EMAILS)
    msg["Subject"] = subject
    msg.set_content(body)

    if zip_path:
        with zip_path.open("rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="zip",
                filename=zip_path.name,
            )

    # Clean up temp zip file
    with suppress(Exception):
        if zip_path:
            zip_path.unlink()

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

    _last_error_sent = error


def _zip_logs(log_dir: Path) -> Path | None:
    """Create a temporary zip of all log files in log_dir."""
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
                # Store with base filename to avoid leaking full paths
                zf.write(log_file, arcname=log_file.name)
    except Exception:
        with suppress(Exception):
            tmp_path.unlink()
        return None
    else:
        return tmp_path


def email_config_status() -> tuple[bool, bool, str | None]:
    """Return (enabled, ok, reason) for email configuration.

    ok is True only if required values come from environment or .env.
    This avoids leaking defaults into production unknowingly.
    """
    enabled = EMAIL_ENABLED
    # Consider config OK only if variables were explicitly provided via env/.env
    user_set = os.getenv("SMTP_USER") is not None
    pwd_set = os.getenv("SMTP_PASSWORD") is not None
    to_set = os.getenv("TO_EMAILS") is not None
    ok = user_set and pwd_set and to_set
    reason = None
    if enabled and not ok:
        missing = []
        if not user_set:
            missing.append("SMTP_USER")
        if not pwd_set:
            missing.append("SMTP_PASSWORD")
        if not to_set:
            missing.append("TO_EMAILS")
        reason = f"missing {', '.join(missing)}; set via environment or .env"
    return enabled, ok, reason


"""Email Notification Module."""

import smtplib
import socket
import tempfile
import zipfile
from contextlib import suppress
from email.message import EmailMessage
from pathlib import Path

# ---------------- Config ----------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = ""
SMTP_PASSWORD = ""
TO_EMAILS = [""]
# ---------------------------------------


_last_error_sent: str | None = None


def notify_email(subject: str = "", body: str = "") -> None:
    """Send diagnostic email notification.

    :param subject: Email subject (optional; if empty, uses default with hostname)
    :param body: Email body (optional; if empty, reads from latest timestamped log or error.log)
    """
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


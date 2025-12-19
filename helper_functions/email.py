"""Email Notification Module."""

import smtplib
import socket
from email.message import EmailMessage
from pathlib import Path

# ---------------- Config ----------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = ""
SMTP_PASSWORD = ""
TO_EMAILS = [""]
# ---------------------------------------


def notify_email(subject: str = "", body: str = "") -> None:
    """Send diagnostic email notification.

    :param subject: Email subject (optional; if empty, uses default with hostname)
    :param body: Email body (optional; if empty, reads from error.log)
    """
    # If no subject provided, use default
    if not subject:
        subject=f"Major League Scoreboard Error - {socket.gethostname()}"

    # If no body provided, read from error.log
    if not body:
        error_log_path = Path("logs/error.log")
        body = error_log_path.read_text() if error_log_path.exists() else "Error log file not found at logs/error.log"

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(TO_EMAILS)
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


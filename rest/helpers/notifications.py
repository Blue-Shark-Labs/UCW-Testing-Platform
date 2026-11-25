"""Email notification helpers for student account lifecycle events (FR-57)."""

import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def send_student_approval_email(recipient_email: str, first_name: str) -> bool:
    """Sends an account approval confirmation email to a student.

    Uses SMTP configuration from environment variables when available; logs and
    returns False gracefully if SMTP is not configured in local/test environments.
    """
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    if not smtp_host:
        logger.info(
            "SMTP_HOST not configured; skipping approval email dispatch to %s.",
            recipient_email,
        )
        return False

    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    sender_email = os.environ.get("SMTP_FROM", smtp_user or "noreply@bluesharklabs.app")

    msg = EmailMessage()
    msg["Subject"] = "Your Reinforcement Testing Platform Account is Approved"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.set_content(
        f"Hello {first_name},\n\n"
        "Your student registration on the Reinforcement Testing Platform has been approved by a lecturer.\n"
        "You can now log in to access your assigned tests and leaderboards.\n\n"
        "Best regards,\n"
        "Blue Shark Labs"
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            if os.environ.get("SMTP_USE_TLS", "true").strip().lower() != "false":
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send approval confirmation email to %s.", recipient_email)
        return False
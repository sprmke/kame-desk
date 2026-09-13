import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_invitation_email(to_email: str, accept_url: str, clinic_name: str) -> None:
    subject = f"Join {clinic_name} on DoctorDesk"
    body = f"You were invited to join {clinic_name}.\n\nAccept: {accept_url}\n"
    _send_email(to_email, subject, body)


def send_reminder_email(
    to_email: str,
    subject: str,
    body: str,
    sender_name: str | None,
) -> str:
    from_header = sender_name or settings.smtp_from
    _send_email(to_email, subject, body, from_addr=from_header)
    return "smtp-local"


def _send_email(
    to_email: str,
    subject: str,
    body: str,
    from_addr: str | None = None,
) -> None:
    if settings.environment == "local":
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = from_addr or settings.smtp_from
            msg["To"] = to_email
            msg.set_content(body)
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
                smtp.send_message(msg)
            return
        except OSError:
            logger.info("Email (dev fallback): reminder_id logged only")
            return
    logger.info("Email queued: to_domain=%s subject=%s", to_email.split("@")[-1], subject)


def send_account_email(to_email: str, subject: str, body: str) -> None:
    _send_email(to_email, subject, body)

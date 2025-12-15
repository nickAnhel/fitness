import ssl
from email.message import EmailMessage
from email.utils import formataddr
import smtplib

from src.config import settings


def _smtp_client() -> smtplib.SMTP:
    if settings.mail.use_ssl:
        client = smtplib.SMTP_SSL(settings.mail.host, settings.mail.port, context=ssl.create_default_context(), timeout=10)
    else:
        client = smtplib.SMTP(settings.mail.host, settings.mail.port, timeout=10)
        if settings.mail.use_tls:
            client.starttls()
    if settings.mail.username and settings.mail.password:
        client.login(settings.mail.username, settings.mail.password)
    return client


def send_email(recipient: str, *, subject: str, body: str) -> None:
    if not settings.mail.enabled:
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((settings.mail.from_name, settings.mail.from_email))
    message["To"] = recipient
    message.set_content(body)

    with _smtp_client() as client:
        client.send_message(message)

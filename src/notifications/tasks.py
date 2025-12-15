from src.celery_app import celery_app
from src.notifications.email import send_email


@celery_app.task(name="notifications.send_email")
def send_email_task(recipient: str, *, subject: str, body: str) -> None:
    send_email(recipient, subject=subject, body=body)


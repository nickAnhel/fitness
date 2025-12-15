from __future__ import annotations

from datetime import date

from src.notifications.tasks import send_email_task
from src.notifications.templates import (
    EmailContent,
    promotion_emails,
    subscription_created_email,
    subscription_status_email,
)


def _send_email(content: EmailContent) -> None:
    send_email_task.delay(content.recipient, subject=content.subject, body=content.body)


def notify_subscription_created(
    *,
    recipient: str,
    first_name: str | None,
    last_name: str | None,
    branch_name: str,
    tariff_name: str,
    start_date: date,
) -> None:
    content = subscription_created_email(
        recipient=recipient,
        first_name=first_name,
        last_name=last_name,
        branch_name=branch_name,
        tariff_name=tariff_name,
        start_date=start_date,
    )
    _send_email(content)


def notify_subscription_status_change(
    *,
    recipient: str,
    first_name: str | None,
    last_name: str | None,
    status_name: str | None,
) -> None:
    content = subscription_status_email(
        recipient=recipient,
        first_name=first_name,
        last_name=last_name,
        status_name=status_name,
    )
    _send_email(content)


def notify_new_promotion(
    recipients: list[tuple[str, str | None, str | None]],
    *,
    promotion_name: str,
    discount_label: str,
    starts_at: date,
    ends_at: date,
) -> None:
    for content in promotion_emails(
        recipients,
        promotion_name=promotion_name,
        discount_label=discount_label,
        starts_at=starts_at,
        ends_at=ends_at,
    ):
        _send_email(content)

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass
class EmailContent:
    recipient: str
    subject: str
    body: str


def _display_name(first_name: str | None, last_name: str | None) -> str:
    parts = [p for p in (first_name, last_name) if p]
    return " ".join(parts) if parts else "клиент"


def subscription_created_email(
    *,
    recipient: str,
    first_name: str | None,
    last_name: str | None,
    branch_name: str,
    tariff_name: str,
    start_date: date,
) -> EmailContent:
    name = _display_name(first_name, last_name)
    subject = "Абонемент успешно создан"
    body = (
        f"Здравствуйте, {name}!\n\n"
        "Мы оформили для вас новый абонемент.\n"
        f"Филиал: {branch_name}\n"
        f"Тариф: {tariff_name}\n"
        f"Дата начала действия: {start_date:%d.%m.%Y}\n\n"
        "Хороших тренировок!"
    )
    return EmailContent(recipient=recipient, subject=subject, body=body)


def subscription_status_email(
    *,
    recipient: str,
    first_name: str | None,
    last_name: str | None,
    status_name: str | None,
) -> EmailContent:
    name = _display_name(first_name, last_name)
    status_label = status_name or "обновлен"
    subject = "Статус абонемента обновлен"
    body = (
        f"Здравствуйте, {name}!\n\n"
        "Статус вашего абонемента изменился.\n"
        f"Новый статус: {status_label}\n\n"
        "Если вы не ожидали это изменение, пожалуйста, свяжитесь с поддержкой клуба."
    )
    return EmailContent(recipient=recipient, subject=subject, body=body)


def promotion_emails(
    recipients: Iterable[tuple[str, str | None, str | None]],
    *,
    promotion_name: str,
    discount_label: str,
    starts_at: date,
    ends_at: date,
) -> list[EmailContent]:
    subject = "Новая промо-акция"
    emails: list[EmailContent] = []
    for email, first_name, last_name in recipients:
        name = _display_name(first_name, last_name)
        body = (
            f"Здравствуйте, {name}!\n\n"
            f"Стартовала новая акция «{promotion_name}».\n"
            f"Условия: {discount_label}\n"
            f"Даты проведения: {starts_at:%d.%m.%Y} — {ends_at:%d.%m.%Y}\n\n"
            "Успейте воспользоваться предложением!"
        )
        emails.append(EmailContent(recipient=email, subject=subject, body=body))
    return emails

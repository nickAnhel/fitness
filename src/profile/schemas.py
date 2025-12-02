from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from src.common.schemas import BaseSchema


class User(BaseSchema):
    user_id: uuid.UUID
    first_name: str
    last_name: str
    middle_name: str | None = None
    email: str
    phone: str | None = None


class SubscriptionStatus(BaseSchema):
    subscription_status_id: uuid.UUID
    name: str


class Subscription(BaseSchema):
    subscription_id: uuid.UUID
    start_date: date
    status: SubscriptionStatus
    branch_name: str = ""
    tariff_name: str = ""
    price: Decimal | None = None


class Visit(BaseSchema):
    visit_id: uuid.UUID
    entered_at: datetime
    exited_at: datetime | None = None
    branch_name: str = ""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from src.common.schemas import BaseSchema


class DiscountType(BaseSchema):
    discount_type_id: uuid.UUID
    name: str


class Promotion(BaseSchema):
    promotion_id: uuid.UUID
    name: str
    description: str | None = None
    starts_at: date
    ends_at: date
    discount_value: Decimal
    usage_limit: int | None = None
    is_active: bool
    discount_type: DiscountType
    branch_names: list[str] = []
    tariff_names: list[str] = []
    branch_refs: list[dict] = []
    tariff_refs: list[dict] = []

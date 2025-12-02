from __future__ import annotations

import uuid
from decimal import Decimal

from src.common.schemas import BaseSchema


class TariffType(BaseSchema):
    tariff_type_id: uuid.UUID
    name: str


class TariffValidityPeriod(BaseSchema):
    tariff_validity_period_id: uuid.UUID
    duration_days: int


class Tariff(BaseSchema):
    tariff_id: uuid.UUID
    name: str
    description: str | None = None
    price: Decimal
    is_available: bool
    tariff_type: TariffType
    validity_period: TariffValidityPeriod

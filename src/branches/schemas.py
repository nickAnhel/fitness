from __future__ import annotations

import uuid

from src.common.schemas import BaseSchema


class District(BaseSchema):
    district_id: uuid.UUID
    name: str


class Branch(BaseSchema):
    branch_id: uuid.UUID
    name: str
    description: str | None = None
    address: str
    contacts: str | None = None
    operating_hours: str | None = None
    is_active: bool
    district: District

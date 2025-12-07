from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class StartVisitRequest(BaseModel):
    branch_id: uuid.UUID
    entered_at: datetime


class FinishVisitRequest(BaseModel):
    branch_id: uuid.UUID
    exited_at: datetime

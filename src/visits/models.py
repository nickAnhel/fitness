from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.models import Base


class VisitModel(Base):
    __tablename__ = "visits"

    visit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"))
    branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.branch_id"))

    entered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    exited_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="visits")
    branch: Mapped["BranchModel"] = relationship("BranchModel", back_populates="visits")

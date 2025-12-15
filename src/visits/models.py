from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, inspect as sa_inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.models import Base


class VisitModel(Base):
    __tablename__ = "visits"

    visit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.branch_id", ondelete="CASCADE"))

    entered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    exited_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="visits")
    branch: Mapped["BranchModel"] = relationship("BranchModel", back_populates="visits")

    def __str__(self) -> str:
        inspector = sa_inspect(self)

        def safe_rel_name(rel_name: str, attr: str = "name") -> str | None:
            if rel_name in inspector.unloaded:
                return None
            rel_obj = getattr(self, rel_name, None)
            return getattr(rel_obj, attr, None) if rel_obj else None

        branch_name = safe_rel_name("branch")
        entered = self.entered_at.strftime("%Y-%m-%d %H:%M") if self.entered_at else None

        parts = [p for p in (branch_name, entered) if p]
        return " · ".join(parts) if parts else "Посещение"

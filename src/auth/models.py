from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.models import Base
from src.users.models import UserModel  # noqa: F401


class SessionModel(Base):
    __tablename__ = "sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["UserModel"] = relationship("UserModel")

    def __str__(self) -> str:
        user_name = getattr(self.user, "login", None) or getattr(self.user, "email", None)
        return f"Сессия {user_name}" if user_name else "Сессия"

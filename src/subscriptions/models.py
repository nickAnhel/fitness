from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, inspect as sa_inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.models import Base
# Register related models in metadata before mapper configuration
from src.users.models import UserModel  # noqa: F401
from src.tariffs.models import TariffModel  # noqa: F401


class SubscriptionStatusModel(Base):
    __tablename__ = "subscription_statuses"

    subscription_status_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    subscriptions: Mapped[list["SubscriptionModel"]] = relationship("SubscriptionModel", back_populates="status")

    def __str__(self) -> str:
        return self.name


class SubscriptionModel(Base):
    __tablename__ = "subscriptions"

    subscription_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.branch_id", ondelete="CASCADE"))
    tariff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tariffs.tariff_id", ondelete="CASCADE"))
    subscription_status_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subscription_statuses.subscription_status_id", ondelete="CASCADE")
    )

    start_date: Mapped[date] = mapped_column(Date, nullable=False)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="subscriptions")
    branch: Mapped["BranchModel"] = relationship("BranchModel", back_populates="subscriptions")
    tariff: Mapped["TariffModel"] = relationship("TariffModel", back_populates="subscriptions")
    status: Mapped["SubscriptionStatusModel"] = relationship("SubscriptionStatusModel", back_populates="subscriptions")

    def __str__(self) -> str:
        inspector = sa_inspect(self)

        def safe_rel_name(rel_name: str, attr: str = "name") -> str | None:
            if rel_name in inspector.unloaded:
                return None
            rel_obj = getattr(self, rel_name, None)
            return getattr(rel_obj, attr, None) if rel_obj else None

        tariff_name = safe_rel_name("tariff")
        branch_name = safe_rel_name("branch")
        status_name = safe_rel_name("status")

        parts = [p for p in (tariff_name, branch_name) if p]
        if not parts and status_name:
            parts.append(status_name)

        return " · ".join(parts) if parts else "Абонемент"

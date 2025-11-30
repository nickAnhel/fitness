from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.models import Base


class SubscriptionStatusModel(Base):
    __tablename__ = "subscription_statuses"

    subscription_status_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    subscriptions: Mapped[list["SubscriptionModel"]] = relationship("SubscriptionModel", back_populates="status")


class SubscriptionModel(Base):
    __tablename__ = "subscriptions"

    subscription_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"))
    branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.branch_id"))
    tariff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tariffs.tariff_id"))
    subscription_status_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subscription_statuses.subscription_status_id")
    )

    start_date: Mapped[date] = mapped_column(Date, nullable=False)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="subscriptions")
    branch: Mapped["BranchModel"] = relationship("BranchModel", back_populates="subscriptions")
    tariff: Mapped["TariffModel"] = relationship("TariffModel", back_populates="subscriptions")
    status: Mapped["SubscriptionStatusModel"] = relationship("SubscriptionStatusModel", back_populates="subscriptions")

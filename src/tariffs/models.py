from __future__ import annotations

import uuid
from sqlalchemy import String, Boolean, Numeric, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.models import Base


class TariffTypeModel(Base):
    __tablename__ = "tariff_types"

    tariff_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    tariffs: Mapped[list["TariffModel"]] = relationship("TariffModel", back_populates="tariff_type")


class TariffValidityPeriodModel(Base):
    __tablename__ = "tariff_validity_periods"

    tariff_validity_period_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)

    tariffs: Mapped[list["TariffModel"]] = relationship("TariffModel", back_populates="validity_period")


class TariffModel(Base):
    __tablename__ = "tariffs"

    tariff_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String)
    price: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    tariff_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tariff_types.tariff_type_id"))
    tariff_validity_period_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tariff_validity_periods.tariff_validity_period_id"))

    tariff_type: Mapped["TariffTypeModel"] = relationship("TariffTypeModel", back_populates="tariffs")
    validity_period: Mapped["TariffValidityPeriodModel"] = relationship("TariffValidityPeriodModel", back_populates="tariffs")

    promotions: Mapped[list["PromotionModel"]] = relationship(
        "PromotionModel",
        secondary="promotion_tariffs",
        back_populates="tariffs"
    )

    subscriptions: Mapped[list["SubscriptionModel"]] = relationship("SubscriptionModel", back_populates="tariff")

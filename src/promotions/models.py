from __future__ import annotations

import uuid
from datetime import date
from sqlalchemy import String, Boolean, Date, Numeric, Integer, ForeignKey, inspect as sa_inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.models import Base


class PromotionModel(Base):
    __tablename__ = "promotions"

    promotion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(String)

    starts_at: Mapped[date] = mapped_column(Date, nullable=False)
    ends_at: Mapped[date] = mapped_column(Date, nullable=False)

    discount_value: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    usage_limit: Mapped[int | None] = mapped_column(Integer)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    discount_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("discount_types.discount_type_id", ondelete="CASCADE"))

    discount_type: Mapped["DiscountTypeModel"] = relationship("DiscountTypeModel", back_populates="promotions")

    branches: Mapped[list["BranchModel"]] = relationship(
        "BranchModel",
        secondary="promotion_branches",
        back_populates="promotions"
    )
    tariffs: Mapped[list["TariffModel"]] = relationship(
        "TariffModel",
        secondary="promotion_tariffs",
        back_populates="promotions"
    )

    promotion_branches: Mapped[list["PromotionBranchModel"]] = relationship(
        "PromotionBranchModel", back_populates="promotion"
    )
    promotion_tariffs: Mapped[list["PromotionTariffModel"]] = relationship(
        "PromotionTariffModel", back_populates="promotion"
    )

    def __str__(self) -> str:
        return self.name


class PromotionBranchModel(Base):
    __tablename__ = "promotion_branches"

    promotion_branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    promotion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("promotions.promotion_id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=False)

    promotion: Mapped["PromotionModel"] = relationship("PromotionModel", back_populates="promotion_branches")
    branch: Mapped["BranchModel"] = relationship("BranchModel")

    def __str__(self) -> str:
        inspector = sa_inspect(self)
        if "branch" in inspector.unloaded:
            return "Филиал акции"
        branch_name = getattr(self.branch, "name", None)
        return branch_name or "Филиал акции"


class PromotionTariffModel(Base):
    __tablename__ = "promotion_tariffs"

    promotion_tariff_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    promotion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("promotions.promotion_id", ondelete="CASCADE"), nullable=False)
    tariff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tariffs.tariff_id", ondelete="CASCADE"), nullable=False)

    promotion: Mapped["PromotionModel"] = relationship("PromotionModel", back_populates="promotion_tariffs")
    tariff: Mapped["TariffModel"] = relationship("TariffModel")

    def __str__(self) -> str:
        inspector = sa_inspect(self)
        if "tariff" in inspector.unloaded:
            return "Тариф акции"
        tariff_name = getattr(self.tariff, "name", None)
        return tariff_name or "Тариф акции"

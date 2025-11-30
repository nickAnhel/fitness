from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.models import Base


class DistrictModel(Base):
    __tablename__ = "districts"

    district_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    branches: Mapped[list["BranchModel"]] = relationship(
        "BranchModel", back_populates="district"
    )


class DiscountTypeModel(Base):
    __tablename__ = "discount_types"

    discount_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    promotions: Mapped[list["PromotionModel"]] = relationship(
        "PromotionModel", back_populates="discount_type"
    )


class BranchModel(Base):
    __tablename__ = "branches"

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    contacts: Mapped[str | None] = mapped_column(String)
    operating_hours: Mapped[str | None] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    district_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("districts.district_id"), nullable=False
    )

    district: Mapped["DistrictModel"] = relationship(
        "DistrictModel", back_populates="branches"
    )
    employees: Mapped[list["EmployeeModel"]] = relationship(
        "EmployeeModel",
        secondary="employee_branches",
        back_populates="branches",
    )
    subscriptions: Mapped[list["SubscriptionModel"]] = relationship(
        "SubscriptionModel", back_populates="branch"
    )
    visits: Mapped[list["VisitModel"]] = relationship(
        "VisitModel", back_populates="branch"
    )

    promotions: Mapped[list["PromotionModel"]] = relationship(
        "PromotionModel", secondary="promotion_branches", back_populates="branches"
    )

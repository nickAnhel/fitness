from __future__ import annotations

import uuid

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.models import Base


class RoleModel(Base):
    __tablename__ = "roles"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String, nullable=True)

    employee_roles: Mapped[list["EmployeeRoleModel"]] = relationship(
        "EmployeeRoleModel",
        back_populates="role",
        cascade="all, delete-orphan",
    )


class EmployeeRoleModel(Base):
    __tablename__ = "employee_roles"

    employee_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.role_id", ondelete="CASCADE"),
        nullable=False,
    )

    employee: Mapped["EmployeeModel"] = relationship(
        "EmployeeModel",
        back_populates="employee_roles",
    )
    role: Mapped["RoleModel"] = relationship(
        "RoleModel",
        back_populates="employee_roles",
    )


class EmployeeModel(Base):
    __tablename__ = "employees"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100))
    birth_date: Mapped[DateTime | None] = mapped_column(DateTime)
    employment_date: Mapped[DateTime | None] = mapped_column(DateTime)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(32))
    login: Mapped[str | None] = mapped_column(String(50))
    password_hash: Mapped[str | None] = mapped_column(String(255))

    employee_roles: Mapped[list["EmployeeRoleModel"]] = relationship(
        "EmployeeRoleModel",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    branches: Mapped[list["BranchModel"]] = relationship(
        "BranchModel",
        secondary="employee_branches",
        back_populates="employees",
    )


class EmployeeBranchModel(Base):
    __tablename__ = "employee_branches"

    employee_branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.employee_id"), nullable=False)
    branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.branch_id"), nullable=False)

    employee: Mapped["EmployeeModel"] = relationship("EmployeeModel")
    branch: Mapped["BranchModel"] = relationship("BranchModel")

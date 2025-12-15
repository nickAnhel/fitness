from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.branches.models import BranchModel
from src.subscriptions.models import SubscriptionModel, SubscriptionStatusModel
from src.tariffs.models import TariffModel
from src.users.models import UserModel
from src.visits.models import VisitModel
from src.auth.models import SessionModel


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user(self, user_id: uuid.UUID) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def is_email_taken(self, email: str, exclude_user_id: uuid.UUID | None = None) -> bool:
        stmt = select(UserModel).where(UserModel.email == email)
        if exclude_user_id:
            stmt = stmt.where(UserModel.user_id != exclude_user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    async def update_user_contacts(
        self,
        user_id: uuid.UUID,
        email: str,
        phone: str | None,
        first_name: str,
        last_name: str,
        middle_name: str | None,
    ) -> UserModel | None:
        user = await self.get_user(user_id)
        if not user:
            return None
        user.email = email
        user.phone = phone
        user.first_name = first_name
        user.last_name = last_name
        user.middle_name = middle_name
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def list_statuses(self) -> list[SubscriptionStatusModel]:
        stmt = select(SubscriptionStatusModel).order_by(SubscriptionStatusModel.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_subscriptions_paginated(
        self,
        user_id: uuid.UUID,
        status_id: uuid.UUID | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[SubscriptionModel]:
        stmt = (
            select(SubscriptionModel)
            .options(
                selectinload(SubscriptionModel.tariff),
                selectinload(SubscriptionModel.branch),
                selectinload(SubscriptionModel.status),
            )
            .where(SubscriptionModel.user_id == user_id)
            .order_by(SubscriptionModel.start_date.desc())
        )
        if status_id:
            stmt = stmt.where(SubscriptionModel.subscription_status_id == status_id)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_subscriptions(self, user_id: uuid.UUID, status_id: uuid.UUID | None = None) -> int:
        stmt = select(func.count()).select_from(SubscriptionModel).where(SubscriptionModel.user_id == user_id)
        if status_id:
            stmt = stmt.where(SubscriptionModel.subscription_status_id == status_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def list_branches(self) -> list[BranchModel]:
        stmt = select(BranchModel).options(selectinload(BranchModel.district)).order_by(BranchModel.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_branch(self, branch_id: uuid.UUID) -> BranchModel | None:
        stmt = select(BranchModel).where(BranchModel.branch_id == branch_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_tariffs(self) -> list[TariffModel]:
        stmt = (
            select(TariffModel)
            .options(
                selectinload(TariffModel.tariff_type),
                selectinload(TariffModel.validity_period),
            )
            .where(TariffModel.is_available.is_(True))
            .order_by(TariffModel.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_tariff(self, tariff_id: uuid.UUID) -> TariffModel | None:
        stmt = select(TariffModel).where(TariffModel.tariff_id == tariff_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_default_status(self) -> SubscriptionStatusModel | None:
        stmt = (
            select(SubscriptionStatusModel)
            .where(func.lower(SubscriptionStatusModel.name) == "создан")
            .limit(1)
        )
        result = await self.session.execute(stmt)
        status = result.scalars().first()
        if status:
            return status
        stmt = select(SubscriptionStatusModel).order_by(SubscriptionStatusModel.name)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_subscription(
        self,
        *,
        user_id: uuid.UUID,
        branch_id: uuid.UUID,
        tariff_id: uuid.UUID,
        status_id: uuid.UUID,
        start_date: date,
    ) -> SubscriptionModel:
        subscription = SubscriptionModel(
            user_id=user_id,
            branch_id=branch_id,
            tariff_id=tariff_id,
            subscription_status_id=status_id,
            start_date=start_date,
        )
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def delete_subscription(self, user_id: uuid.UUID, subscription_id: uuid.UUID) -> bool:
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.subscription_id == subscription_id,
            SubscriptionModel.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        subscription = result.scalars().first()
        if not subscription:
            return False
        await self.session.delete(subscription)
        await self.session.commit()
        return True

    async def get_status_by_name(self, name: str) -> SubscriptionStatusModel | None:
        stmt = select(SubscriptionStatusModel).where(func.lower(SubscriptionStatusModel.name) == name.lower())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def set_subscription_status(
        self, user_id: uuid.UUID, subscription_id: uuid.UUID, status_id: uuid.UUID
    ) -> SubscriptionModel | None:
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.subscription_id == subscription_id,
            SubscriptionModel.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        subscription = result.scalars().first()
        if not subscription:
            return None
        subscription.subscription_status_id = status_id
        await self.session.commit()
        return await self.get_subscription_with_relations(subscription.subscription_id)

    async def get_subscription_with_relations(self, subscription_id: uuid.UUID) -> SubscriptionModel | None:
        stmt = (
            select(SubscriptionModel)
            .options(
                selectinload(SubscriptionModel.user),
                selectinload(SubscriptionModel.branch),
                selectinload(SubscriptionModel.tariff),
                selectinload(SubscriptionModel.status),
            )
            .where(SubscriptionModel.subscription_id == subscription_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_visits(
        self, user_id: uuid.UUID, month: date | None = None, branch_id: uuid.UUID | None = None
    ) -> list[VisitModel]:
        stmt = select(VisitModel).options(selectinload(VisitModel.branch)).where(VisitModel.user_id == user_id)

        if month:
            start = month.replace(day=1)
            # get first day of next month
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1, day=1)
            else:
                end = start.replace(month=start.month + 1, day=1)
            stmt = stmt.where(VisitModel.entered_at >= start, VisitModel.entered_at < end)
        if branch_id:
            stmt = stmt.where(VisitModel.branch_id == branch_id)

        stmt = stmt.order_by(VisitModel.entered_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_visit(self, user_id: uuid.UUID, visit_id: uuid.UUID) -> bool:
        stmt = select(VisitModel).where(VisitModel.visit_id == visit_id, VisitModel.user_id == user_id)
        result = await self.session.execute(stmt)
        visit = result.scalars().first()
        if not visit:
            return False
        await self.session.delete(visit)
        await self.session.commit()
        return True

    async def delete_all_visits(self, user_id: uuid.UUID) -> None:
        await self.session.execute(VisitModel.__table__.delete().where(VisitModel.user_id == user_id))
        await self.session.commit()

    async def delete_user_account(self, user_id: uuid.UUID) -> None:
        # remove dependent rows manually
        await self.session.execute(
            SubscriptionModel.__table__.delete().where(SubscriptionModel.user_id == user_id)
        )
        await self.session.execute(VisitModel.__table__.delete().where(VisitModel.user_id == user_id))
        await self.session.execute(SessionModel.__table__.delete().where(SessionModel.user_id == user_id))
        await self.session.execute(UserModel.__table__.delete().where(UserModel.user_id == user_id))
        await self.session.commit()

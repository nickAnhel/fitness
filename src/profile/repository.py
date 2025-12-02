from __future__ import annotations

import uuid
from datetime import datetime, date, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.branches.models import BranchModel
from src.subscriptions.models import SubscriptionModel, SubscriptionStatusModel
from src.tariffs.models import TariffModel
from src.users.models import UserModel
from src.visits.models import VisitModel


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_first_user(self) -> UserModel | None:
        stmt = select(UserModel).order_by(UserModel.registered_at).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_user_contacts(
        self, user_id: uuid.UUID, email: str, phone: str | None, first_name: str, last_name: str
    ) -> None:
        # placeholder for future update logic; not used yet
        pass

    async def list_statuses(self) -> list[SubscriptionStatusModel]:
        stmt = select(SubscriptionStatusModel).order_by(SubscriptionStatusModel.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_subscriptions(
        self, user_id: uuid.UUID, status_id: uuid.UUID | None = None
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

    async def list_visits(self, user_id: uuid.UUID, month: date | None = None) -> list[VisitModel]:
        stmt = select(VisitModel).options(selectinload(VisitModel.branch)).where(VisitModel.user_id == user_id)

        if month:
            start = month.replace(day=1)
            # get first day of next month
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1, day=1)
            else:
                end = start.replace(month=start.month + 1, day=1)
            stmt = stmt.where(VisitModel.entered_at >= start, VisitModel.entered_at < end)

        stmt = stmt.order_by(VisitModel.entered_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

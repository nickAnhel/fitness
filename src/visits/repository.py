from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.branches.models import BranchModel
from src.visits.models import VisitModel


class VisitsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_branch(self, branch_id: uuid.UUID) -> BranchModel | None:
        stmt = select(BranchModel).where(BranchModel.branch_id == branch_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_open_visit(self, user_id: uuid.UUID) -> VisitModel | None:
        stmt = (
            select(VisitModel)
            .options(selectinload(VisitModel.branch))
            .where(VisitModel.user_id == user_id, VisitModel.exited_at.is_(None))
            .order_by(VisitModel.entered_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_visit(self, user_id: uuid.UUID, branch_id: uuid.UUID, entered_at: datetime) -> VisitModel:
        visit = VisitModel(user_id=user_id, branch_id=branch_id, entered_at=entered_at)
        self.session.add(visit)
        await self.session.commit()
        await self.session.refresh(visit)
        return visit

    async def close_visit(self, visit: VisitModel, exited_at: datetime) -> VisitModel:
        visit.exited_at = exited_at
        await self.session.commit()
        await self.session.refresh(visit)
        return visit

from __future__ import annotations

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.branches.models import BranchModel, DistrictModel


class BranchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_districts(self) -> list[DistrictModel]:
        stmt = select(DistrictModel).order_by(DistrictModel.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_branches(
        self,
        district_id: uuid.UUID | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[BranchModel]:
        stmt = (
            select(BranchModel)
            .options(selectinload(BranchModel.district))
            .order_by(BranchModel.name)
        )
        if district_id:
            stmt = stmt.where(BranchModel.district_id == district_id)

        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_branch(self, branch_id: uuid.UUID) -> BranchModel | None:
        stmt = (
            select(BranchModel)
            .options(selectinload(BranchModel.district))
            .where(BranchModel.branch_id == branch_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def count_branches(self, district_id: uuid.UUID | None = None) -> int:
        stmt = select(func.count()).select_from(BranchModel)
        if district_id:
            stmt = stmt.where(BranchModel.district_id == district_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()

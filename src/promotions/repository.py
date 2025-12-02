from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.promotions.models import PromotionModel
from src.branches.models import BranchModel
from src.tariffs.models import TariffModel
from src.branches.models import DiscountTypeModel


class PromotionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_discount_types(self):
        stmt = select(DiscountTypeModel).order_by(DiscountTypeModel.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_promotions(
        self,
        discount_type_id: uuid.UUID | None = None,
        active_only: bool = True,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[PromotionModel]:
        today = date.today()
        stmt = (
            select(PromotionModel)
            .options(
                selectinload(PromotionModel.discount_type),
                selectinload(PromotionModel.branches),
                selectinload(PromotionModel.tariffs),
            )
            .order_by(PromotionModel.starts_at.desc())
        )

        if discount_type_id:
            stmt = stmt.where(PromotionModel.discount_type_id == discount_type_id)
        if active_only:
            stmt = stmt.where(
                PromotionModel.is_active.is_(True),
                PromotionModel.starts_at <= today,
                PromotionModel.ends_at >= today,
            )

        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_promotion(self, promotion_id: uuid.UUID) -> PromotionModel | None:
        stmt = (
            select(PromotionModel)
            .options(
                selectinload(PromotionModel.discount_type),
                selectinload(PromotionModel.branches),
                selectinload(PromotionModel.tariffs),
            )
            .where(PromotionModel.promotion_id == promotion_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def count_promotions(
        self, discount_type_id: uuid.UUID | None = None, active_only: bool = True
    ) -> int:
        today = date.today()
        stmt = select(func.count()).select_from(PromotionModel)
        if discount_type_id:
            stmt = stmt.where(PromotionModel.discount_type_id == discount_type_id)
        if active_only:
            stmt = stmt.where(
                PromotionModel.is_active.is_(True),
                PromotionModel.starts_at <= today,
                PromotionModel.ends_at >= today,
            )
        result = await self.session.execute(stmt)
        return result.scalar_one()

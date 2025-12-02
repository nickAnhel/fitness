from __future__ import annotations

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.tariffs.models import TariffModel, TariffTypeModel, TariffValidityPeriodModel
from src.promotions.models import PromotionModel


class TariffRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_tariff_types(self) -> list[TariffTypeModel]:
        stmt = select(TariffTypeModel).order_by(TariffTypeModel.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_validity_periods(self) -> list[TariffValidityPeriodModel]:
        stmt = select(TariffValidityPeriodModel).order_by(TariffValidityPeriodModel.duration_days)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_tariffs(
        self,
        tariff_type_id: uuid.UUID | None = None,
        validity_period_id: uuid.UUID | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[TariffModel]:
        stmt = (
            select(TariffModel)
            .options(
                selectinload(TariffModel.tariff_type),
                selectinload(TariffModel.validity_period),
            )
            .order_by(TariffModel.name)
        )

        if tariff_type_id:
            stmt = stmt.where(TariffModel.tariff_type_id == tariff_type_id)
        if validity_period_id:
            stmt = stmt.where(TariffModel.tariff_validity_period_id == validity_period_id)

        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_tariff(self, tariff_id: uuid.UUID) -> TariffModel | None:
        stmt = (
            select(TariffModel)
            .options(
                selectinload(TariffModel.tariff_type),
                selectinload(TariffModel.validity_period),
                selectinload(TariffModel.promotions).selectinload(PromotionModel.discount_type),
            )
            .where(TariffModel.tariff_id == tariff_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def count_tariffs(
        self, tariff_type_id: uuid.UUID | None = None, validity_period_id: uuid.UUID | None = None
    ) -> int:
        stmt = select(func.count()).select_from(TariffModel)
        if tariff_type_id:
            stmt = stmt.where(TariffModel.tariff_type_id == tariff_type_id)
        if validity_period_id:
            stmt = stmt.where(TariffModel.tariff_validity_period_id == validity_period_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()

from __future__ import annotations

import uuid

from src.tariffs import schemas
from src.tariffs.models import TariffModel
from src.tariffs.repository import TariffRepository


class TariffService:
    def __init__(self, repository: TariffRepository) -> None:
        self.repository = repository

    async def get_tariffs(
        self,
        tariff_type_id: uuid.UUID | None = None,
        validity_period_id: uuid.UUID | None = None,
        page: int = 1,
        per_page: int = 5,
    ) -> dict[str, object]:
        tariff_types = await self.repository.list_tariff_types()
        validity_periods = await self.repository.list_validity_periods()
        total = await self.repository.count_tariffs(
            tariff_type_id=tariff_type_id, validity_period_id=validity_period_id
        )
        page, per_page, offset = self._normalize_pagination(page, per_page)
        tariffs = await self.repository.list_tariffs(
            tariff_type_id=tariff_type_id,
            validity_period_id=validity_period_id,
            limit=per_page,
            offset=offset,
        )

        return {
            "filters": {
                "tariff_types": [schemas.TariffType.model_validate(t) for t in tariff_types],
                "validity_periods": [
                    schemas.TariffValidityPeriod.model_validate(p) for p in validity_periods
                ],
                "selected_tariff_type_id": tariff_type_id,
                "selected_validity_period_id": validity_period_id,
            },
            "tariffs": [self._tariff_to_schema(tariff) for tariff in tariffs],
            "pagination": self._pagination_meta(total, page, per_page),
        }

    async def get_tariff(self, tariff_id: uuid.UUID) -> schemas.Tariff | None:
        tariff = await self.repository.get_tariff(tariff_id)
        if not tariff:
            return None
        return self._tariff_to_schema(tariff)

    def _tariff_to_schema(self, tariff: TariffModel) -> schemas.Tariff:
        return schemas.Tariff.model_validate(tariff)

    def _normalize_pagination(self, page: int, per_page: int) -> tuple[int, int, int]:
        safe_page = max(page, 1)
        safe_per_page = max(per_page, 1)
        offset = (safe_page - 1) * safe_per_page
        return safe_page, safe_per_page, offset

    def _pagination_meta(self, total: int, page: int, per_page: int) -> dict[str, int | bool]:
        pages = (total + per_page - 1) // per_page if per_page else 1
        current = min(page, pages) if pages else 1
        return {
            "total": total,
            "page": current,
            "per_page": per_page,
            "pages": max(pages, 1),
            "has_prev": current > 1,
            "has_next": current < max(pages, 1),
            "prev_page": current - 1,
            "next_page": current + 1,
        }

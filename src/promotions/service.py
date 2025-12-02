from __future__ import annotations

import uuid
from datetime import date

from src.promotions import schemas
from src.promotions.models import PromotionModel
from src.promotions.repository import PromotionRepository


class PromotionService:
    def __init__(self, repository: PromotionRepository) -> None:
        self.repository = repository

    async def get_promotions(
        self,
        discount_type_id: uuid.UUID | None = None,
        active_only: bool = True,
        page: int = 1,
        per_page: int = 6,
    ) -> dict[str, object]:
        discount_types = await self.repository.list_discount_types()
        total = await self.repository.count_promotions(
            discount_type_id=discount_type_id, active_only=active_only
        )
        page, per_page, offset = self._normalize_pagination(page, per_page)
        promotions = await self.repository.list_promotions(
            discount_type_id=discount_type_id,
            active_only=active_only,
            limit=per_page,
            offset=offset,
        )

        return {
            "filters": {
                "discount_types": [schemas.DiscountType.model_validate(d) for d in discount_types],
                "selected_discount_type_id": discount_type_id,
                "active_only": active_only,
            },
            "promotions": [self._promotion_to_schema(promo) for promo in promotions],
            "pagination": self._pagination_meta(total, page, per_page),
        }

    async def get_promotion(self, promotion_id: uuid.UUID) -> schemas.Promotion | None:
        promotion = await self.repository.get_promotion(promotion_id)
        if not promotion:
            return None
        return self._promotion_to_schema(promotion)

    def _promotion_to_schema(self, promotion: PromotionModel) -> schemas.Promotion:
        today = date.today()
        is_live = (
            promotion.is_active
            and promotion.starts_at <= today
            and promotion.ends_at >= today
        )

        base = schemas.Promotion.model_validate(promotion)
        return base.model_copy(
            update={
                "is_active": is_live,
                "branch_names": sorted(branch.name for branch in promotion.branches),
                "tariff_names": sorted(tariff.name for tariff in promotion.tariffs),
                "branch_refs": [
                    {"id": branch.branch_id, "name": branch.name}
                    for branch in sorted(promotion.branches, key=lambda b: b.name)
                ],
                "tariff_refs": [
                    {"id": tariff.tariff_id, "name": tariff.name}
                    for tariff in sorted(promotion.tariffs, key=lambda t: t.name)
                ],
            }
        )

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

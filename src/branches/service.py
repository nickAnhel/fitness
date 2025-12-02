from __future__ import annotations

import uuid

from src.branches import schemas
from src.branches.models import BranchModel
from src.branches.repository import BranchRepository


class BranchService:
    def __init__(self, repository: BranchRepository) -> None:
        self.repository = repository

    async def get_branches(
        self,
        district_id: uuid.UUID | None = None,
        page: int = 1,
        per_page: int = 6,
    ) -> dict[str, object]:
        districts = await self.repository.list_districts()
        total = await self.repository.count_branches(district_id=district_id)
        page, per_page, offset = self._normalize_pagination(page, per_page)
        branches = await self.repository.list_branches(
            district_id=district_id,
            limit=per_page,
            offset=offset,
        )

        return {
            "filters": {
                "districts": [schemas.District.model_validate(d) for d in districts],
                "selected_district_id": district_id,
            },
            "branches": [self._branch_to_schema(branch) for branch in branches],
            "pagination": self._pagination_meta(total, page, per_page),
        }

    async def get_branch(self, branch_id: uuid.UUID) -> schemas.Branch | None:
        branch = await self.repository.get_branch(branch_id)
        if not branch:
            return None
        return self._branch_to_schema(branch)

    def _branch_to_schema(self, branch: BranchModel) -> schemas.Branch:
        return schemas.Branch.model_validate(branch)

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

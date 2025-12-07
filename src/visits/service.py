from __future__ import annotations

import uuid
from datetime import datetime

from src.visits.repository import VisitsRepository


class VisitsService:
    def __init__(self, repository: VisitsRepository) -> None:
        self.repository = repository

    async def start_visit(
        self, user_id: uuid.UUID, branch_id: uuid.UUID, entered_at: datetime
    ) -> tuple[dict | None, str | None]:
        branch = await self.repository.get_branch(branch_id)
        if not branch:
            return None, "Филиал не найден"
        open_visit = await self.repository.get_open_visit(user_id)
        if open_visit:
            return None, "Есть незавершенное посещение"
        visit = await self.repository.create_visit(user_id, branch_id, entered_at)
        return self._map_visit(visit), None

    async def finish_visit(
        self, user_id: uuid.UUID, branch_id: uuid.UUID, exited_at: datetime
    ) -> tuple[dict | None, str | None]:
        open_visit = await self.repository.get_open_visit(user_id)
        if not open_visit:
            return None, "Нет активного посещения"
        if open_visit.branch_id != branch_id:
            return None, "Неверный филиал для выхода"
        if exited_at < open_visit.entered_at:
            return None, "Время выхода не может быть раньше входа"
        visit = await self.repository.close_visit(open_visit, exited_at)
        return self._map_visit(visit), None

    def _map_visit(self, visit) -> dict:
        return {
            "visit_id": str(visit.visit_id),
            "branch_id": str(visit.branch_id),
            "entered_at": visit.entered_at.isoformat(),
            "exited_at": visit.exited_at.isoformat() if visit.exited_at else None,
        }

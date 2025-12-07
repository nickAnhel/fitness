from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.common.database import get_async_session
from src.visits.repository import VisitsRepository
from src.visits.service import VisitsService
from src.visits.schemas import StartVisitRequest, FinishVisitRequest

router = APIRouter(tags=["visits"])


async def get_visits_service(session: AsyncSession = Depends(get_async_session)) -> VisitsService:
    return VisitsService(VisitsRepository(session))


def _parse_dt(value: str, name: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Некорректное значение {name}") from exc


@router.post("/visits/start")
async def start_visit(
    request: Request,
    payload: StartVisitRequest,
    service: VisitsService = Depends(get_visits_service),
):
    user = getattr(request.state, "user", None)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    _, error = await service.start_visit(user.user_id, payload.branch_id, payload.entered_at)
    if error:
        return RedirectResponse(url=f"/profile?error={error.replace(' ', '+')}", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)


@router.put("/visits/finish")
async def finish_visit(
    request: Request,
    payload: FinishVisitRequest,
    service: VisitsService = Depends(get_visits_service),
):
    user = getattr(request.state, "user", None)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    _, error = await service.finish_visit(user.user_id, payload.branch_id, payload.exited_at)
    if error:
        return RedirectResponse(url=f"/profile?error={error.replace(' ', '+')}", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)

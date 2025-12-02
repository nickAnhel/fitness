from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database import get_async_session
from src.profile.repository import ProfileRepository
from src.profile.service import ProfileService

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

router = APIRouter(tags=["profile"])


async def get_profile_service(session: AsyncSession = Depends(get_async_session)) -> ProfileService:
    repository = ProfileRepository(session=session)
    return ProfileService(repository=repository)


def _parse_uuid(value: str | None) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректный идентификатор") from exc


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    status_id: str | None = Query(default=None),
    month: str | None = Query(default=None, description="Месяц в формате YYYY-MM"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=5, ge=1, le=50),
    service: ProfileService = Depends(get_profile_service),
) -> HTMLResponse:
    month_date = None
    if month:
        try:
            month_date = datetime.strptime(month, "%Y-%m").date().replace(day=1)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Некорректный месяц (ожидается YYYY-MM)") from exc

    data = await service.get_profile(
        status_id=_parse_uuid(status_id),
        month=month_date,
        page=page,
        per_page=per_page,
    )
    if not data:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return templates.TemplateResponse(
        "profile/index.html",
        {
            "request": request,
            "page_title": "Профиль",
            **data,
        },
    )

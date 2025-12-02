from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database import get_async_session
from src.tariffs.repository import TariffRepository
from src.tariffs.service import TariffService

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

router = APIRouter(tags=["tariffs"])


async def get_tariff_service(session: AsyncSession = Depends(get_async_session)) -> TariffService:
    repository = TariffRepository(session=session)
    return TariffService(repository=repository)


def _parse_uuid(value: str | None) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректный идентификатор") from exc


@router.get("/tariffs", response_class=HTMLResponse, name="list_tariffs")
async def list_tariffs(
    request: Request,
    tariff_type_id: str | None = Query(default=None),
    validity_period_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=6, ge=1, le=50),
    service: TariffService = Depends(get_tariff_service),
) -> HTMLResponse:
    data = await service.get_tariffs(
        tariff_type_id=_parse_uuid(tariff_type_id),
        validity_period_id=_parse_uuid(validity_period_id),
        page=page,
        per_page=per_page,
    )
    return templates.TemplateResponse(
        "tariffs/list.html",
        {
            "request": request,
            "page_title": "Тарифные планы",
            **data,
        },
    )


@router.get("/tariffs/{tariff_id}", response_class=HTMLResponse, name="tariff_details")
async def tariff_details(
    request: Request,
    tariff_id: uuid.UUID,
    service: TariffService = Depends(get_tariff_service),
) -> HTMLResponse:
    tariff = await service.get_tariff(tariff_id)
    if not tariff:
        raise HTTPException(status_code=404, detail="Тариф не найден")

    return templates.TemplateResponse(
        "tariffs/detail.html",
        {
            "request": request,
            "page_title": tariff.name,
            "tariff": tariff,
        },
    )

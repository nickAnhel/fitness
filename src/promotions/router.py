from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database import get_async_session
from src.promotions.repository import PromotionRepository
from src.promotions.service import PromotionService

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

router = APIRouter(tags=["promotions"])


async def get_promotion_service(session: AsyncSession = Depends(get_async_session)) -> PromotionService:
    repository = PromotionRepository(session=session)
    return PromotionService(repository=repository)


def _parse_uuid(value: str | None) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректный идентификатор") from exc


@router.get("/promotions", response_class=HTMLResponse, name="list_promotions")
async def list_promotions(
    request: Request,
    discount_type_id: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=6, ge=1, le=50),
    service: PromotionService = Depends(get_promotion_service),
) -> HTMLResponse:
    data = await service.get_promotions(
        discount_type_id=_parse_uuid(discount_type_id),
        active_only=active_only,
        page=page,
        per_page=per_page,
    )
    return templates.TemplateResponse(
        "promotions/list.html",
        {
            "request": request,
            "page_title": "Промо-акции",
            **data,
        },
    )


@router.get("/promotions/{promotion_id}", response_class=HTMLResponse, name="promotion_details")
async def promotion_details(
    request: Request,
    promotion_id: uuid.UUID,
    service: PromotionService = Depends(get_promotion_service),
) -> HTMLResponse:
    promotion = await service.get_promotion(promotion_id)
    if not promotion:
        raise HTTPException(status_code=404, detail="Акция не найдена")

    return templates.TemplateResponse(
        "promotions/detail.html",
        {
            "request": request,
            "page_title": promotion.name,
            "promotion": promotion,
        },
    )

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.branches.repository import BranchRepository
from src.branches.service import BranchService
from src.common.database import get_async_session

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

router = APIRouter(tags=["branches"])


async def get_branch_service(session: AsyncSession = Depends(get_async_session)) -> BranchService:
    repository = BranchRepository(session=session)
    return BranchService(repository=repository)


def _parse_uuid(value: str | None) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректный идентификатор") from exc


@router.get("/branches", response_class=HTMLResponse, name="list_branches")
async def list_branches(
    request: Request,
    district_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=50),
    service: BranchService = Depends(get_branch_service),
) -> HTMLResponse:
    data = await service.get_branches(
        district_id=_parse_uuid(district_id),
        page=page,
        per_page=per_page,
    )
    return templates.TemplateResponse(
        "branches/list.html",
        {
            "request": request,
            "page_title": "Филиалы",
            **data,
        },
    )


@router.get("/branches/{branch_id}", response_class=HTMLResponse, name="branch_details")
async def branch_details(
    request: Request,
    branch_id: uuid.UUID,
    service: BranchService = Depends(get_branch_service),
) -> HTMLResponse:
    branch = await service.get_branch(branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Филиал не найден")

    return templates.TemplateResponse(
        "branches/detail.html",
        {
            "request": request,
            "page_title": branch.name,
            "branch": branch,
        },
    )

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database import get_async_session
from src.branches.repository import BranchRepository
from src.tariffs.repository import TariffRepository

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

router = APIRouter(tags=["public"])


@router.get("/", response_class=HTMLResponse)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/about", status_code=status.HTTP_302_FOUND)


@router.get("/about", response_class=HTMLResponse, name="about")
async def about(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    branch_repo = BranchRepository(session=session)
    tariff_repo = TariffRepository(session=session)
    counts = {
        "branches_total": await branch_repo.count_branches(),
        "tariffs_total": await tariff_repo.count_tariffs(),
    }
    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            "page_title": "О сети фитнес-клубов",
            "counts": counts,
        },
    )

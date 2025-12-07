from __future__ import annotations

import uuid
from urllib.parse import quote_plus
from datetime import datetime, date
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.auth.service import SESSION_COOKIE_NAME
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
    branch_id: str | None = Query(default=None, description="Фильтр по филиалу"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=5, ge=1, le=50),
    service: ProfileService = Depends(get_profile_service),
) -> HTMLResponse:
    if not getattr(request.state, "user", None):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    current_user = request.state.user
    month_date = None
    if month:
        try:
            month_date = datetime.strptime(month, "%Y-%m").date().replace(day=1)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Некорректный месяц (ожидается YYYY-MM)") from exc

    data = await service.get_profile(
        user_id=current_user.user_id,
        status_id=_parse_uuid(status_id),
        month=month_date,
        branch_id=_parse_uuid(branch_id),
        page=page,
        per_page=per_page,
    )
    if not data:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        "profile/index.html",
        {
            "request": request,
            "page_title": "Профиль",
            **data,
            "form_error": request.query_params.get("error"),
        },
    )


@router.post("/profile/update")
async def update_profile(
    request: Request,
    service: ProfileService = Depends(get_profile_service),
    first_name: str = Form(...),
    last_name: str = Form(...),
    middle_name: str | None = Form(default=None),
    email: str = Form(...),
    phone: str | None = Form(default=None),
) -> Response:
    if not getattr(request.state, "user", None):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    current_user = request.state.user
    updated, error = await service.update_profile(
        current_user.user_id,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        middle_name=middle_name.strip() if middle_name else None,
        email=email.strip().lower(),
        phone=phone.strip() if phone else None,
    )
    if error:
        data = await service.get_profile(
            user_id=current_user.user_id,
            status_id=None,
            month=None,
            branch_id=None,
        )
        return templates.TemplateResponse(
            "profile/index.html",
            {
                "request": request,
                "page_title": "Профиль",
                **(data or {}),
                "form_error": error,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)


@router.post("/profile/subscriptions")
async def create_subscription(
    request: Request,
    service: ProfileService = Depends(get_profile_service),
    branch_id: str = Form(...),
    tariff_id: str = Form(...),
    start_date: str = Form(...),
) -> Response:
    if not getattr(request.state, "user", None):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    current_user = request.state.user
    try:
        branch_uuid = uuid.UUID(branch_id)
        tariff_uuid = uuid.UUID(tariff_id)
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        return RedirectResponse(
            url="/profile?error=Некорректные+данные+формы",
            status_code=status.HTTP_302_FOUND,
        )

    if start < date.today():
        return RedirectResponse(
            url="/profile?error=Дата+начала+не+может+быть+в+прошлом",
            status_code=status.HTTP_302_FOUND,
        )

    _, error = await service.create_subscription(
        current_user.user_id,
        branch_id=branch_uuid,
        tariff_id=tariff_uuid,
        start_date=start,
    )
    if error:
        return RedirectResponse(
            url=f"/profile?error={quote_plus(error)}",
            status_code=status.HTTP_302_FOUND,
        )
    return RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)


@router.post("/profile/subscriptions/cancel")
async def cancel_subscription(
    request: Request,
    service: ProfileService = Depends(get_profile_service),
    subscription_id: str = Form(...),
) -> Response:
    if not getattr(request.state, "user", None):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    try:
        sub_uuid = uuid.UUID(subscription_id)
    except ValueError:
        return RedirectResponse(url="/profile?error=Некорректный+идентификатор+абонемента", status_code=status.HTTP_302_FOUND)
    await service.cancel_subscription(request.state.user.user_id, sub_uuid)
    return RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)


@router.post("/profile/visits/delete")
async def delete_visit(
    request: Request,
    service: ProfileService = Depends(get_profile_service),
    visit_id: str = Form(...),
) -> Response:
    if not getattr(request.state, "user", None):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    try:
        visit_uuid = uuid.UUID(visit_id)
    except ValueError:
        return RedirectResponse(url="/profile?error=Некорректный+идентификатор+посещения", status_code=status.HTTP_302_FOUND)
    await service.delete_visit(request.state.user.user_id, visit_uuid)
    return RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)


@router.post("/profile/visits/clear")
async def clear_visits(
    request: Request,
    service: ProfileService = Depends(get_profile_service),
) -> Response:
    if not getattr(request.state, "user", None):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    await service.clear_visits(request.state.user.user_id)
    return RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)



@router.post("/profile/delete-account")
async def delete_account(
    request: Request,
    service: ProfileService = Depends(get_profile_service),
) -> Response:
    if not getattr(request.state, "user", None):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    await service.delete_account(request.state.user.user_id)
    response = RedirectResponse(url="/register", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response

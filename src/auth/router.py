from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Cookie, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.auth.repository import AuthRepository
from src.auth.service import AuthService, SESSION_COOKIE_NAME
from src.common.database import get_async_session

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

router = APIRouter(tags=["auth"])


async def get_auth_service(session: AsyncSession = Depends(get_async_session)) -> AuthService:
    repository = AuthRepository(session=session)
    return AuthService(repository=repository)


@router.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request) -> HTMLResponse:
    if getattr(request.state, "user", None):
        return RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "page_title": "Вход в аккаунт"},
    )


@router.post("/login")
async def login(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
    service: AuthService = Depends(get_auth_service),
) -> Response:
    user = await service.authenticate(login.strip(), password)
    if not user:
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "page_title": "Вход в аккаунт",
                "error": "Неверный логин или пароль",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    session_id = await service.create_session(user.user_id)
    response = RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=str(session_id),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 14,
    )
    return response


@router.get("/register", response_class=HTMLResponse, name="register_page")
async def register_page(request: Request) -> HTMLResponse:
    if getattr(request.state, "user", None):
        return RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request, "page_title": "Регистрация"},
    )


@router.post("/register")
async def register(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    login: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str | None = Form(default=None),
    service: AuthService = Depends(get_auth_service),
) -> Response:
    normalized_email = email.strip().lower()
    normalized_login = login.strip()
    if await service.repository.is_email_taken(normalized_email):
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "page_title": "Регистрация",
                "error": "Пользователь с таким email уже зарегистрирован",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if await service.repository.is_login_taken(normalized_login):
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "page_title": "Регистрация",
                "error": "Пользователь с таким логином уже существует",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = await service.register_user(
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        email=normalized_email,
        login=normalized_login,
        password=password,
        phone=phone.strip() if phone else None,
    )
    session_id = await service.create_session(user.user_id)
    response = RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=str(session_id),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 14,
    )
    return response


@router.post("/logout", name="logout")
async def logout(
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    service: AuthService = Depends(get_auth_service),
) -> Response:
    if session_cookie:
        try:
            session_id = uuid.UUID(session_cookie)
            await service.logout(session_id)
        except ValueError:
            pass
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response

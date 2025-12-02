from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

router = APIRouter(tags=["auth"])


@router.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "page_title": "Вход в аккаунт"},
    )


@router.get("/register", response_class=HTMLResponse, name="register_page")
async def register_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request, "page_title": "Регистрация"},
    )

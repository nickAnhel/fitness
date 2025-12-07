from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.auth import auth_router
from src.auth.middleware import SessionMiddleware
from src.branches.router import router as branches_router
from src.promotions.router import router as promotions_router
from src.profile import profile_router
from src.public.router import router as public_router
from src.tariffs.router import router as tariffs_router
from src.visits.router import router as visits_router


def register_routes(app: FastAPI) -> None:
    app.include_router(public_router)
    app.include_router(auth_router)
    app.include_router(branches_router)
    app.include_router(tariffs_router)
    app.include_router(promotions_router)
    app.include_router(profile_router)
    app.include_router(visits_router)


def setup_app(app: FastAPI) -> None:
    static_path = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    app.add_middleware(SessionMiddleware)
    register_routes(app)

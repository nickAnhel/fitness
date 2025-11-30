from fastapi import FastAPI


def register_routes(app: FastAPI) -> None:
    pass


def setup_app(app: FastAPI) -> None:
    register_routes(app)

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware

from src.auth.repository import AuthRepository
from src.auth.service import AuthService, SESSION_COOKIE_NAME
from src.common.database import async_session_maker


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.user = None
        session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
        if session_cookie:
            try:
                session_id = uuid.UUID(session_cookie)
            except ValueError:
                response = await call_next(request)
                response.delete_cookie(SESSION_COOKIE_NAME)
                return response

            async with async_session_maker() as session:
                service = AuthService(AuthRepository(session))
                user = await service.get_session_user(session_id)
                if user:
                    request.state.user = user

        response = await call_next(request)
        return response

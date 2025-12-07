from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta

from src.auth.repository import AuthRepository
from src.users.models import UserModel

SESSION_COOKIE_NAME = "session_id"
SESSION_TTL_DAYS = 14


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    async def register_user(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        login: str,
        password: str,
        phone: str | None = None,
    ) -> UserModel:
        password_hash = self._hash_password(password)
        return await self.repository.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            login=login,
            password_hash=password_hash,
            phone=phone,
        )

    async def authenticate(self, identifier: str, password: str) -> UserModel | None:
        user = await self.repository.get_user_by_login_or_email(identifier)
        if not user:
            return None
        if user.password_hash != self._hash_password(password):
            return None
        if user.is_blocked:
            return None
        return user

    async def create_session(self, user_id: uuid.UUID) -> uuid.UUID:
        expires_at = datetime.utcnow() + timedelta(days=SESSION_TTL_DAYS)
        session = await self.repository.create_session(user_id=user_id, expires_at=expires_at)
        return session.session_id

    async def get_session_user(self, session_id: uuid.UUID) -> UserModel | None:
        session = await self.repository.get_session(session_id)
        if not session:
            return None
        if session.expires_at <= datetime.utcnow():
            await self.repository.delete_session(session_id)
            return None
        return session.user

    async def logout(self, session_id: uuid.UUID) -> None:
        await self.repository.delete_session(session_id)

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

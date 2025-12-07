from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.models import SessionModel
from src.users.models import UserModel


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_login_or_email(self, identifier: str) -> UserModel | None:
        stmt = select(UserModel).where(
            (UserModel.email == identifier) | (UserModel.login == identifier)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def is_email_taken(self, email: str, exclude_user_id: uuid.UUID | None = None) -> bool:
        stmt = select(UserModel).where(UserModel.email == email)
        if exclude_user_id:
            stmt = stmt.where(UserModel.user_id != exclude_user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    async def create_user(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        login: str,
        password_hash: str,
        phone: str | None = None,
    ) -> UserModel:
        user = UserModel(
            first_name=first_name,
            last_name=last_name,
            email=email,
            login=login,
            password_hash=password_hash,
            phone=phone,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def is_login_taken(self, login: str, exclude_user_id: uuid.UUID | None = None) -> bool:
        stmt = select(UserModel).where(UserModel.login == login)
        if exclude_user_id:
            stmt = stmt.where(UserModel.user_id != exclude_user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    async def create_session(self, *, user_id: uuid.UUID, expires_at: datetime) -> SessionModel:
        session = SessionModel(user_id=user_id, expires_at=expires_at)
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def get_session(self, session_id: uuid.UUID) -> SessionModel | None:
        stmt = (
            select(SessionModel)
            .options(selectinload(SessionModel.user))
            .where(SessionModel.session_id == session_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def delete_session(self, session_id: uuid.UUID) -> None:
        session = await self.get_session(session_id)
        if not session:
            return
        await self.session.delete(session)
        await self.session.commit()

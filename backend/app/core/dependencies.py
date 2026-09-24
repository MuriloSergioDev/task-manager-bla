from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.domain.repositories.task_repository import TaskRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_hasher import PasswordHasher
from app.domain.services.token_service import TokenService
from app.infrastructure.repositories.sqlalchemy_task_repository import SqlAlchemyTaskRepository
from app.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.infrastructure.services.argon2_password_hasher import Argon2PasswordHasher
from app.infrastructure.services.jwt_token_service import JwtTokenService


def get_user_repository(session: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_task_repository(session: Annotated[AsyncSession, Depends(get_db)]) -> TaskRepository:
    return SqlAlchemyTaskRepository(session)


def get_password_hasher() -> PasswordHasher:
    return Argon2PasswordHasher()


def get_token_service(settings: Annotated[Settings, Depends(get_settings)]) -> TokenService:
    return JwtTokenService(settings)

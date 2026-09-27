from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.domain.entities.user import User
from app.domain.services.token_service import InvalidTokenError
from app.presentation.api.dependencies.auth import get_current_user
from tests.fixtures.factories import build_user


class FakeTokenService:
    def __init__(self, *, user_id: UUID | None = None, error: Exception | None = None) -> None:
        self._user_id = user_id
        self._error = error

    def create_access_token(self, *, user_id: UUID, email: str) -> tuple[str, int]:
        raise NotImplementedError

    def decode_access_token(self, token: str) -> UUID:
        if self._error is not None:
            raise self._error
        assert self._user_id is not None
        return self._user_id


class FakeUserRepository:
    def __init__(self, *, user: User | None = None) -> None:
        self.user = user

    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    async def get_by_id(self, user_id: UUID) -> User | None:
        if self.user is not None and self.user.id == user_id:
            return self.user
        return None

    async def create(self, *, email: str, password_hash: str) -> User:
        raise NotImplementedError

    async def list_all(self) -> list[User]:
        raise NotImplementedError


async def test_get_current_user_rejects_missing_cookie() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            token_service=FakeTokenService(),
            user_repository=FakeUserRepository(),
            access_token=None,
        )

    assert exc_info.value.status_code == 401


async def test_get_current_user_rejects_invalid_token() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            token_service=FakeTokenService(error=InvalidTokenError("bad token")),
            user_repository=FakeUserRepository(),
            access_token="token",
        )

    assert exc_info.value.status_code == 401


async def test_get_current_user_rejects_inactive_user() -> None:
    user = build_user(is_active=False)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            token_service=FakeTokenService(user_id=user.id),
            user_repository=FakeUserRepository(user=user),
            access_token="token",
        )

    assert exc_info.value.status_code == 401


async def test_get_current_user_rejects_unknown_user() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            token_service=FakeTokenService(user_id=uuid4()),
            user_repository=FakeUserRepository(user=None),
            access_token="token",
        )

    assert exc_info.value.status_code == 401


async def test_get_current_user_returns_active_user() -> None:
    user = build_user(is_active=True)

    result = await get_current_user(
        token_service=FakeTokenService(user_id=user.id),
        user_repository=FakeUserRepository(user=user),
        access_token="token",
    )

    assert result == user

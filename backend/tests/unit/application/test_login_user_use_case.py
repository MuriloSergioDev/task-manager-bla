from uuid import UUID

import pytest

from app.application.use_cases.auth.login_user import InvalidCredentialsError, LoginUserUseCase
from app.domain.entities.user import User
from tests.fixtures.factories import build_user


class FakeUserRepository:
    def __init__(self, *, user: User | None = None) -> None:
        self.user = user

    async def get_by_email(self, email: str) -> User | None:
        if self.user is not None and self.user.email == email:
            return self.user
        return None

    async def get_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    async def create(self, *, email: str, password_hash: str) -> User:
        raise NotImplementedError

    async def list_all(self) -> list[User]:
        raise NotImplementedError


class FakePasswordHasher:
    def hash(self, plain_password: str) -> str:
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{plain_password}"


class FakeTokenService:
    def __init__(self) -> None:
        self.issued_for: tuple[UUID, str] | None = None

    def create_access_token(self, *, user_id: UUID, email: str) -> tuple[str, int]:
        self.issued_for = (user_id, email)
        return "fake-token", 1800

    def decode_access_token(self, token: str) -> UUID:
        raise NotImplementedError


async def test_login_succeeds_with_correct_credentials() -> None:
    user = build_user(email="user@example.com", password_hash="hashed:correct-password")
    repository = FakeUserRepository(user=user)
    token_service = FakeTokenService()
    use_case = LoginUserUseCase(
        user_repository=repository,
        password_hasher=FakePasswordHasher(),
        token_service=token_service,
    )

    authenticated_user, token, expires_in = await use_case.execute(
        email="user@example.com", password="correct-password"
    )

    assert authenticated_user == user
    assert token == "fake-token"
    assert expires_in == 1800
    assert token_service.issued_for == (user.id, user.email)


async def test_login_rejects_unknown_email() -> None:
    repository = FakeUserRepository(user=None)
    use_case = LoginUserUseCase(
        user_repository=repository,
        password_hasher=FakePasswordHasher(),
        token_service=FakeTokenService(),
    )

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(email="ghost@example.com", password="whatever")


async def test_login_rejects_wrong_password() -> None:
    user = build_user(email="user@example.com", password_hash="hashed:correct-password")
    repository = FakeUserRepository(user=user)
    use_case = LoginUserUseCase(
        user_repository=repository,
        password_hasher=FakePasswordHasher(),
        token_service=FakeTokenService(),
    )

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(email="user@example.com", password="wrong-password")


async def test_login_rejects_inactive_user() -> None:
    user = build_user(
        email="user@example.com", password_hash="hashed:correct-password", is_active=False
    )
    repository = FakeUserRepository(user=user)
    use_case = LoginUserUseCase(
        user_repository=repository,
        password_hasher=FakePasswordHasher(),
        token_service=FakeTokenService(),
    )

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(email="user@example.com", password="correct-password")

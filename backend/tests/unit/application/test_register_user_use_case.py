from uuid import UUID

import pytest

from app.application.use_cases.auth.register_user import (
    EmailAlreadyRegisteredError,
    RegisterUserUseCase,
)
from app.domain.entities.user import User
from tests.fixtures.factories import build_user


class FakeUserRepository:
    def __init__(self, *, existing: User | None = None) -> None:
        self.existing = existing
        self.created: User | None = None

    async def get_by_email(self, email: str) -> User | None:
        if self.existing is not None and self.existing.email == email:
            return self.existing
        return None

    async def get_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    async def create(self, *, email: str, password_hash: str) -> User:
        user = build_user(email=email, password_hash=password_hash)
        self.created = user
        return user


class FakePasswordHasher:
    def hash(self, plain_password: str) -> str:
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{plain_password}"


async def test_register_user_creates_user_with_hashed_password() -> None:
    repository = FakeUserRepository()
    use_case = RegisterUserUseCase(user_repository=repository, password_hasher=FakePasswordHasher())

    user = await use_case.execute(email="new@example.com", password="s3cret123")

    assert user.email == "new@example.com"
    assert user.password_hash == "hashed:s3cret123"
    assert repository.created is user


async def test_register_user_rejects_duplicate_email() -> None:
    existing = build_user(email="taken@example.com")
    repository = FakeUserRepository(existing=existing)
    use_case = RegisterUserUseCase(user_repository=repository, password_hasher=FakePasswordHasher())

    with pytest.raises(EmailAlreadyRegisteredError):
        await use_case.execute(email="taken@example.com", password="s3cret123")

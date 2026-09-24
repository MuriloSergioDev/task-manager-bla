from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.entities.user import User


def build_user(
    *,
    id: UUID | None = None,
    email: str = "user@example.com",
    password_hash: str = "hashed-password",
    is_active: bool = True,
) -> User:
    now = datetime.now(UTC)
    return User(
        id=id or uuid4(),
        email=email,
        password_hash=password_hash,
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )

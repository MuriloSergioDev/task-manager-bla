from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from app.domain.entities.task import Task, TaskStatus
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


def build_task(
    *,
    id: UUID | None = None,
    title: str = "Test task",
    description: str | None = None,
    status: TaskStatus = TaskStatus.TODO,
    due_date: date | None = None,
    completed_at: datetime | None = None,
    owner_id: UUID | None = None,
    assigned_to: UUID | None = None,
) -> Task:
    now = datetime.now(UTC)
    return Task(
        id=id or uuid4(),
        title=title,
        description=description,
        status=status,
        due_date=due_date,
        completed_at=completed_at,
        owner_id=owner_id or uuid4(),
        assigned_to=assigned_to,
        created_at=now,
        updated_at=now,
    )

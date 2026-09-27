"""Idempotent demo data seeding.

Run with: python -m scripts.seed (from backend/, with DATABASE_URL set,
e.g. via the api/celery-worker container or a local .env).
"""

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.domain.entities.task import TaskStatus
from app.infrastructure.database.models import TaskModel, UserModel
from app.infrastructure.services.argon2_password_hasher import Argon2PasswordHasher

DEMO_PASSWORD = "DemoPass123!"

# Enough generated tasks that alice's list spans multiple pages at the
# frontend's page size of 20, so pagination is demonstrable out of the box.
BACKLOG_SIZE = 30
_BACKLOG_STATUSES = (TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED)


def _backlog_tasks(owner: UserModel, assignees: list[UserModel | None]) -> list[TaskModel]:
    """Deterministic spread of statuses, due dates (past, future, none) and
    assignees -- no randomness, so every seeded environment looks the same."""
    now = datetime.now(UTC)
    tasks = []
    for index in range(BACKLOG_SIZE):
        status = _BACKLOG_STATUSES[index % len(_BACKLOG_STATUSES)]
        # index // 3 (not index % 3) so assignee varies independently of status.
        assignee = assignees[(index // 3) % len(assignees)]
        due_offset = (index % 9) * 4 - 12  # from 12 days ago to 20 days ahead
        tasks.append(
            TaskModel(
                title=f"Backlog item #{index + 1:02d}",
                description="Generated demo task for pagination and filtering",
                status=status,
                due_date=None if index % 7 == 0 else (now + timedelta(days=due_offset)).date(),
                completed_at=now - timedelta(days=index % 5)
                if status == TaskStatus.COMPLETED
                else None,
                owner_id=owner.id,
                assigned_to=assignee.id if assignee is not None else None,
            )
        )
    return tasks


async def seed() -> None:
    hasher = Argon2PasswordHasher()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.email == "alice@example.com")
        )
        if result.scalar_one_or_none() is not None:
            print("Seed data already present (alice@example.com exists) — skipping.")
            return

        alice = UserModel(
            email="alice@example.com", password_hash=hasher.hash(DEMO_PASSWORD), is_active=True
        )
        bob = UserModel(
            email="bob@example.com", password_hash=hasher.hash(DEMO_PASSWORD), is_active=True
        )
        carol = UserModel(
            email="carol@example.com", password_hash=hasher.hash(DEMO_PASSWORD), is_active=True
        )
        session.add_all([alice, bob, carol])
        await session.flush()

        today = datetime.now(UTC).date()

        tasks = [
            TaskModel(
                title="Draft Q4 roadmap",
                description="Outline priorities for next quarter",
                status=TaskStatus.TODO,
                due_date=today + timedelta(days=7),
                owner_id=alice.id,
                assigned_to=bob.id,
            ),
            TaskModel(
                title="Review pull request #142",
                description="Focus on the auth middleware changes",
                status=TaskStatus.IN_PROGRESS,
                due_date=today + timedelta(days=1),
                owner_id=alice.id,
                assigned_to=carol.id,
            ),
            TaskModel(
                title="Renew SSL certificate",
                description=None,
                status=TaskStatus.TODO,
                due_date=today - timedelta(days=3),
                owner_id=alice.id,
                assigned_to=None,
            ),
            TaskModel(
                title="Fix flaky checkout test",
                description="Intermittent failures in CI on the payment step",
                status=TaskStatus.COMPLETED,
                due_date=today - timedelta(days=10),
                completed_at=datetime.now(UTC) - timedelta(days=8),
                owner_id=bob.id,
                assigned_to=alice.id,
            ),
            TaskModel(
                title="Investigate slow dashboard query",
                description=None,
                status=TaskStatus.TODO,
                due_date=None,
                owner_id=bob.id,
                assigned_to=None,
            ),
            TaskModel(
                title="Write onboarding guide",
                description="For new engineers joining the team",
                status=TaskStatus.IN_PROGRESS,
                due_date=today + timedelta(days=14),
                owner_id=carol.id,
                assigned_to=alice.id,
            ),
            TaskModel(
                title="Rotate database credentials",
                description=None,
                status=TaskStatus.COMPLETED,
                due_date=today - timedelta(days=5),
                completed_at=datetime.now(UTC) - timedelta(days=5),
                owner_id=carol.id,
                assigned_to=bob.id,
            ),
        ]
        tasks += _backlog_tasks(alice, [None, bob, carol])
        session.add_all(tasks)
        await session.commit()

    print("Seed data created:")
    print("  Users: alice@example.com, bob@example.com, carol@example.com")
    print(f"  Password (all demo users): {DEMO_PASSWORD}")
    print(f"  Tasks: {len(tasks)}")


if __name__ == "__main__":
    asyncio.run(seed())

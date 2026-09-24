from datetime import date
from uuid import UUID

import pytest

from app.application.use_cases.tasks.create_task import CreateTaskUseCase
from app.domain.exceptions import AssigneeNotFoundError
from tests.fixtures.factories import build_user
from tests.fixtures.fakes import FakeTaskRepository, FakeUserRepository


async def test_create_task_without_assignee() -> None:
    task_repository = FakeTaskRepository()
    owner_id = build_user().id
    use_case = CreateTaskUseCase(
        task_repository=task_repository, user_repository=FakeUserRepository()
    )

    task = await use_case.execute(
        owner_id=owner_id,
        title="Write report",
        description=None,
        due_date=date(2026, 12, 31),
        assigned_to=None,
    )

    assert task.title == "Write report"
    assert task.owner_id == owner_id
    assert task.assigned_to is None
    assert await task_repository.get_by_id(task.id) == task


async def test_create_task_with_existing_assignee_succeeds() -> None:
    assignee = build_user()
    task_repository = FakeTaskRepository()
    use_case = CreateTaskUseCase(
        task_repository=task_repository, user_repository=FakeUserRepository(users=[assignee])
    )

    task = await use_case.execute(
        owner_id=build_user().id,
        title="Pair up",
        description=None,
        due_date=None,
        assigned_to=assignee.id,
    )

    assert task.assigned_to == assignee.id


async def test_create_task_rejects_unknown_assignee() -> None:
    use_case = CreateTaskUseCase(
        task_repository=FakeTaskRepository(), user_repository=FakeUserRepository()
    )

    with pytest.raises(AssigneeNotFoundError):
        await use_case.execute(
            owner_id=build_user().id,
            title="Orphan assignment",
            description=None,
            due_date=None,
            assigned_to=UUID("00000000-0000-0000-0000-000000000000"),
        )

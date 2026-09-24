import pytest

from app.application.use_cases.tasks.update_task import UpdateTaskUseCase
from app.domain.exceptions import AssigneeNotFoundError, TaskAuthorizationError, TaskNotFoundError
from tests.fixtures.factories import build_task, build_user
from tests.fixtures.fakes import FakeTaskRepository, FakeUserRepository


async def test_owner_can_update_title() -> None:
    owner = build_user()
    task = build_task(owner_id=owner.id, title="Old title")
    use_case = UpdateTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]), user_repository=FakeUserRepository()
    )

    updated = await use_case.execute(
        task_id=task.id, current_user=owner, updates={"title": "New title"}
    )

    assert updated.title == "New title"


async def test_non_owner_cannot_update_task() -> None:
    owner = build_user()
    stranger = build_user()
    task = build_task(owner_id=owner.id)
    use_case = UpdateTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]), user_repository=FakeUserRepository()
    )

    with pytest.raises(TaskAuthorizationError):
        await use_case.execute(
            task_id=task.id, current_user=stranger, updates={"title": "Hijacked"}
        )


async def test_update_raises_when_task_missing() -> None:
    owner = build_user()
    use_case = UpdateTaskUseCase(
        task_repository=FakeTaskRepository(), user_repository=FakeUserRepository()
    )

    with pytest.raises(TaskNotFoundError):
        await use_case.execute(task_id=build_task().id, current_user=owner, updates={"title": "x"})


async def test_update_rejects_unknown_assignee() -> None:
    owner = build_user()
    task = build_task(owner_id=owner.id)
    use_case = UpdateTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]), user_repository=FakeUserRepository()
    )

    with pytest.raises(AssigneeNotFoundError):
        await use_case.execute(
            task_id=task.id,
            current_user=owner,
            updates={"assigned_to": build_user().id},
        )


async def test_update_allows_clearing_assignee_to_none() -> None:
    owner = build_user()
    assignee = build_user()
    task = build_task(owner_id=owner.id, assigned_to=assignee.id)
    use_case = UpdateTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]),
        user_repository=FakeUserRepository(users=[assignee]),
    )

    updated = await use_case.execute(
        task_id=task.id, current_user=owner, updates={"assigned_to": None}
    )

    assert updated.assigned_to is None

import pytest

from app.application.schemas.task_schemas import TaskUpdate
from app.application.use_cases.tasks.update_task import UpdateTaskUseCase
from app.domain.entities.task import TaskStatus
from app.domain.exceptions import (
    AssigneeNotFoundError,
    InvalidStatusChangeError,
    TaskAuthorizationError,
    TaskNotFoundError,
)
from tests.fixtures.factories import build_task, build_user
from tests.fixtures.fakes import FakeTaskRepository, FakeUserRepository


async def test_owner_can_update_title() -> None:
    owner = build_user()
    task = build_task(owner_id=owner.id, title="Old title")
    use_case = UpdateTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]), user_repository=FakeUserRepository()
    )

    updated = await use_case.execute(
        task_id=task.id, current_user=owner, changes=TaskUpdate(title="New title")
    )

    assert updated.title == "New title"


async def test_stranger_updating_task_gets_not_found() -> None:
    owner = build_user()
    stranger = build_user()
    task = build_task(owner_id=owner.id)
    use_case = UpdateTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]), user_repository=FakeUserRepository()
    )

    with pytest.raises(TaskNotFoundError):
        await use_case.execute(
            task_id=task.id, current_user=stranger, changes=TaskUpdate(title="Hijacked")
        )


async def test_update_raises_when_task_missing() -> None:
    owner = build_user()
    use_case = UpdateTaskUseCase(
        task_repository=FakeTaskRepository(), user_repository=FakeUserRepository()
    )

    with pytest.raises(TaskNotFoundError):
        await use_case.execute(
            task_id=build_task().id, current_user=owner, changes=TaskUpdate(title="x")
        )


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
            changes=TaskUpdate(assigned_to=build_user().id),
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
        task_id=task.id, current_user=owner, changes=TaskUpdate(assigned_to=None)
    )

    assert updated.assigned_to is None


async def test_assignee_cannot_reassign_via_update() -> None:
    owner = build_user()
    assignee = build_user()
    other_user = build_user()
    task = build_task(owner_id=owner.id, assigned_to=assignee.id)
    use_case = UpdateTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]),
        user_repository=FakeUserRepository(users=[other_user]),
    )

    # The assignee can see the task, so this is a real permission failure
    # (403), unlike a stranger who gets TaskNotFoundError (404).
    with pytest.raises(TaskAuthorizationError):
        await use_case.execute(
            task_id=task.id, current_user=assignee, changes=TaskUpdate(assigned_to=other_user.id)
        )


async def test_update_cannot_move_a_task_to_completed() -> None:
    owner = build_user()
    task = build_task(owner_id=owner.id, status=TaskStatus.IN_PROGRESS)
    repository = FakeTaskRepository(tasks=[task])
    use_case = UpdateTaskUseCase(task_repository=repository, user_repository=FakeUserRepository())

    with pytest.raises(InvalidStatusChangeError):
        await use_case.execute(
            task_id=task.id, current_user=owner, changes=TaskUpdate(status=TaskStatus.COMPLETED)
        )

    stored = await repository.get_by_id(task.id)
    assert stored is not None
    assert stored.status == TaskStatus.IN_PROGRESS

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


async def test_stranger_updating_task_gets_not_found() -> None:
    owner = build_user()
    stranger = build_user()
    task = build_task(owner_id=owner.id)
    use_case = UpdateTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]), user_repository=FakeUserRepository()
    )

    with pytest.raises(TaskNotFoundError):
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
            task_id=task.id, current_user=assignee, updates={"assigned_to": other_user.id}
        )

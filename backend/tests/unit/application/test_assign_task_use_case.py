import pytest

from app.application.use_cases.tasks.assign_task import AssignTaskUseCase
from app.domain.exceptions import AssigneeNotFoundError, TaskAuthorizationError, TaskNotFoundError
from tests.fixtures.factories import build_task, build_user
from tests.fixtures.fakes import FakeTaskRepository, FakeUserRepository


async def test_owner_can_assign_task_to_existing_user() -> None:
    owner = build_user()
    assignee = build_user()
    task = build_task(owner_id=owner.id)
    use_case = AssignTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]),
        user_repository=FakeUserRepository(users=[assignee]),
    )

    updated = await use_case.execute(task_id=task.id, current_user=owner, assigned_to=assignee.id)

    assert updated.assigned_to == assignee.id


async def test_owner_can_unassign_task() -> None:
    owner = build_user()
    assignee = build_user()
    task = build_task(owner_id=owner.id, assigned_to=assignee.id)
    use_case = AssignTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]),
        user_repository=FakeUserRepository(users=[assignee]),
    )

    updated = await use_case.execute(task_id=task.id, current_user=owner, assigned_to=None)

    assert updated.assigned_to is None


async def test_assignee_cannot_reassign_task() -> None:
    owner = build_user()
    assignee = build_user()
    other_user = build_user()
    task = build_task(owner_id=owner.id, assigned_to=assignee.id)
    use_case = AssignTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]),
        user_repository=FakeUserRepository(users=[other_user]),
    )

    with pytest.raises(TaskAuthorizationError):
        await use_case.execute(task_id=task.id, current_user=assignee, assigned_to=other_user.id)


async def test_assign_rejects_unknown_user() -> None:
    owner = build_user()
    task = build_task(owner_id=owner.id)
    use_case = AssignTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]), user_repository=FakeUserRepository()
    )

    with pytest.raises(AssigneeNotFoundError):
        await use_case.execute(task_id=task.id, current_user=owner, assigned_to=build_user().id)


async def test_assign_raises_when_task_missing() -> None:
    use_case = AssignTaskUseCase(
        task_repository=FakeTaskRepository(), user_repository=FakeUserRepository()
    )

    with pytest.raises(TaskNotFoundError):
        await use_case.execute(task_id=build_task().id, current_user=build_user(), assigned_to=None)

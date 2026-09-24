import pytest

from app.application.use_cases.tasks.delete_task import DeleteTaskUseCase
from app.domain.exceptions import TaskAuthorizationError, TaskNotFoundError
from tests.fixtures.factories import build_task, build_user
from tests.fixtures.fakes import FakeTaskRepository


async def test_owner_can_delete_task() -> None:
    owner = build_user()
    task = build_task(owner_id=owner.id)
    repository = FakeTaskRepository(tasks=[task])
    use_case = DeleteTaskUseCase(task_repository=repository)

    await use_case.execute(task_id=task.id, current_user=owner)

    assert await repository.get_by_id(task.id) is None


async def test_non_owner_cannot_delete_task() -> None:
    owner = build_user()
    stranger = build_user()
    task = build_task(owner_id=owner.id)
    repository = FakeTaskRepository(tasks=[task])
    use_case = DeleteTaskUseCase(task_repository=repository)

    with pytest.raises(TaskAuthorizationError):
        await use_case.execute(task_id=task.id, current_user=stranger)

    assert await repository.get_by_id(task.id) is not None


async def test_delete_raises_when_task_missing() -> None:
    use_case = DeleteTaskUseCase(task_repository=FakeTaskRepository())

    with pytest.raises(TaskNotFoundError):
        await use_case.execute(task_id=build_task().id, current_user=build_user())

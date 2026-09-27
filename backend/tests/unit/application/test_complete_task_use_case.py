import pytest

from app.application.use_cases.tasks.complete_task import CompleteTaskUseCase
from app.domain.entities.task import TaskStatus
from app.domain.exceptions import TaskNotFoundError
from tests.fixtures.factories import build_task, build_user
from tests.fixtures.fakes import FakeActivityDispatcher, FakeTaskRepository


async def test_owner_can_complete_task() -> None:
    owner = build_user()
    task = build_task(owner_id=owner.id, status=TaskStatus.IN_PROGRESS)
    use_case = CompleteTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]),
        activity_dispatcher=FakeActivityDispatcher(),
    )

    completed = await use_case.execute(task_id=task.id, current_user=owner)

    assert completed.status == TaskStatus.COMPLETED
    assert completed.completed_at is not None


async def test_completing_a_task_dispatches_activity_event() -> None:
    owner = build_user()
    task = build_task(owner_id=owner.id, status=TaskStatus.IN_PROGRESS)
    dispatcher = FakeActivityDispatcher()
    use_case = CompleteTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]), activity_dispatcher=dispatcher
    )

    await use_case.execute(task_id=task.id, current_user=owner)

    assert dispatcher.dispatched == [(task.id, owner.id, "IN_PROGRESS")]


async def test_assignee_can_complete_task() -> None:
    owner = build_user()
    assignee = build_user()
    task = build_task(owner_id=owner.id, assigned_to=assignee.id)
    use_case = CompleteTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]),
        activity_dispatcher=FakeActivityDispatcher(),
    )

    completed = await use_case.execute(task_id=task.id, current_user=assignee)

    assert completed.status == TaskStatus.COMPLETED


async def test_stranger_completing_task_gets_not_found() -> None:
    owner = build_user()
    stranger = build_user()
    task = build_task(owner_id=owner.id)
    dispatcher = FakeActivityDispatcher()
    use_case = CompleteTaskUseCase(
        task_repository=FakeTaskRepository(tasks=[task]), activity_dispatcher=dispatcher
    )

    with pytest.raises(TaskNotFoundError):
        await use_case.execute(task_id=task.id, current_user=stranger)

    assert dispatcher.dispatched == []


async def test_complete_raises_when_task_missing() -> None:
    use_case = CompleteTaskUseCase(
        task_repository=FakeTaskRepository(), activity_dispatcher=FakeActivityDispatcher()
    )

    with pytest.raises(TaskNotFoundError):
        await use_case.execute(task_id=build_task().id, current_user=build_user())

import pytest

from app.application.use_cases.tasks.get_task import GetTaskUseCase
from app.application.use_cases.tasks.list_tasks import ListTasksUseCase
from app.domain.exceptions import TaskNotFoundError
from tests.fixtures.factories import build_task, build_user
from tests.fixtures.fakes import FakeTaskRepository


async def test_get_task_returns_existing_task() -> None:
    task = build_task()
    repository = FakeTaskRepository(tasks=[task])
    use_case = GetTaskUseCase(task_repository=repository)

    result = await use_case.execute(task.id)

    assert result == task


async def test_get_task_raises_when_missing() -> None:
    use_case = GetTaskUseCase(task_repository=FakeTaskRepository())

    with pytest.raises(TaskNotFoundError):
        await use_case.execute(build_task().id)


async def test_list_tasks_paginates_results() -> None:
    owner = build_user()
    tasks = [build_task(owner_id=owner.id, title=f"Task {i}") for i in range(5)]
    repository = FakeTaskRepository(tasks=tasks)
    use_case = ListTasksUseCase(task_repository=repository)

    page_one, total = await use_case.execute(page=1, page_size=2)
    page_two, _ = await use_case.execute(page=2, page_size=2)

    assert total == 5
    assert len(page_one) == 2
    assert len(page_two) == 2
    assert {task.id for task in page_one}.isdisjoint({task.id for task in page_two})


async def test_list_tasks_returns_empty_when_no_tasks_exist() -> None:
    use_case = ListTasksUseCase(task_repository=FakeTaskRepository())

    items, total = await use_case.execute(page=1, page_size=20)

    assert items == []
    assert total == 0

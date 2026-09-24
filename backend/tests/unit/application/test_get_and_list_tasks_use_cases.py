from datetime import date

import pytest

from app.application.use_cases.tasks.get_task import GetTaskUseCase
from app.application.use_cases.tasks.list_tasks import ListTasksUseCase
from app.domain.entities.task import TaskStatus
from app.domain.exceptions import TaskNotFoundError
from app.domain.repositories.task_repository import TaskFilters
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


async def test_list_tasks_filters_by_status() -> None:
    owner = build_user()
    todo_task = build_task(owner_id=owner.id, status=TaskStatus.TODO)
    done_task = build_task(owner_id=owner.id, status=TaskStatus.COMPLETED)
    repository = FakeTaskRepository(tasks=[todo_task, done_task])
    use_case = ListTasksUseCase(task_repository=repository)

    items, total = await use_case.execute(
        page=1, page_size=20, filters=TaskFilters(status=TaskStatus.TODO)
    )

    assert total == 1
    assert [task.id for task in items] == [todo_task.id]


async def test_list_tasks_filters_by_due_date_range() -> None:
    owner = build_user()
    in_range = build_task(owner_id=owner.id, due_date=date(2026, 6, 15))
    out_of_range = build_task(owner_id=owner.id, due_date=date(2026, 7, 1))
    no_due_date = build_task(owner_id=owner.id, due_date=None)
    repository = FakeTaskRepository(tasks=[in_range, out_of_range, no_due_date])
    use_case = ListTasksUseCase(task_repository=repository)

    items, total = await use_case.execute(
        page=1,
        page_size=20,
        filters=TaskFilters(due_date_from=date(2026, 6, 1), due_date_to=date(2026, 6, 30)),
    )

    assert total == 1
    assert [task.id for task in items] == [in_range.id]

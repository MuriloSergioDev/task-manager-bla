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
    owner = build_user()
    task = build_task(owner_id=owner.id)
    repository = FakeTaskRepository(tasks=[task])
    use_case = GetTaskUseCase(task_repository=repository)

    result = await use_case.execute(task_id=task.id, current_user=owner)

    assert result == task


async def test_get_task_returns_task_to_assignee() -> None:
    assignee = build_user()
    task = build_task(owner_id=build_user().id, assigned_to=assignee.id)
    use_case = GetTaskUseCase(task_repository=FakeTaskRepository(tasks=[task]))

    assert await use_case.execute(task_id=task.id, current_user=assignee) == task


async def test_get_task_raises_when_missing() -> None:
    use_case = GetTaskUseCase(task_repository=FakeTaskRepository())

    with pytest.raises(TaskNotFoundError):
        await use_case.execute(task_id=build_task().id, current_user=build_user())


async def test_get_task_hides_other_users_task_as_not_found() -> None:
    task = build_task(owner_id=build_user().id)
    use_case = GetTaskUseCase(task_repository=FakeTaskRepository(tasks=[task]))

    with pytest.raises(TaskNotFoundError):
        await use_case.execute(task_id=task.id, current_user=build_user())


async def test_list_tasks_paginates_results() -> None:
    owner = build_user()
    tasks = [build_task(owner_id=owner.id, title=f"Task {i}") for i in range(5)]
    repository = FakeTaskRepository(tasks=tasks)
    use_case = ListTasksUseCase(task_repository=repository)

    page_one, total = await use_case.execute(current_user=owner, page=1, page_size=2)
    page_two, _ = await use_case.execute(current_user=owner, page=2, page_size=2)

    assert total == 5
    assert len(page_one) == 2
    assert len(page_two) == 2
    assert {task.id for task in page_one}.isdisjoint({task.id for task in page_two})


async def test_list_tasks_returns_empty_when_no_tasks_exist() -> None:
    use_case = ListTasksUseCase(task_repository=FakeTaskRepository())

    items, total = await use_case.execute(current_user=build_user(), page=1, page_size=20)

    assert items == []
    assert total == 0


async def test_list_tasks_filters_by_status() -> None:
    owner = build_user()
    todo_task = build_task(owner_id=owner.id, status=TaskStatus.TODO)
    done_task = build_task(owner_id=owner.id, status=TaskStatus.COMPLETED)
    repository = FakeTaskRepository(tasks=[todo_task, done_task])
    use_case = ListTasksUseCase(task_repository=repository)

    items, total = await use_case.execute(
        current_user=owner, page=1, page_size=20, filters=TaskFilters(status=TaskStatus.TODO)
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
        current_user=owner,
        page=1,
        page_size=20,
        filters=TaskFilters(due_date_from=date(2026, 6, 1), due_date_to=date(2026, 6, 30)),
    )

    assert total == 1
    assert [task.id for task in items] == [in_range.id]


async def test_list_tasks_only_returns_tasks_owned_by_or_assigned_to_current_user() -> None:
    me = build_user()
    someone_else = build_user()
    owned = build_task(owner_id=me.id)
    assigned_to_me = build_task(owner_id=someone_else.id, assigned_to=me.id)
    not_mine = build_task(owner_id=someone_else.id)
    use_case = ListTasksUseCase(
        task_repository=FakeTaskRepository(tasks=[owned, assigned_to_me, not_mine])
    )

    items, total = await use_case.execute(current_user=me, page=1, page_size=20)

    assert total == 2
    assert {task.id for task in items} == {owned.id, assigned_to_me.id}


async def test_list_tasks_scope_cannot_be_widened_by_caller_filters() -> None:
    me = build_user()
    other = build_user()
    not_mine = build_task(owner_id=other.id)
    use_case = ListTasksUseCase(task_repository=FakeTaskRepository(tasks=[not_mine]))

    # Even a caller passing someone else's id gets scoped to current_user.
    items, total = await use_case.execute(
        current_user=me, page=1, page_size=20, filters=TaskFilters(visible_to=other.id)
    )

    assert total == 0
    assert items == []

from dataclasses import replace
from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.task_repository import TaskFilters
from app.infrastructure.database.models import UserModel
from app.infrastructure.repositories.sqlalchemy_task_repository import SqlAlchemyTaskRepository
from tests.fixtures.factories import build_task


async def _create_user(session: AsyncSession, email: str) -> UserModel:
    user = UserModel(email=email, password_hash="hashed", is_active=True)
    session.add(user)
    await session.flush()
    return user


async def test_create_and_get_by_id_round_trip(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session, "owner@example.com")
    repository = SqlAlchemyTaskRepository(db_session)

    created = await repository.create(
        title="Write docs",
        description="Architecture doc",
        due_date=date(2026, 10, 1),
        owner_id=owner.id,
        assigned_to=None,
    )

    fetched = await repository.get_by_id(created.id)

    assert fetched is not None
    assert fetched.title == "Write docs"
    assert fetched.owner_id == owner.id
    assert fetched.status.value == "TODO"


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repository = SqlAlchemyTaskRepository(db_session)

    result = await repository.get_by_id(uuid4())

    assert result is None


async def test_list_paginated_orders_newest_first_and_reports_total(
    db_session: AsyncSession,
) -> None:
    owner = await _create_user(db_session, "owner2@example.com")
    repository = SqlAlchemyTaskRepository(db_session)
    for i in range(3):
        await repository.create(
            title=f"Task {i}",
            description=None,
            due_date=None,
            owner_id=owner.id,
            assigned_to=None,
        )

    items, total = await repository.list_paginated(page=1, page_size=2, filters=TaskFilters())

    assert total == 3
    assert len(items) == 2
    assert items[0].created_at >= items[1].created_at


async def test_save_persists_mutable_fields_only(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session, "owner3@example.com")
    repository = SqlAlchemyTaskRepository(db_session)
    task = await repository.create(
        title="Original", description=None, due_date=None, owner_id=owner.id, assigned_to=None
    )

    updated = replace(task, title="Renamed")
    saved = await repository.save(updated)

    assert saved.title == "Renamed"
    assert saved.owner_id == owner.id


async def test_save_raises_when_task_no_longer_exists(db_session: AsyncSession) -> None:
    repository = SqlAlchemyTaskRepository(db_session)

    with pytest.raises(ValueError, match="does not exist"):
        await repository.save(build_task())


async def test_delete_removes_task(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session, "owner4@example.com")
    repository = SqlAlchemyTaskRepository(db_session)
    task = await repository.create(
        title="Ephemeral", description=None, due_date=None, owner_id=owner.id, assigned_to=None
    )

    await repository.delete(task.id)

    assert await repository.get_by_id(task.id) is None


async def test_deleting_owner_cascades_to_their_tasks(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session, "owner5@example.com")
    repository = SqlAlchemyTaskRepository(db_session)
    task = await repository.create(
        title="Owned", description=None, due_date=None, owner_id=owner.id, assigned_to=None
    )

    await db_session.delete(owner)
    await db_session.commit()

    assert await repository.get_by_id(task.id) is None


async def test_deleting_assignee_unassigns_but_keeps_task(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session, "owner6@example.com")
    assignee = await _create_user(db_session, "assignee6@example.com")
    repository = SqlAlchemyTaskRepository(db_session)
    task = await repository.create(
        title="Assigned",
        description=None,
        due_date=None,
        owner_id=owner.id,
        assigned_to=assignee.id,
    )

    await db_session.delete(assignee)
    await db_session.commit()

    result = await repository.get_by_id(task.id)
    assert result is not None
    assert result.assigned_to is None


async def test_list_paginated_visible_to_matches_owner_or_assignee(
    db_session: AsyncSession,
) -> None:
    me = await _create_user(db_session, "visible-me@example.com")
    other = await _create_user(db_session, "visible-other@example.com")
    repository = SqlAlchemyTaskRepository(db_session)
    owned = await repository.create(
        title="Mine", description=None, due_date=None, owner_id=me.id, assigned_to=None
    )
    assigned = await repository.create(
        title="Assigned to me",
        description=None,
        due_date=None,
        owner_id=other.id,
        assigned_to=me.id,
    )
    await repository.create(
        title="Not mine", description=None, due_date=None, owner_id=other.id, assigned_to=None
    )

    items, total = await repository.list_paginated(
        page=1, page_size=20, filters=TaskFilters(visible_to=me.id)
    )

    assert total == 2
    assert {task.id for task in items} == {owned.id, assigned.id}


async def test_list_paginated_pages_are_stable_when_created_at_ties(
    db_session: AsyncSession,
) -> None:
    # Postgres's now() is the transaction's start time, so every task
    # inserted in one transaction (the seed script, or this test) shares a
    # created_at. Ordering by created_at alone leaves ties in no defined
    # order, and LIMIT/OFFSET can then repeat or skip rows across pages.
    owner = await _create_user(db_session, "tie-break-owner@example.com")
    repository = SqlAlchemyTaskRepository(db_session)
    created_ids = set()
    for i in range(30):
        task = await repository.create(
            title=f"Tied task {i}",
            description=None,
            due_date=None,
            owner_id=owner.id,
            assigned_to=None,
        )
        created_ids.add(task.id)

    seen_ids = []
    for page in range(1, 6):
        items, total = await repository.list_paginated(
            page=page, page_size=7, filters=TaskFilters(visible_to=owner.id)
        )
        seen_ids.extend(item.id for item in items)

    assert total == 30
    assert len(seen_ids) == len(set(seen_ids)), "a task appeared on more than one page"
    assert set(seen_ids) == created_ids

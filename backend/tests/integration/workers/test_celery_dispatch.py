import asyncio
import time
from collections.abc import Generator
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.infrastructure.database.models import ActivityLogModel, TaskModel, UserModel
from app.workers.celery_app import celery_app
from app.workers.tasks import record_task_completed_activity

# NullPool: each asyncio.run() call below tears down its event loop, and a
# pooled asyncpg connection can't be reused once its loop is closed (the
# same reason app/workers/tasks.py uses its own NullPool engine).
_engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
_SessionLocal = async_sessionmaker(_engine, expire_on_commit=False)


@pytest.fixture
def eager_celery() -> Generator[None, None, None]:
    """Runs .delay() synchronously in-process, per the project's documented
    strategy for testing Celery dispatch without a running broker/worker."""
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_eager_propagates = False


async def _create_user_and_task() -> tuple[str, str]:
    async with _SessionLocal() as session:
        user = UserModel(email="celery-test-user@example.com", password_hash="x", is_active=True)
        session.add(user)
        await session.flush()

        task = TaskModel(title="Celery test task", owner_id=user.id)
        session.add(task)
        await session.commit()
        return str(user.id), str(task.id)


async def _fetch_activity_log(task_id: str) -> ActivityLogModel | None:
    async with _SessionLocal() as session:
        result = await session.execute(
            select(ActivityLogModel).where(ActivityLogModel.task_id == task_id)
        )
        return result.scalar_one_or_none()


async def _cleanup(user_id: str, task_id: str) -> None:
    async with _SessionLocal() as session:
        await session.execute(delete(ActivityLogModel).where(ActivityLogModel.task_id == task_id))
        await session.execute(delete(TaskModel).where(TaskModel.id == task_id))
        await session.execute(delete(UserModel).where(UserModel.id == user_id))
        await session.commit()


def test_record_task_completed_activity_writes_activity_log(eager_celery: None) -> None:
    # This test writes real, committed rows (the task opens its own DB
    # session, independent of the app's per-request transaction) and cleans
    # them up explicitly rather than relying on the transactional-rollback
    # `db_session` fixture used elsewhere.
    user_id, task_id = asyncio.run(_create_user_and_task())

    try:
        record_task_completed_activity.delay(task_id, user_id, "IN_PROGRESS")

        log = asyncio.run(_fetch_activity_log(task_id))

        assert log is not None
        assert log.event_type == "TASK_COMPLETED"
        assert str(log.actor_user_id) == user_id
        assert log.payload == {"previous_status": "IN_PROGRESS"}
    finally:
        asyncio.run(_cleanup(user_id, task_id))


def test_record_task_completed_activity_does_not_retry_a_missing_task(
    eager_celery: None,
) -> None:
    # Discovered via manual end-to-end testing: completing a task and then
    # immediately deleting it (a legitimate real sequence, not just a test
    # artifact) races the async activity-log write against the delete. The
    # resulting foreign-key violation is permanent -- retrying can't make a
    # deleted row reappear -- so this must fail fast, not burn 3 retries.
    nonexistent_task_id = str(uuid4())
    nonexistent_actor_id = str(uuid4())

    started = time.monotonic()
    record_task_completed_activity.delay(nonexistent_task_id, nonexistent_actor_id, "TODO")
    elapsed = time.monotonic() - started

    # A real retry attempt sleeps 10s per Celery's default_retry_delay; a
    # fast return confirms the IntegrityError branch fired instead.
    assert elapsed < 5

    log = asyncio.run(_fetch_activity_log(nonexistent_task_id))
    assert log is None

import asyncio
import logging
from typing import Any
from uuid import UUID

from celery.exceptions import MaxRetriesExceededError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.infrastructure.repositories.sqlalchemy_activity_log_repository import (
    SqlAlchemyActivityLogRepository,
)
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# NullPool: each call opens a fresh connection instead of reusing one from a
# pool. This task runs via asyncio.run(), which tears down its event loop on
# every invocation — a pooled connection checked out under one loop can't be
# reused once that loop is closed, so a persistent pool (like the app's own
# AsyncSessionLocal) would fail on the task's second-ever invocation.
_worker_engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
_WorkerSessionLocal = async_sessionmaker(_worker_engine, expire_on_commit=False)


async def _record_activity(task_id: str, actor_user_id: str, previous_status: str) -> None:
    async with _WorkerSessionLocal() as session:
        repository = SqlAlchemyActivityLogRepository(session)
        await repository.create(
            task_id=UUID(task_id),
            event_type="TASK_COMPLETED",
            actor_user_id=UUID(actor_user_id),
            payload={"previous_status": previous_status},
        )


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10, acks_late=True)  # type: ignore[untyped-decorator]
def record_task_completed_activity(
    self: Any, task_id: str, actor_user_id: str, previous_status: str
) -> None:
    try:
        asyncio.run(_record_activity(task_id, actor_user_id, previous_status))
    except IntegrityError as exc:
        # A foreign-key violation here means the task (or actor) referenced
        # no longer exists -- e.g. it was deleted between completion and
        # this task running. That's permanent, not transient: retrying
        # can't make a deleted row reappear, so don't burn retries on it.
        logger.error("Cannot record activity for task %s: %s", task_id, exc)
    except Exception as exc:
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            # Non-critical operation: never let a failed activity log
            # propagate as a failure of the task-completion request itself.
            logger.error("Exhausted retries recording activity log for task %s: %s", task_id, exc)

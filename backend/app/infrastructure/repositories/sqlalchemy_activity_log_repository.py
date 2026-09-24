from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.activity_log import ActivityLog
from app.infrastructure.database.models import ActivityLogModel


class SqlAlchemyActivityLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        task_id: UUID,
        event_type: str,
        actor_user_id: UUID,
        payload: dict[str, Any] | None,
    ) -> ActivityLog:
        model = ActivityLogModel(
            task_id=task_id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            payload=payload,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return ActivityLog(
            id=model.id,
            task_id=model.task_id,
            event_type=model.event_type,
            actor_user_id=model.actor_user_id,
            payload=model.payload,
            created_at=model.created_at,
        )

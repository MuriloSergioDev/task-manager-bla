from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.activity_log import ActivityLog


class ActivityLogRepository(Protocol):
    async def create(
        self,
        *,
        task_id: UUID,
        event_type: str,
        actor_user_id: UUID,
        payload: dict[str, Any] | None,
    ) -> ActivityLog: ...

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ActivityLog:
    id: UUID
    task_id: UUID
    event_type: str
    actor_user_id: UUID
    payload: dict[str, Any] | None
    created_at: datetime

from typing import Protocol
from uuid import UUID


class ActivityDispatcher(Protocol):
    def dispatch_task_completed(
        self, *, task_id: UUID, actor_user_id: UUID, previous_status: str
    ) -> None: ...

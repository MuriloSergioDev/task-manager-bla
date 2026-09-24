from uuid import UUID

from app.workers.tasks import record_task_completed_activity


class CeleryActivityDispatcher:
    def dispatch_task_completed(
        self, *, task_id: UUID, actor_user_id: UUID, previous_status: str
    ) -> None:
        record_task_completed_activity.delay(str(task_id), str(actor_user_id), previous_status)

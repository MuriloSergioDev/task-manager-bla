import logging
from uuid import UUID

from kombu.exceptions import OperationalError

from app.workers.tasks import record_task_completed_activity

logger = logging.getLogger(__name__)


class CeleryActivityDispatcher:
    def dispatch_task_completed(
        self, *, task_id: UUID, actor_user_id: UUID, previous_status: str
    ) -> None:
        try:
            record_task_completed_activity.delay(str(task_id), str(actor_user_id), previous_status)
        except OperationalError:
            # The completion is already committed, and the activity log is
            # non-critical: if the broker is unreachable, lose the event and
            # say so rather than turn a successful request into a 500. A
            # transactional outbox would keep it; see the README.
            logger.exception("Could not enqueue completed-activity event for task %s", task_id)

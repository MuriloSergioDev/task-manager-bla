from unittest.mock import patch
from uuid import uuid4

from app.infrastructure.services.celery_activity_dispatcher import CeleryActivityDispatcher


def test_dispatch_task_completed_calls_delay_with_stringified_args() -> None:
    task_id = uuid4()
    actor_user_id = uuid4()
    dispatcher = CeleryActivityDispatcher()

    with patch(
        "app.infrastructure.services.celery_activity_dispatcher.record_task_completed_activity"
    ) as mock_task:
        dispatcher.dispatch_task_completed(
            task_id=task_id, actor_user_id=actor_user_id, previous_status="IN_PROGRESS"
        )

    mock_task.delay.assert_called_once_with(str(task_id), str(actor_user_id), "IN_PROGRESS")

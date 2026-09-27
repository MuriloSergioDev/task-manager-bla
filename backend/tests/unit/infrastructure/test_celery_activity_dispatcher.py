import logging
from unittest.mock import patch
from uuid import uuid4

import pytest
from kombu.exceptions import OperationalError

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


def test_dispatch_does_not_fail_the_request_when_the_broker_is_down(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The completion is already committed when this runs, so raising here
    # would return a 500 for a change that did happen.
    dispatcher = CeleryActivityDispatcher()
    task_id = uuid4()

    with patch(
        "app.infrastructure.services.celery_activity_dispatcher.record_task_completed_activity"
    ) as mock_task:
        mock_task.delay.side_effect = OperationalError("Error 111 connecting to redis")
        with caplog.at_level(logging.ERROR):
            dispatcher.dispatch_task_completed(
                task_id=task_id, actor_user_id=uuid4(), previous_status="TODO"
            )

    assert str(task_id) in caplog.text

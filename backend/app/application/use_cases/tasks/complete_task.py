from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID

from app.application.use_cases.tasks.task_lookup import get_visible_task
from app.domain.entities.task import Task, TaskStatus
from app.domain.entities.user import User
from app.domain.exceptions import TaskAuthorizationError
from app.domain.repositories.task_repository import TaskRepository
from app.domain.services.activity_dispatcher import ActivityDispatcher
from app.domain.services.authorization_service import TaskAuthorizationService


@dataclass
class CompleteTaskUseCase:
    task_repository: TaskRepository
    activity_dispatcher: ActivityDispatcher

    async def execute(self, *, task_id: UUID, current_user: User) -> Task:
        task = await get_visible_task(self.task_repository, task_id, current_user)

        if not TaskAuthorizationService.can_complete(current_user, task):
            raise TaskAuthorizationError("Only the task owner or assignee can complete this task")

        previous_status = task.status
        completed_task = replace(task, status=TaskStatus.COMPLETED, completed_at=datetime.now(UTC))
        saved_task = await self.task_repository.save(completed_task)

        # Dispatched only after the commit succeeds, so a rolled-back
        # completion never produces a phantom activity event.
        self.activity_dispatcher.dispatch_task_completed(
            task_id=saved_task.id,
            actor_user_id=current_user.id,
            previous_status=previous_status.value,
        )

        return saved_task

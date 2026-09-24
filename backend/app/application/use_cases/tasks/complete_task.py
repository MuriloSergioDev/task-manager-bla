from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID

from app.domain.entities.task import Task, TaskStatus
from app.domain.entities.user import User
from app.domain.exceptions import TaskAuthorizationError, TaskNotFoundError
from app.domain.repositories.task_repository import TaskRepository
from app.domain.services.authorization_service import TaskAuthorizationService


@dataclass
class CompleteTaskUseCase:
    task_repository: TaskRepository

    async def execute(self, *, task_id: UUID, current_user: User) -> Task:
        task = await self.task_repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(str(task_id))

        if not TaskAuthorizationService.can_complete(current_user, task):
            raise TaskAuthorizationError("Only the task owner or assignee can complete this task")

        completed_task = replace(task, status=TaskStatus.COMPLETED, completed_at=datetime.now(UTC))
        return await self.task_repository.save(completed_task)

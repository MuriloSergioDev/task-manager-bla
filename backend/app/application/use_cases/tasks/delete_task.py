from dataclasses import dataclass
from uuid import UUID

from app.application.use_cases.tasks.task_lookup import get_visible_task
from app.domain.entities.user import User
from app.domain.exceptions import TaskAuthorizationError
from app.domain.repositories.task_repository import TaskRepository
from app.domain.services.authorization_service import TaskAuthorizationService


@dataclass
class DeleteTaskUseCase:
    task_repository: TaskRepository

    async def execute(self, *, task_id: UUID, current_user: User) -> None:
        task = await get_visible_task(self.task_repository, task_id, current_user)

        if not TaskAuthorizationService.can_delete(current_user, task):
            raise TaskAuthorizationError("Only the task owner or assignee can delete this task")

        await self.task_repository.delete(task_id)

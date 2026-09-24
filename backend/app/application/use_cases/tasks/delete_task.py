from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.user import User
from app.domain.exceptions import TaskAuthorizationError, TaskNotFoundError
from app.domain.repositories.task_repository import TaskRepository
from app.domain.services.authorization_service import TaskAuthorizationService


@dataclass
class DeleteTaskUseCase:
    task_repository: TaskRepository

    async def execute(self, *, task_id: UUID, current_user: User) -> None:
        task = await self.task_repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(str(task_id))

        if not TaskAuthorizationService.can_delete(current_user, task):
            raise TaskAuthorizationError("Only the task owner can delete this task")

        await self.task_repository.delete(task_id)

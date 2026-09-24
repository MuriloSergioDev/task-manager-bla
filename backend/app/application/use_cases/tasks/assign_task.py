from dataclasses import dataclass, replace
from uuid import UUID

from app.domain.entities.task import Task
from app.domain.entities.user import User
from app.domain.exceptions import AssigneeNotFoundError, TaskAuthorizationError, TaskNotFoundError
from app.domain.repositories.task_repository import TaskRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.authorization_service import TaskAuthorizationService


@dataclass
class AssignTaskUseCase:
    task_repository: TaskRepository
    user_repository: UserRepository

    async def execute(self, *, task_id: UUID, current_user: User, assigned_to: UUID | None) -> Task:
        task = await self.task_repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(str(task_id))

        if not TaskAuthorizationService.can_assign(current_user, task):
            raise TaskAuthorizationError("Only the task owner can reassign this task")

        if assigned_to is not None and await self.user_repository.get_by_id(assigned_to) is None:
            raise AssigneeNotFoundError(str(assigned_to))

        updated_task = replace(task, assigned_to=assigned_to)
        return await self.task_repository.save(updated_task)

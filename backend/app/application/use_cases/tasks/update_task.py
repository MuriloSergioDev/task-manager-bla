from dataclasses import dataclass, replace
from typing import Any
from uuid import UUID

from app.domain.entities.task import Task
from app.domain.entities.user import User
from app.domain.exceptions import AssigneeNotFoundError, TaskAuthorizationError, TaskNotFoundError
from app.domain.repositories.task_repository import TaskRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.authorization_service import TaskAuthorizationService


@dataclass
class UpdateTaskUseCase:
    task_repository: TaskRepository
    user_repository: UserRepository

    async def execute(self, *, task_id: UUID, current_user: User, updates: dict[str, Any]) -> Task:
        task = await self.task_repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(str(task_id))

        if not TaskAuthorizationService.can_edit(current_user, task):
            raise TaskAuthorizationError("Only the task owner can update this task")

        if "assigned_to" in updates and updates["assigned_to"] is not None:
            new_assignee = updates["assigned_to"]
            if await self.user_repository.get_by_id(new_assignee) is None:
                raise AssigneeNotFoundError(str(new_assignee))

        updated_task = replace(task, **updates)
        return await self.task_repository.save(updated_task)

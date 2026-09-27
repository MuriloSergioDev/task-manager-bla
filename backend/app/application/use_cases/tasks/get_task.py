from dataclasses import dataclass
from uuid import UUID

from app.application.use_cases.tasks.task_lookup import get_visible_task
from app.domain.entities.task import Task
from app.domain.entities.user import User
from app.domain.repositories.task_repository import TaskRepository


@dataclass
class GetTaskUseCase:
    task_repository: TaskRepository

    async def execute(self, *, task_id: UUID, current_user: User) -> Task:
        return await get_visible_task(self.task_repository, task_id, current_user)

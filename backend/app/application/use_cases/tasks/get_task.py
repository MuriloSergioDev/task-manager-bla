from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.task import Task
from app.domain.exceptions import TaskNotFoundError
from app.domain.repositories.task_repository import TaskRepository


@dataclass
class GetTaskUseCase:
    task_repository: TaskRepository

    async def execute(self, task_id: UUID) -> Task:
        task = await self.task_repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(str(task_id))
        return task

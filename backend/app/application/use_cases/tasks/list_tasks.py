from dataclasses import dataclass

from app.domain.entities.task import Task
from app.domain.repositories.task_repository import TaskRepository


@dataclass
class ListTasksUseCase:
    task_repository: TaskRepository

    async def execute(self, *, page: int, page_size: int) -> tuple[list[Task], int]:
        return await self.task_repository.list_paginated(page=page, page_size=page_size)

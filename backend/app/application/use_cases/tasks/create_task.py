from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.domain.entities.task import Task
from app.domain.exceptions import AssigneeNotFoundError
from app.domain.repositories.task_repository import TaskRepository
from app.domain.repositories.user_repository import UserRepository


@dataclass
class CreateTaskUseCase:
    task_repository: TaskRepository
    user_repository: UserRepository

    async def execute(
        self,
        *,
        owner_id: UUID,
        title: str,
        description: str | None,
        due_date: date | None,
        assigned_to: UUID | None,
    ) -> Task:
        if assigned_to is not None and await self.user_repository.get_by_id(assigned_to) is None:
            raise AssigneeNotFoundError(str(assigned_to))

        return await self.task_repository.create(
            title=title,
            description=description,
            due_date=due_date,
            owner_id=owner_id,
            assigned_to=assigned_to,
        )

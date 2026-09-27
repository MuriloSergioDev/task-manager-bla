from dataclasses import dataclass, replace

from app.domain.entities.task import Task
from app.domain.entities.user import User
from app.domain.repositories.task_repository import TaskFilters, TaskRepository


@dataclass
class ListTasksUseCase:
    task_repository: TaskRepository

    async def execute(
        self,
        *,
        current_user: User,
        page: int,
        page_size: int,
        filters: TaskFilters | None = None,
    ) -> tuple[list[Task], int]:
        # Scope is forced here, not taken from the caller, so no route can
        # forget it (or widen it) -- users only ever list tasks they own or
        # are assigned to, matching TaskAuthorizationService.can_view.
        scoped_filters = replace(filters or TaskFilters(), visible_to=current_user.id)
        return await self.task_repository.list_paginated(
            page=page, page_size=page_size, filters=scoped_filters
        )

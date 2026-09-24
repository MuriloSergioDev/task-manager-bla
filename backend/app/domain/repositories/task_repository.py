from datetime import date
from typing import Protocol
from uuid import UUID

from app.domain.entities.task import Task


class TaskRepository(Protocol):
    async def create(
        self,
        *,
        title: str,
        description: str | None,
        due_date: date | None,
        owner_id: UUID,
        assigned_to: UUID | None,
    ) -> Task: ...

    async def get_by_id(self, task_id: UUID) -> Task | None: ...

    async def list_paginated(self, *, page: int, page_size: int) -> tuple[list[Task], int]: ...

    async def save(self, task: Task) -> Task:
        """Persist all mutable fields of an already-merged Task entity.

        Callers build the full desired state (e.g. via dataclasses.replace)
        before calling this, so the repository never has to guess which
        fields changed.
        """
        ...

    async def delete(self, task_id: UUID) -> None: ...

from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.task import Task
from app.infrastructure.database.models import TaskModel


class SqlAlchemyTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        title: str,
        description: str | None,
        due_date: date | None,
        owner_id: UUID,
        assigned_to: UUID | None,
    ) -> Task:
        model = TaskModel(
            title=title,
            description=description,
            due_date=due_date,
            owner_id=owner_id,
            assigned_to=assigned_to,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_id(self, task_id: UUID) -> Task | None:
        result = await self._session.execute(select(TaskModel).where(TaskModel.id == task_id))
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_paginated(self, *, page: int, page_size: int) -> tuple[list[Task], int]:
        total = await self._session.scalar(select(func.count()).select_from(TaskModel))
        offset = (page - 1) * page_size
        result = await self._session.execute(
            select(TaskModel).order_by(TaskModel.created_at.desc()).offset(offset).limit(page_size)
        )
        models = result.scalars().all()
        return [_to_entity(model) for model in models], total or 0

    async def save(self, task: Task) -> Task:
        model = await self._session.get(TaskModel, task.id)
        if model is None:
            raise ValueError(f"Task {task.id} does not exist")

        model.title = task.title
        model.description = task.description
        model.status = task.status
        model.due_date = task.due_date
        model.completed_at = task.completed_at
        model.assigned_to = task.assigned_to

        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, task_id: UUID) -> None:
        model = await self._session.get(TaskModel, task_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.commit()


def _to_entity(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        title=model.title,
        description=model.description,
        status=model.status,
        due_date=model.due_date,
        completed_at=model.completed_at,
        owner_id=model.owner_id,
        assigned_to=model.assigned_to,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )

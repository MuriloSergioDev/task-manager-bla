from datetime import date
from uuid import UUID

from app.domain.entities.task import Task
from app.domain.entities.user import User
from tests.fixtures.factories import build_task, build_user


class FakeTaskRepository:
    def __init__(self, *, tasks: list[Task] | None = None) -> None:
        self._tasks: dict[UUID, Task] = {task.id: task for task in (tasks or [])}
        self.deleted_ids: list[UUID] = []

    async def create(
        self,
        *,
        title: str,
        description: str | None,
        due_date: date | None,
        owner_id: UUID,
        assigned_to: UUID | None,
    ) -> Task:
        task = build_task(
            title=title,
            description=description,
            due_date=due_date,
            owner_id=owner_id,
            assigned_to=assigned_to,
        )
        self._tasks[task.id] = task
        return task

    async def get_by_id(self, task_id: UUID) -> Task | None:
        return self._tasks.get(task_id)

    async def list_paginated(self, *, page: int, page_size: int) -> tuple[list[Task], int]:
        all_tasks = sorted(self._tasks.values(), key=lambda task: task.created_at, reverse=True)
        total = len(all_tasks)
        start = (page - 1) * page_size
        return all_tasks[start : start + page_size], total

    async def save(self, task: Task) -> Task:
        self._tasks[task.id] = task
        return task

    async def delete(self, task_id: UUID) -> None:
        self._tasks.pop(task_id, None)
        self.deleted_ids.append(task_id)


class FakeUserRepository:
    def __init__(self, *, users: list[User] | None = None) -> None:
        self._users: dict[UUID, User] = {user.id: user for user in (users or [])}
        self._users_by_email: dict[str, User] = {user.email: user for user in (users or [])}

    async def get_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._users.get(user_id)

    async def create(self, *, email: str, password_hash: str) -> User:
        user = build_user(email=email, password_hash=password_hash)
        self._users[user.id] = user
        self._users_by_email[email] = user
        return user

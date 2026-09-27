from dataclasses import dataclass, replace
from typing import Any
from uuid import UUID

from app.application.schemas.task_schemas import TaskUpdate
from app.application.use_cases.tasks.task_lookup import get_visible_task
from app.domain.entities.task import Task, TaskStatus
from app.domain.entities.user import User
from app.domain.exceptions import (
    AssigneeNotFoundError,
    InvalidStatusChangeError,
    TaskAuthorizationError,
)
from app.domain.repositories.task_repository import TaskRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.authorization_service import TaskAuthorizationService


@dataclass
class UpdateTaskUseCase:
    task_repository: TaskRepository
    user_repository: UserRepository

    async def execute(self, *, task_id: UUID, current_user: User, changes: TaskUpdate) -> Task:
        task = await get_visible_task(self.task_repository, task_id, current_user)

        if not TaskAuthorizationService.can_edit(current_user, task):
            raise TaskAuthorizationError("Only the task owner or assignee can update this task")

        # Only the fields the client actually sent: PATCH leaves the rest alone,
        # and an explicit null (where the schema allows one) clears a field.
        updates: dict[str, Any] = changes.model_dump(exclude_unset=True)

        # can_edit now covers the assignee too, but reassigning to someone
        # else is a separate, owner-only decision (matches the dedicated
        # POST .../assign endpoint) -- checked explicitly rather than
        # letting the broader can_edit implicitly grant it.
        if "assigned_to" in updates and not TaskAuthorizationService.can_assign(current_user, task):
            raise TaskAuthorizationError("Only the task owner can reassign this task")

        if "assigned_to" in updates and updates["assigned_to"] is not None:
            new_assignee = updates["assigned_to"]
            if await self.user_repository.get_by_id(new_assignee) is None:
                raise AssigneeNotFoundError(str(new_assignee))

        # Completing goes through CompleteTaskUseCase only: it stamps
        # completed_at and dispatches the activity event, and a status
        # change here would silently do neither. Restating COMPLETED on a
        # task that's already done is harmless, so that's allowed.
        if updates.get("status") == TaskStatus.COMPLETED and task.status != TaskStatus.COMPLETED:
            raise InvalidStatusChangeError("Use the complete action to complete a task")

        # completed_at must only ever be set while status is actually
        # COMPLETED -- moving away from it (e.g. reopening a task) has to
        # clear the stamp, or it'd misrepresent when the task was last done.
        if (
            "status" in updates
            and updates["status"] != TaskStatus.COMPLETED
            and task.status == TaskStatus.COMPLETED
        ):
            updates["completed_at"] = None

        updated_task = replace(task, **updates)
        return await self.task_repository.save(updated_task)

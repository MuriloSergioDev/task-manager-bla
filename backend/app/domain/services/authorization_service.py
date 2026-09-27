from app.domain.entities.task import Task
from app.domain.entities.user import User


class TaskAuthorizationService:
    """Tasks are private to the people involved: only the owner or assignee
    can see a task or work it (edit/delete/complete). Only the owner can hand
    it to someone else (assign) -- reassignment is a record-level decision,
    not part of doing the work."""

    @staticmethod
    def can_view(user: User, task: Task) -> bool:
        return task.owner_id == user.id or task.assigned_to == user.id

    @staticmethod
    def can_edit(user: User, task: Task) -> bool:
        return task.owner_id == user.id or task.assigned_to == user.id

    @staticmethod
    def can_delete(user: User, task: Task) -> bool:
        return task.owner_id == user.id or task.assigned_to == user.id

    @staticmethod
    def can_assign(user: User, task: Task) -> bool:
        return task.owner_id == user.id

    @staticmethod
    def can_complete(user: User, task: Task) -> bool:
        return task.owner_id == user.id or task.assigned_to == user.id

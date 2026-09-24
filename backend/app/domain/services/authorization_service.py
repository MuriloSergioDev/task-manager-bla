from app.domain.entities.task import Task
from app.domain.entities.user import User


class TaskAuthorizationService:
    """Owner controls the record; the current assignee may only complete it."""

    @staticmethod
    def can_view(user: User, task: Task) -> bool:
        return True

    @staticmethod
    def can_edit(user: User, task: Task) -> bool:
        return task.owner_id == user.id

    @staticmethod
    def can_delete(user: User, task: Task) -> bool:
        return task.owner_id == user.id

    @staticmethod
    def can_assign(user: User, task: Task) -> bool:
        return task.owner_id == user.id

    @staticmethod
    def can_complete(user: User, task: Task) -> bool:
        return task.owner_id == user.id or task.assigned_to == user.id

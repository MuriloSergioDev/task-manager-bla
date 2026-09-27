from uuid import UUID

from app.domain.entities.task import Task
from app.domain.entities.user import User
from app.domain.exceptions import TaskNotFoundError
from app.domain.repositories.task_repository import TaskRepository
from app.domain.services.authorization_service import TaskAuthorizationService


async def get_visible_task(task_repository: TaskRepository, task_id: UUID, user: User) -> Task:
    """Load a task the user is allowed to see, or raise TaskNotFoundError.

    A task the user can't view is reported exactly like a missing one (404,
    not 403) so that task ids can't be probed to learn which tasks exist.
    Every single-task use case goes through here, so the visibility rule
    can't be skipped by one of them.
    """
    task = await task_repository.get_by_id(task_id)
    if task is None or not TaskAuthorizationService.can_view(user, task):
        raise TaskNotFoundError(str(task_id))
    return task

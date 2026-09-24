from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.schemas.task_schemas import (
    AssignTaskRequest,
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from app.application.use_cases.tasks.assign_task import AssignTaskUseCase
from app.application.use_cases.tasks.complete_task import CompleteTaskUseCase
from app.application.use_cases.tasks.create_task import CreateTaskUseCase
from app.application.use_cases.tasks.delete_task import DeleteTaskUseCase
from app.application.use_cases.tasks.get_task import GetTaskUseCase
from app.application.use_cases.tasks.list_tasks import ListTasksUseCase
from app.application.use_cases.tasks.update_task import UpdateTaskUseCase
from app.core.dependencies import get_task_repository, get_user_repository
from app.domain.entities.user import User
from app.domain.exceptions import AssigneeNotFoundError, TaskAuthorizationError, TaskNotFoundError
from app.domain.repositories.task_repository import TaskFilters, TaskRepository
from app.domain.repositories.user_repository import UserRepository
from app.presentation.api.dependencies.auth import get_current_user
from app.presentation.api.dependencies.pagination import PaginationParams, pagination_params
from app.presentation.api.dependencies.task_filters import task_filters

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(pagination_params)],
    filters: Annotated[TaskFilters, Depends(task_filters)],
    task_repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> TaskListResponse:
    use_case = ListTasksUseCase(task_repository=task_repository)
    items, total = await use_case.execute(
        page=pagination.page, page_size=pagination.page_size, filters=filters
    )
    pages = ceil(total / pagination.page_size) if total else 0
    return TaskListResponse(
        items=[TaskResponse.model_validate(task) for task in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
        pages=pages,
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    task_repository: Annotated[TaskRepository, Depends(get_task_repository)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> TaskResponse:
    use_case = CreateTaskUseCase(task_repository=task_repository, user_repository=user_repository)
    try:
        task = await use_case.execute(
            owner_id=current_user.id,
            title=payload.title,
            description=payload.description,
            due_date=payload.due_date,
            assigned_to=payload.assigned_to,
        )
    except AssigneeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="assigned_to user does not exist",
        ) from exc

    return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    task_repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> TaskResponse:
    use_case = GetTaskUseCase(task_repository=task_repository)
    try:
        task = await use_case.execute(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc

    return TaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    task_repository: Annotated[TaskRepository, Depends(get_task_repository)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> TaskResponse:
    use_case = UpdateTaskUseCase(task_repository=task_repository, user_repository=user_repository)
    updates = payload.model_dump(exclude_unset=True)
    try:
        task = await use_case.execute(task_id=task_id, current_user=current_user, updates=updates)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
    except TaskAuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except AssigneeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="assigned_to user does not exist",
        ) from exc

    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    task_repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> None:
    use_case = DeleteTaskUseCase(task_repository=task_repository)
    try:
        await use_case.execute(task_id=task_id, current_user=current_user)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
    except TaskAuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    task_repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> TaskResponse:
    use_case = CompleteTaskUseCase(task_repository=task_repository)
    try:
        task = await use_case.execute(task_id=task_id, current_user=current_user)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
    except TaskAuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return TaskResponse.model_validate(task)


@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: UUID,
    payload: AssignTaskRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    task_repository: Annotated[TaskRepository, Depends(get_task_repository)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> TaskResponse:
    use_case = AssignTaskUseCase(task_repository=task_repository, user_repository=user_repository)
    try:
        task = await use_case.execute(
            task_id=task_id, current_user=current_user, assigned_to=payload.assigned_to
        )
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
    except TaskAuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except AssigneeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="assigned_to user does not exist",
        ) from exc

    return TaskResponse.model_validate(task)

from datetime import date
from typing import Annotated

from fastapi import HTTPException, Query, status

from app.domain.entities.task import TaskStatus
from app.domain.repositories.task_repository import TaskFilters


def task_filters(
    status_filter: Annotated[TaskStatus | None, Query(alias="status")] = None,
    due_date: Annotated[date | None, Query()] = None,
    due_date_from: Annotated[date | None, Query()] = None,
    due_date_to: Annotated[date | None, Query()] = None,
) -> TaskFilters:
    if due_date_from is not None and due_date_to is not None and due_date_from > due_date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="due_date_from must be before or equal to due_date_to",
        )

    return TaskFilters(
        status=status_filter,
        due_date=due_date,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
    )

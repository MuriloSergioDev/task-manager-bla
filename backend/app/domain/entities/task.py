from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True, slots=True)
class Task:
    id: UUID
    title: str
    description: str | None
    status: TaskStatus
    due_date: date | None
    completed_at: datetime | None
    owner_id: UUID
    assigned_to: UUID | None
    created_at: datetime
    updated_at: datetime

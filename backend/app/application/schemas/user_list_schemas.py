from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserDirectoryEntry(BaseModel):
    """What any signed-in user may learn about another: enough to pick an
    assignee, nothing about the account's state."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str


class UserListResponse(BaseModel):
    items: list[UserDirectoryEntry]

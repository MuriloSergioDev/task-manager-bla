from pydantic import BaseModel

from app.application.schemas.user_schemas import UserResponse


class UserListResponse(BaseModel):
    items: list[UserResponse]

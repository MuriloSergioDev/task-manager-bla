from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.schemas.user_list_schemas import UserDirectoryEntry, UserListResponse
from app.application.use_cases.users.list_users import ListUsersUseCase
from app.core.dependencies import get_user_repository
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.presentation.api.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: Annotated[User, Depends(get_current_user)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserListResponse:
    use_case = ListUsersUseCase(user_repository=user_repository)
    users = await use_case.execute()
    return UserListResponse(items=[UserDirectoryEntry.model_validate(user) for user in users])

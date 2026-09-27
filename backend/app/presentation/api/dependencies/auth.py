from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status

from app.core.cookies import ACCESS_TOKEN_COOKIE_NAME
from app.core.dependencies import get_token_service, get_user_repository
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.token_service import InvalidTokenError, TokenService


async def get_current_user(
    token_service: Annotated[TokenService, Depends(get_token_service)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    access_token: Annotated[str | None, Cookie(alias=ACCESS_TOKEN_COOKIE_NAME)] = None,
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    if access_token is None:
        raise unauthorized

    try:
        user_id = token_service.decode_access_token(access_token)
    except InvalidTokenError as exc:
        raise unauthorized from exc

    user = await user_repository.get_by_id(user_id)
    if user is None or not user.is_active:
        raise unauthorized

    return user

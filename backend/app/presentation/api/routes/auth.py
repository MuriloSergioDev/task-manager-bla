from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.schemas.auth_schemas import LoginRequest, RegisterRequest, TokenResponse
from app.application.schemas.user_schemas import UserResponse
from app.application.use_cases.auth.login_user import InvalidCredentialsError, LoginUserUseCase
from app.application.use_cases.auth.register_user import (
    EmailAlreadyRegisteredError,
    RegisterUserUseCase,
)
from app.core.dependencies import get_password_hasher, get_token_service, get_user_repository
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_hasher import PasswordHasher
from app.domain.services.token_service import TokenService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
) -> UserResponse:
    use_case = RegisterUserUseCase(user_repository=user_repository, password_hasher=password_hasher)
    try:
        user = await use_case.execute(email=payload.email, password=payload.password)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered"
        ) from exc

    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> TokenResponse:
    use_case = LoginUserUseCase(
        user_repository=user_repository,
        password_hasher=password_hasher,
        token_service=token_service,
    )
    try:
        access_token, expires_in = await use_case.execute(
            email=payload.email, password=payload.password
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        ) from exc

    return TokenResponse(access_token=access_token, expires_in=expires_in)

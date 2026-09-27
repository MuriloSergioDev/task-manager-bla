from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.application.schemas.auth_schemas import LoginRequest, RegisterRequest
from app.application.schemas.user_schemas import UserResponse
from app.application.use_cases.auth.login_user import InvalidCredentialsError, LoginUserUseCase
from app.application.use_cases.auth.register_user import (
    EmailAlreadyRegisteredError,
    RegisterUserUseCase,
)
from app.core.config import Settings, get_settings
from app.core.cookies import clear_access_token_cookie, set_access_token_cookie
from app.core.dependencies import get_password_hasher, get_token_service, get_user_repository
from app.core.rate_limit import limiter
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_hasher import PasswordHasher
from app.domain.services.token_service import TokenService
from app.presentation.api.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Login/register are unauthenticated and credential-adjacent, so they get a
# stricter limit than the app-wide default to slow brute-force/mass-signup
# attempts.
AUTH_RATE_LIMIT = "5/minute"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_RATE_LIMIT)
async def register(
    request: Request,
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


@router.post("/login", response_model=UserResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserResponse:
    use_case = LoginUserUseCase(
        user_repository=user_repository,
        password_hasher=password_hasher,
        token_service=token_service,
    )
    try:
        user, access_token, expires_in = await use_case.execute(
            email=payload.email, password=payload.password
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        ) from exc

    # The token lives only in an httpOnly cookie -- never in the JSON body --
    # so it's inaccessible to JS on the frontend origin even under XSS.
    set_access_token_cookie(
        response, token=access_token, max_age_seconds=expires_in, secure=settings.cookie_secure
    )
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response, settings: Annotated[Settings, Depends(get_settings)]) -> None:
    clear_access_token_cookie(response, secure=settings.cookie_secure)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(current_user)

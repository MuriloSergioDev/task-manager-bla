from dataclasses import dataclass

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_hasher import PasswordHasher
from app.domain.services.token_service import TokenService


class InvalidCredentialsError(Exception):
    pass


@dataclass
class LoginUserUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher
    token_service: TokenService

    async def execute(self, *, email: str, password: str) -> tuple[User, str, int]:
        user = await self.user_repository.get_by_email(email)
        if user is None or not user.is_active:
            raise InvalidCredentialsError

        if not self.password_hasher.verify(password, user.password_hash):
            raise InvalidCredentialsError

        access_token, expires_in = self.token_service.create_access_token(
            user_id=user.id, email=user.email
        )
        return user, access_token, expires_in

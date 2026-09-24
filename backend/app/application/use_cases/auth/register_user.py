from dataclasses import dataclass

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_hasher import PasswordHasher


class EmailAlreadyRegisteredError(Exception):
    pass


@dataclass
class RegisterUserUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher

    async def execute(self, *, email: str, password: str) -> User:
        if await self.user_repository.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError(email)

        password_hash = self.password_hasher.hash(password)
        return await self.user_repository.create(email=email, password_hash=password_hash)

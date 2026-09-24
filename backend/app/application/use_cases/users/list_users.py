from dataclasses import dataclass

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository


@dataclass
class ListUsersUseCase:
    user_repository: UserRepository

    async def execute(self) -> list[User]:
        return await self.user_repository.list_all()

from typing import Protocol
from uuid import UUID


class InvalidTokenError(Exception):
    """Raised when an access token is missing, malformed, expired, or forged."""


class TokenService(Protocol):
    def create_access_token(self, *, user_id: UUID, email: str) -> tuple[str, int]: ...

    def decode_access_token(self, token: str) -> UUID: ...

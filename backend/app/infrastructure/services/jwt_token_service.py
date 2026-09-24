from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.core.config import Settings
from app.domain.services.token_service import InvalidTokenError

_TOKEN_TYPE = "access"


class JwtTokenService:
    def __init__(self, settings: Settings) -> None:
        self._secret_key = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._expire_minutes = settings.access_token_expire_minutes

    def create_access_token(self, *, user_id: UUID, email: str) -> tuple[str, int]:
        now = datetime.now(UTC)
        expires_delta = timedelta(minutes=self._expire_minutes)
        payload = {
            "sub": str(user_id),
            "email": email,
            "iat": now,
            "exp": now + expires_delta,
            "type": _TOKEN_TYPE,
        }
        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        return token, int(expires_delta.total_seconds())

    def decode_access_token(self, token: str) -> UUID:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except jwt.PyJWTError as exc:
            raise InvalidTokenError("Could not validate credentials") from exc

        if payload.get("type") != _TOKEN_TYPE:
            raise InvalidTokenError("Unexpected token type")

        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise InvalidTokenError("Token missing subject")

        try:
            return UUID(subject)
        except ValueError as exc:
            raise InvalidTokenError("Invalid token subject") from exc

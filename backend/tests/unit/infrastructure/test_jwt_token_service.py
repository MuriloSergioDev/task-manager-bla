import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.core.config import Settings
from app.domain.services.token_service import InvalidTokenError
from app.infrastructure.services.jwt_token_service import JwtTokenService


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "database_url": "postgresql+asyncpg://user:pass@localhost/db",
        "jwt_secret_key": "unit-test-secret-at-least-32-bytes-long",
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def test_create_and_decode_access_token_round_trip() -> None:
    service = JwtTokenService(_settings())
    user_id = uuid4()

    token, expires_in = service.create_access_token(user_id=user_id, email="user@example.com")
    decoded_user_id = service.decode_access_token(token)

    assert decoded_user_id == user_id
    assert expires_in == 30 * 60


def test_decode_rejects_token_signed_with_different_secret() -> None:
    service_a = JwtTokenService(_settings(jwt_secret_key="secret-a-padded-to-32-bytes-min!!"))
    service_b = JwtTokenService(_settings(jwt_secret_key="secret-b-padded-to-32-bytes-min!!"))
    token, _ = service_a.create_access_token(user_id=uuid4(), email="user@example.com")

    with pytest.raises(InvalidTokenError):
        service_b.decode_access_token(token)


def test_decode_rejects_expired_token() -> None:
    service = JwtTokenService(_settings(access_token_expire_minutes=0))
    token, _ = service.create_access_token(user_id=uuid4(), email="user@example.com")
    time.sleep(1.1)

    with pytest.raises(InvalidTokenError):
        service.decode_access_token(token)


def test_decode_rejects_malformed_token() -> None:
    service = JwtTokenService(_settings())

    with pytest.raises(InvalidTokenError):
        service.decode_access_token("not-a-real-token")


def _forge_token(secret: str, payload: dict[str, object]) -> str:
    return jwt.encode(payload, secret, algorithm="HS256")


def test_decode_rejects_token_with_wrong_type_claim() -> None:
    settings = _settings()
    now = datetime.now(UTC)
    # A forged token that passes signature verification but claims to be a
    # different token type (e.g. a hypothetical future refresh token) --
    # the type check exists precisely to reject this kind of confusion.
    token = _forge_token(
        settings.jwt_secret_key,
        {
            "sub": str(uuid4()),
            "email": "user@example.com",
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "type": "refresh",
        },
    )

    with pytest.raises(InvalidTokenError):
        JwtTokenService(settings).decode_access_token(token)


def test_decode_rejects_token_missing_subject() -> None:
    settings = _settings()
    now = datetime.now(UTC)
    token = _forge_token(
        settings.jwt_secret_key,
        {
            "email": "user@example.com",
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "type": "access",
        },
    )

    with pytest.raises(InvalidTokenError):
        JwtTokenService(settings).decode_access_token(token)


def test_decode_rejects_token_with_non_uuid_subject() -> None:
    settings = _settings()
    now = datetime.now(UTC)
    token = _forge_token(
        settings.jwt_secret_key,
        {
            "sub": "not-a-uuid",
            "email": "user@example.com",
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "type": "access",
        },
    )

    with pytest.raises(InvalidTokenError):
        JwtTokenService(settings).decode_access_token(token)

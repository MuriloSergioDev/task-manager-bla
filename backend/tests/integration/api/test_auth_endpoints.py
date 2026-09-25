from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import UserModel
from app.infrastructure.services.argon2_password_hasher import Argon2PasswordHasher


async def test_register_creates_user(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "new-user@example.com", "password": "s3cretpass"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new-user@example.com"
    assert body["is_active"] is True
    assert "password" not in body
    assert "password_hash" not in body


async def test_register_rejects_duplicate_email(client: AsyncClient) -> None:
    payload = {"email": "dup@example.com", "password": "s3cretpass"}
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/register", json=payload)

    assert second.status_code == 400


async def test_register_rejects_invalid_payload(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register", json={"email": "not-an-email", "password": "short"}
    )

    assert response.status_code == 422


async def test_login_succeeds_with_correct_credentials(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login-user@example.com", "password": "s3cretpass"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login-user@example.com", "password": "s3cretpass"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]
    assert body["expires_in"] > 0


async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpass@example.com", "password": "s3cretpass"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "bad-password"},
    )

    assert response.status_code == 401


async def test_login_rejects_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"email": "ghost@example.com", "password": "whatever123"}
    )

    assert response.status_code == 401


async def test_login_rejects_malformed_body(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/login", json={"email": "not-an-email"})

    assert response.status_code == 422


async def test_login_rejects_oversized_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "someone@example.com", "password": "x" * 129},
    )

    assert response.status_code == 422


async def test_login_rejects_inactive_user(client: AsyncClient, db_session: AsyncSession) -> None:
    hasher = Argon2PasswordHasher()
    user = UserModel(
        email="inactive@example.com",
        password_hash=hasher.hash("s3cretpass"),
        is_active=False,
    )
    db_session.add(user)
    await db_session.flush()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "s3cretpass"},
    )

    assert response.status_code == 401

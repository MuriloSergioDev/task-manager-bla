from httpx import AsyncClient


async def _register_and_login(client: AsyncClient, email: str, password: str = "s3cretpass") -> str:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token: str = response.json()["access_token"]
    return token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_list_users_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users")

    assert response.status_code == 401


async def test_list_users_returns_all_users_without_password_hash(client: AsyncClient) -> None:
    token = await _register_and_login(client, "users-list-1@example.com")
    await _register_and_login(client, "users-list-2@example.com")

    response = await client.get("/api/v1/users", headers=_auth_headers(token))

    assert response.status_code == 200
    body = response.json()
    emails = {item["email"] for item in body["items"]}
    assert {"users-list-1@example.com", "users-list-2@example.com"} <= emails
    for item in body["items"]:
        assert "password_hash" not in item
        assert "password" not in item

from httpx import AsyncClient


async def test_login_returns_429_after_exceeding_the_limit(client: AsyncClient) -> None:
    payload = {"email": "ratelimit@example.com", "password": "wrong-password"}

    statuses = []
    for _ in range(6):
        response = await client.post("/api/v1/auth/login", json=payload)
        statuses.append(response.status_code)

    assert statuses[-1] == 429
    assert 401 in statuses[:5]


async def test_429_response_uses_the_same_error_shape_as_the_rest_of_the_api(
    client: AsyncClient,
) -> None:
    payload = {"email": "ratelimit-shape@example.com", "password": "wrong-password"}

    for _ in range(5):
        await client.post("/api/v1/auth/login", json=payload)
    response = await client.post("/api/v1/auth/login", json=payload)

    assert response.status_code == 429
    body = response.json()
    # SlowAPI's own default handler uses {"error": ...} -- every other
    # error response in this API (HTTPException, Pydantic validation) uses
    # {"detail": ...}, so this asserts the override is actually wired up.
    assert "detail" in body
    assert "error" not in body
    assert "Rate limit exceeded" in body["detail"]


async def test_register_returns_429_after_exceeding_the_limit(client: AsyncClient) -> None:
    statuses = []
    for i in range(6):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": f"ratelimit-register-{i}@example.com", "password": "s3cretpass"},
        )
        statuses.append(response.status_code)

    assert statuses[-1] == 429
    assert statuses[:5].count(201) == 5


async def test_exceeding_login_limit_does_not_affect_other_endpoints(client: AsyncClient) -> None:
    for _ in range(6):
        await client.post(
            "/api/v1/auth/login", json={"email": "x@example.com", "password": "wrong"}
        )

    response = await client.get("/health")

    assert response.status_code == 200

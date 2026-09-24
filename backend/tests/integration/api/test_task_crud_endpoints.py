from uuid import uuid4

from httpx import AsyncClient


async def _register_and_login(client: AsyncClient, email: str, password: str = "s3cretpass") -> str:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token: str = response.json()["access_token"]
    return token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_create_task_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/api/v1/tasks", json={"title": "No auth"})

    assert response.status_code == 401


async def test_create_and_get_task(client: AsyncClient) -> None:
    token = await _register_and_login(client, "owner@example.com")

    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "Write report", "description": "Q3 numbers"},
        headers=_auth_headers(token),
    )
    assert create_response.status_code == 201
    task = create_response.json()
    assert task["title"] == "Write report"
    assert task["status"] == "TODO"
    assert task["assigned_to"] is None

    get_response = await client.get(f"/api/v1/tasks/{task['id']}", headers=_auth_headers(token))
    assert get_response.status_code == 200
    assert get_response.json()["id"] == task["id"]


async def test_get_nonexistent_task_returns_404(client: AsyncClient) -> None:
    token = await _register_and_login(client, "getter@example.com")

    response = await client.get(f"/api/v1/tasks/{uuid4()}", headers=_auth_headers(token))

    assert response.status_code == 404


async def test_create_task_rejects_invalid_payload(client: AsyncClient) -> None:
    token = await _register_and_login(client, "invalid@example.com")

    response = await client.post("/api/v1/tasks", json={"title": ""}, headers=_auth_headers(token))

    assert response.status_code == 422


async def test_create_task_rejects_unknown_assignee(client: AsyncClient) -> None:
    token = await _register_and_login(client, "assigner@example.com")

    response = await client.post(
        "/api/v1/tasks",
        json={"title": "Assign to ghost", "assigned_to": str(uuid4())},
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


async def test_update_task_rejects_unknown_assignee(client: AsyncClient) -> None:
    token = await _register_and_login(client, "update-assigner@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Needs assignee"}, headers=_auth_headers(token)
    )
    task_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"assigned_to": str(uuid4())},
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


async def test_owner_can_update_task(client: AsyncClient) -> None:
    token = await _register_and_login(client, "updater@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Original"}, headers=_auth_headers(token)
    )
    task_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/tasks/{task_id}", json={"title": "Updated"}, headers=_auth_headers(token)
    )

    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated"


async def test_non_owner_cannot_update_task(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "owner2@example.com")
    stranger_token = await _register_and_login(client, "stranger2@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Protected"}, headers=_auth_headers(owner_token)
    )
    task_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Hijacked"},
        headers=_auth_headers(stranger_token),
    )

    assert response.status_code == 403


async def test_update_nonexistent_task_returns_404(client: AsyncClient) -> None:
    token = await _register_and_login(client, "updater404@example.com")

    response = await client.patch(
        f"/api/v1/tasks/{uuid4()}", json={"title": "x"}, headers=_auth_headers(token)
    )

    assert response.status_code == 404


async def test_owner_can_delete_task(client: AsyncClient) -> None:
    token = await _register_and_login(client, "deleter@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "To delete"}, headers=_auth_headers(token)
    )
    task_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/tasks/{task_id}", headers=_auth_headers(token))
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/tasks/{task_id}", headers=_auth_headers(token))
    assert get_response.status_code == 404


async def test_non_owner_cannot_delete_task(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "owner3@example.com")
    stranger_token = await _register_and_login(client, "stranger3@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Protected"}, headers=_auth_headers(owner_token)
    )
    task_id = create_response.json()["id"]

    response = await client.delete(
        f"/api/v1/tasks/{task_id}", headers=_auth_headers(stranger_token)
    )

    assert response.status_code == 403


async def test_delete_nonexistent_task_returns_404(client: AsyncClient) -> None:
    token = await _register_and_login(client, "deleter404@example.com")

    response = await client.delete(f"/api/v1/tasks/{uuid4()}", headers=_auth_headers(token))

    assert response.status_code == 404


async def test_list_tasks_returns_paginated_envelope(client: AsyncClient) -> None:
    token = await _register_and_login(client, "lister@example.com")
    for i in range(3):
        await client.post(
            "/api/v1/tasks", json={"title": f"Task {i}"}, headers=_auth_headers(token)
        )

    response = await client.get("/api/v1/tasks?page=1&page_size=2", headers=_auth_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"items", "page", "page_size", "total", "pages"}
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["items"]) == 2
    assert body["total"] >= 3


async def test_list_tasks_rejects_page_size_over_cap(client: AsyncClient) -> None:
    token = await _register_and_login(client, "capper@example.com")

    response = await client.get("/api/v1/tasks?page_size=101", headers=_auth_headers(token))

    assert response.status_code == 422


async def test_list_tasks_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/tasks")

    assert response.status_code == 401

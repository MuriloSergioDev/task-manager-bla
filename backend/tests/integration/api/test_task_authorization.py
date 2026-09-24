from uuid import uuid4

from httpx import AsyncClient


async def _register_and_login(client: AsyncClient, email: str, password: str = "s3cretpass") -> str:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token: str = response.json()["access_token"]
    return token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_owner_can_complete_own_task(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "complete-owner@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Finish this"}, headers=_auth_headers(owner_token)
    )
    task_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/complete", headers=_auth_headers(owner_token)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["completed_at"] is not None


async def test_assignee_can_complete_assigned_task(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "complete-owner2@example.com")
    assignee_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "complete-assignee@example.com", "password": "s3cretpass"},
    )
    assignee_id = assignee_response.json()["id"]
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "complete-assignee@example.com", "password": "s3cretpass"},
    )
    assignee_token = login_resp.json()["access_token"]

    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "Do the work", "assigned_to": assignee_id},
        headers=_auth_headers(owner_token),
    )
    task_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/complete", headers=_auth_headers(assignee_token)
    )

    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"


async def test_stranger_cannot_complete_task(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "complete-owner3@example.com")
    stranger_token = await _register_and_login(client, "complete-stranger@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Not yours"}, headers=_auth_headers(owner_token)
    )
    task_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/complete", headers=_auth_headers(stranger_token)
    )

    assert response.status_code == 403


async def test_owner_can_reassign_task(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "assign-owner@example.com")
    assignee_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "assign-target@example.com", "password": "s3cretpass"},
    )
    assignee_id = assignee_response.json()["id"]
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Needs assignee"}, headers=_auth_headers(owner_token)
    )
    task_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/assign",
        json={"assigned_to": assignee_id},
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 200
    assert response.json()["assigned_to"] == assignee_id


async def test_assignee_cannot_reassign_task(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "assign-owner2@example.com")
    assignee_reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "assign-assignee2@example.com", "password": "s3cretpass"},
    )
    assignee_id = assignee_reg.json()["id"]
    assignee_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "assign-assignee2@example.com", "password": "s3cretpass"},
    )
    assignee_token = assignee_login.json()["access_token"]

    other_user_reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "assign-other2@example.com", "password": "s3cretpass"},
    )
    other_user_id = other_user_reg.json()["id"]

    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "Assigned task", "assigned_to": assignee_id},
        headers=_auth_headers(owner_token),
    )
    task_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/assign",
        json={"assigned_to": other_user_id},
        headers=_auth_headers(assignee_token),
    )

    assert response.status_code == 403


async def test_assign_rejects_unknown_assignee(client: AsyncClient) -> None:

    owner_token = await _register_and_login(client, "assign-owner3@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Needs assignee"}, headers=_auth_headers(owner_token)
    )
    task_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/assign",
        json={"assigned_to": str(uuid4())},
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 422


async def test_complete_nonexistent_task_returns_404(client: AsyncClient) -> None:

    token = await _register_and_login(client, "complete-404@example.com")

    response = await client.post(f"/api/v1/tasks/{uuid4()}/complete", headers=_auth_headers(token))

    assert response.status_code == 404


async def test_assign_nonexistent_task_returns_404(client: AsyncClient) -> None:

    token = await _register_and_login(client, "assign-404@example.com")

    response = await client.post(
        f"/api/v1/tasks/{uuid4()}/assign",
        json={"assigned_to": None},
        headers=_auth_headers(token),
    )

    assert response.status_code == 404

from uuid import uuid4

from httpx import AsyncClient


async def _register_and_login(client: AsyncClient, email: str, password: str = "s3cretpass") -> str:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = response.cookies.get("access_token")
    assert token is not None
    return token


def _auth_cookies(token: str) -> dict[str, str]:
    return {"access_token": token}


async def test_create_task_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/api/v1/tasks", json={"title": "No auth"})

    assert response.status_code == 401


async def test_create_and_get_task(client: AsyncClient) -> None:
    token = await _register_and_login(client, "owner@example.com")

    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "Write report", "description": "Q3 numbers"},
        cookies=_auth_cookies(token),
    )
    assert create_response.status_code == 201
    task = create_response.json()
    assert task["title"] == "Write report"
    assert task["status"] == "TODO"
    assert task["assigned_to"] is None

    get_response = await client.get(f"/api/v1/tasks/{task['id']}", cookies=_auth_cookies(token))
    assert get_response.status_code == 200
    assert get_response.json()["id"] == task["id"]


async def test_get_nonexistent_task_returns_404(client: AsyncClient) -> None:
    token = await _register_and_login(client, "getter@example.com")

    response = await client.get(f"/api/v1/tasks/{uuid4()}", cookies=_auth_cookies(token))

    assert response.status_code == 404


async def test_create_task_rejects_invalid_payload(client: AsyncClient) -> None:
    token = await _register_and_login(client, "invalid@example.com")

    response = await client.post("/api/v1/tasks", json={"title": ""}, cookies=_auth_cookies(token))

    assert response.status_code == 422


async def test_create_task_rejects_unknown_assignee(client: AsyncClient) -> None:
    token = await _register_and_login(client, "assigner@example.com")

    response = await client.post(
        "/api/v1/tasks",
        json={"title": "Assign to ghost", "assigned_to": str(uuid4())},
        cookies=_auth_cookies(token),
    )

    assert response.status_code == 422


async def test_update_task_rejects_unknown_assignee(client: AsyncClient) -> None:
    token = await _register_and_login(client, "update-assigner@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Needs assignee"}, cookies=_auth_cookies(token)
    )
    task_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"assigned_to": str(uuid4())},
        cookies=_auth_cookies(token),
    )

    assert response.status_code == 422


async def test_owner_can_update_task(client: AsyncClient) -> None:
    token = await _register_and_login(client, "updater@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Original"}, cookies=_auth_cookies(token)
    )
    task_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/tasks/{task_id}", json={"title": "Updated"}, cookies=_auth_cookies(token)
    )

    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated"


async def test_stranger_updating_task_gets_404(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "owner2@example.com")
    stranger_token = await _register_and_login(client, "stranger2@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Protected"}, cookies=_auth_cookies(owner_token)
    )
    task_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Hijacked"},
        cookies=_auth_cookies(stranger_token),
    )

    assert response.status_code == 404


async def test_assignee_can_update_task(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "assignee-update-owner@example.com")
    assignee_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "assignee-update-assignee@example.com", "password": "s3cretpass"},
    )
    assignee_id = assignee_response.json()["id"]
    assignee_token = await _register_and_login(client, "assignee-update-assignee@example.com")

    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "Assigned work", "assigned_to": assignee_id},
        cookies=_auth_cookies(owner_token),
    )
    task_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Updated by assignee"},
        cookies=_auth_cookies(assignee_token),
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated by assignee"


async def test_assignee_cannot_reassign_task_via_update(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "assignee-reassign-owner@example.com")
    assignee_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "assignee-reassign-assignee@example.com", "password": "s3cretpass"},
    )
    assignee_id = assignee_response.json()["id"]
    assignee_token = await _register_and_login(client, "assignee-reassign-assignee@example.com")

    other_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "assignee-reassign-other@example.com", "password": "s3cretpass"},
    )
    other_id = other_response.json()["id"]

    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "Assigned work", "assigned_to": assignee_id},
        cookies=_auth_cookies(owner_token),
    )
    task_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"assigned_to": other_id},
        cookies=_auth_cookies(assignee_token),
    )

    assert response.status_code == 403


async def test_reverting_completed_task_status_clears_completed_at(client: AsyncClient) -> None:
    token = await _register_and_login(client, "revert-completed@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Will be reverted"}, cookies=_auth_cookies(token)
    )
    task_id = create_response.json()["id"]

    complete_response = await client.post(
        f"/api/v1/tasks/{task_id}/complete", cookies=_auth_cookies(token)
    )
    assert complete_response.json()["completed_at"] is not None

    revert_response = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "TODO"},
        cookies=_auth_cookies(token),
    )

    assert revert_response.status_code == 200
    body = revert_response.json()
    assert body["status"] == "TODO"
    assert body["completed_at"] is None


async def test_update_nonexistent_task_returns_404(client: AsyncClient) -> None:
    token = await _register_and_login(client, "updater404@example.com")

    response = await client.patch(
        f"/api/v1/tasks/{uuid4()}", json={"title": "x"}, cookies=_auth_cookies(token)
    )

    assert response.status_code == 404


async def test_owner_can_delete_task(client: AsyncClient) -> None:
    token = await _register_and_login(client, "deleter@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "To delete"}, cookies=_auth_cookies(token)
    )
    task_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/tasks/{task_id}", cookies=_auth_cookies(token))
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/tasks/{task_id}", cookies=_auth_cookies(token))
    assert get_response.status_code == 404


async def test_stranger_deleting_task_gets_404(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "owner3@example.com")
    stranger_token = await _register_and_login(client, "stranger3@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Protected"}, cookies=_auth_cookies(owner_token)
    )
    task_id = create_response.json()["id"]

    response = await client.delete(
        f"/api/v1/tasks/{task_id}", cookies=_auth_cookies(stranger_token)
    )

    assert response.status_code == 404
    owner_view = await client.get(f"/api/v1/tasks/{task_id}", cookies=_auth_cookies(owner_token))
    assert owner_view.status_code == 200


async def test_assignee_can_delete_task(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "assignee-delete-owner@example.com")
    assignee_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "assignee-delete-assignee@example.com", "password": "s3cretpass"},
    )
    assignee_id = assignee_response.json()["id"]
    assignee_token = await _register_and_login(client, "assignee-delete-assignee@example.com")

    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "Assigned work", "assigned_to": assignee_id},
        cookies=_auth_cookies(owner_token),
    )
    task_id = create_response.json()["id"]

    response = await client.delete(
        f"/api/v1/tasks/{task_id}", cookies=_auth_cookies(assignee_token)
    )

    assert response.status_code == 204


async def test_delete_nonexistent_task_returns_404(client: AsyncClient) -> None:
    token = await _register_and_login(client, "deleter404@example.com")

    response = await client.delete(f"/api/v1/tasks/{uuid4()}", cookies=_auth_cookies(token))

    assert response.status_code == 404


async def test_list_tasks_returns_paginated_envelope(client: AsyncClient) -> None:
    token = await _register_and_login(client, "lister@example.com")
    for i in range(3):
        await client.post(
            "/api/v1/tasks", json={"title": f"Task {i}"}, cookies=_auth_cookies(token)
        )

    response = await client.get("/api/v1/tasks?page=1&page_size=2", cookies=_auth_cookies(token))

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"items", "page", "page_size", "total", "pages"}
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["items"]) == 2
    assert body["total"] >= 3


async def test_list_tasks_rejects_page_size_over_cap(client: AsyncClient) -> None:
    token = await _register_and_login(client, "capper@example.com")

    response = await client.get("/api/v1/tasks?page_size=101", cookies=_auth_cookies(token))

    assert response.status_code == 422


async def test_list_tasks_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/tasks")

    assert response.status_code == 401

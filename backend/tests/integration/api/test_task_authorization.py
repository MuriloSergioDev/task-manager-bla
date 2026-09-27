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


async def test_owner_can_complete_own_task(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "complete-owner@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Finish this"}, cookies=_auth_cookies(owner_token)
    )
    task_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/complete", cookies=_auth_cookies(owner_token)
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
    assignee_token = login_resp.cookies.get("access_token")
    assert assignee_token is not None

    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "Do the work", "assigned_to": assignee_id},
        cookies=_auth_cookies(owner_token),
    )
    task_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/complete", cookies=_auth_cookies(assignee_token)
    )

    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"


async def test_stranger_completing_task_gets_404(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "complete-owner3@example.com")
    stranger_token = await _register_and_login(client, "complete-stranger@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Not yours"}, cookies=_auth_cookies(owner_token)
    )
    task_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/complete", cookies=_auth_cookies(stranger_token)
    )

    assert response.status_code == 404


async def test_owner_can_reassign_task(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "assign-owner@example.com")
    assignee_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "assign-target@example.com", "password": "s3cretpass"},
    )
    assignee_id = assignee_response.json()["id"]
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Needs assignee"}, cookies=_auth_cookies(owner_token)
    )
    task_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/assign",
        json={"assigned_to": assignee_id},
        cookies=_auth_cookies(owner_token),
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
    assignee_token = assignee_login.cookies.get("access_token")
    assert assignee_token is not None

    other_user_reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "assign-other2@example.com", "password": "s3cretpass"},
    )
    other_user_id = other_user_reg.json()["id"]

    create_response = await client.post(
        "/api/v1/tasks",
        json={"title": "Assigned task", "assigned_to": assignee_id},
        cookies=_auth_cookies(owner_token),
    )
    task_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/assign",
        json={"assigned_to": other_user_id},
        cookies=_auth_cookies(assignee_token),
    )

    assert response.status_code == 403


async def test_assign_rejects_unknown_assignee(client: AsyncClient) -> None:

    owner_token = await _register_and_login(client, "assign-owner3@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Needs assignee"}, cookies=_auth_cookies(owner_token)
    )
    task_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/assign",
        json={"assigned_to": str(uuid4())},
        cookies=_auth_cookies(owner_token),
    )

    assert response.status_code == 422


async def test_complete_nonexistent_task_returns_404(client: AsyncClient) -> None:

    token = await _register_and_login(client, "complete-404@example.com")

    response = await client.post(f"/api/v1/tasks/{uuid4()}/complete", cookies=_auth_cookies(token))

    assert response.status_code == 404


async def test_assign_nonexistent_task_returns_404(client: AsyncClient) -> None:

    token = await _register_and_login(client, "assign-404@example.com")

    response = await client.post(
        f"/api/v1/tasks/{uuid4()}/assign",
        json={"assigned_to": None},
        cookies=_auth_cookies(token),
    )

    assert response.status_code == 404


async def test_stranger_cannot_read_task_and_gets_404(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "private-owner@example.com")
    stranger_token = await _register_and_login(client, "private-stranger@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Private"}, cookies=_auth_cookies(owner_token)
    )
    task_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/tasks/{task_id}", cookies=_auth_cookies(stranger_token))

    # Same response as a task that doesn't exist -- no existence leak.
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


async def test_stranger_assigning_task_gets_404(client: AsyncClient) -> None:
    owner_token = await _register_and_login(client, "assign-private-owner@example.com")
    stranger_token = await _register_and_login(client, "assign-private-stranger@example.com")
    create_response = await client.post(
        "/api/v1/tasks", json={"title": "Private"}, cookies=_auth_cookies(owner_token)
    )
    task_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/assign",
        json={"assigned_to": None},
        cookies=_auth_cookies(stranger_token),
    )

    assert response.status_code == 404


async def test_list_only_returns_tasks_owned_or_assigned(client: AsyncClient) -> None:
    alice_token = await _register_and_login(client, "list-alice@example.com")
    bob_response = await client.post(
        "/api/v1/auth/register", json={"email": "list-bob@example.com", "password": "s3cretpass"}
    )
    bob_id = bob_response.json()["id"]
    bob_token = await _register_and_login(client, "list-bob@example.com")
    carol_token = await _register_and_login(client, "list-carol@example.com")

    await client.post(
        "/api/v1/tasks", json={"title": "Alice own"}, cookies=_auth_cookies(alice_token)
    )
    await client.post(
        "/api/v1/tasks",
        json={"title": "Alice for Bob", "assigned_to": bob_id},
        cookies=_auth_cookies(alice_token),
    )
    await client.post("/api/v1/tasks", json={"title": "Bob own"}, cookies=_auth_cookies(bob_token))

    alice_list = (await client.get("/api/v1/tasks", cookies=_auth_cookies(alice_token))).json()
    bob_list = (await client.get("/api/v1/tasks", cookies=_auth_cookies(bob_token))).json()
    carol_list = (await client.get("/api/v1/tasks", cookies=_auth_cookies(carol_token))).json()

    assert {task["title"] for task in alice_list["items"]} == {"Alice own", "Alice for Bob"}
    assert alice_list["total"] == 2
    assert {task["title"] for task in bob_list["items"]} == {"Alice for Bob", "Bob own"}
    assert bob_list["total"] == 2
    assert carol_list["items"] == []
    assert carol_list["total"] == 0
    assert carol_list["pages"] == 0

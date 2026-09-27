from typing import Any

from httpx import AsyncClient


async def _register_and_login(client: AsyncClient, email: str, password: str = "s3cretpass") -> str:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = response.cookies.get("access_token")
    assert token is not None
    return token


def _auth_cookies(token: str) -> dict[str, str]:
    return {"access_token": token}


async def _create_task(
    client: AsyncClient, token: str, *, title: str, due_date: str | None = None
) -> dict[str, Any]:
    payload: dict[str, Any] = {"title": title}
    if due_date is not None:
        payload["due_date"] = due_date
    response = await client.post("/api/v1/tasks", json=payload, cookies=_auth_cookies(token))
    task: dict[str, Any] = response.json()
    return task


async def test_filter_by_status(client: AsyncClient) -> None:
    token = await _register_and_login(client, "filter-status@example.com")
    todo = await _create_task(client, token, title="Still todo")
    in_progress_task = await _create_task(client, token, title="In progress")
    await client.patch(
        f"/api/v1/tasks/{in_progress_task['id']}",
        json={"status": "IN_PROGRESS"},
        cookies=_auth_cookies(token),
    )

    response = await client.get("/api/v1/tasks?status=TODO", cookies=_auth_cookies(token))

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert todo["id"] in ids
    assert in_progress_task["id"] not in ids


async def test_filter_by_exact_due_date(client: AsyncClient) -> None:
    token = await _register_and_login(client, "filter-exact-due@example.com")
    matching = await _create_task(client, token, title="Due on the day", due_date="2026-11-15")
    await _create_task(client, token, title="Due later", due_date="2026-11-20")
    await _create_task(client, token, title="No due date")

    response = await client.get("/api/v1/tasks?due_date=2026-11-15", cookies=_auth_cookies(token))

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == [matching["id"]]


async def test_filter_by_due_date_range(client: AsyncClient) -> None:
    token = await _register_and_login(client, "filter-range@example.com")
    await _create_task(client, token, title="Too early", due_date="2026-08-01")
    in_range_1 = await _create_task(client, token, title="In range 1", due_date="2026-09-10")
    in_range_2 = await _create_task(client, token, title="In range 2", due_date="2026-09-20")
    await _create_task(client, token, title="Too late", due_date="2026-10-15")

    response = await client.get(
        "/api/v1/tasks?due_date_from=2026-09-01&due_date_to=2026-09-30",
        cookies=_auth_cookies(token),
    )

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert ids == {in_range_1["id"], in_range_2["id"]}


async def test_due_date_range_excludes_tasks_without_a_due_date(client: AsyncClient) -> None:
    token = await _register_and_login(client, "filter-range-none@example.com")
    await _create_task(client, token, title="No due date at all")

    response = await client.get(
        "/api/v1/tasks?due_date_from=2026-01-01&due_date_to=2026-12-31",
        cookies=_auth_cookies(token),
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


async def test_combined_status_and_due_date_range_filters(client: AsyncClient) -> None:
    token = await _register_and_login(client, "filter-combined@example.com")
    matching = await _create_task(client, token, title="Todo in range", due_date="2026-09-15")
    wrong_status = await _create_task(
        client, token, title="Completed in range", due_date="2026-09-16"
    )
    await client.post(f"/api/v1/tasks/{wrong_status['id']}/complete", cookies=_auth_cookies(token))
    await _create_task(client, token, title="Todo out of range", due_date="2026-12-01")

    response = await client.get(
        "/api/v1/tasks?status=TODO&due_date_from=2026-09-01&due_date_to=2026-09-30",
        cookies=_auth_cookies(token),
    )

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert ids == {matching["id"]}


async def test_due_date_from_after_due_date_to_is_rejected(client: AsyncClient) -> None:
    token = await _register_and_login(client, "filter-invalid-range@example.com")

    response = await client.get(
        "/api/v1/tasks?due_date_from=2026-09-30&due_date_to=2026-09-01",
        cookies=_auth_cookies(token),
    )

    assert response.status_code == 422


async def test_invalid_status_filter_value_is_rejected(client: AsyncClient) -> None:
    token = await _register_and_login(client, "filter-bad-status@example.com")

    response = await client.get("/api/v1/tasks?status=NOT_A_STATUS", cookies=_auth_cookies(token))

    assert response.status_code == 422


async def test_pagination_beyond_last_page_returns_empty_items(client: AsyncClient) -> None:
    token = await _register_and_login(client, "pagination-beyond@example.com")
    await _create_task(client, token, title="Only task")

    response = await client.get("/api/v1/tasks?page=50&page_size=10", cookies=_auth_cookies(token))

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] >= 1
    assert body["page"] == 50


async def test_pagination_reports_correct_page_count(client: AsyncClient) -> None:
    token = await _register_and_login(client, "pagination-pages@example.com")
    for i in range(5):
        await _create_task(client, token, title=f"Paged task {i}")

    response = await client.get("/api/v1/tasks?page=1&page_size=2", cookies=_auth_cookies(token))

    body = response.json()
    assert body["total"] >= 5
    assert body["pages"] == -(-body["total"] // 2)


async def test_list_tasks_with_no_matches_reports_zero_pages(client: AsyncClient) -> None:
    token = await _register_and_login(client, "pagination-zero@example.com")

    response = await client.get(
        "/api/v1/tasks?status=COMPLETED&due_date=2099-01-01", cookies=_auth_cookies(token)
    )

    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["pages"] == 0

# User Stories

What a user can do in the Task Manager, and the rules each action follows. Every story has acceptance criteria and a **Covered by** line naming the endpoint and the tests that check it, so each behavior can be traced to code.

Test paths are relative to `backend/tests/`. `unit/…` tests use in-memory fakes; `integration/…` tests hit a real Postgres database through the HTTP API or repository.

## Roles

| Role | Who |
|---|---|
| **Visitor** | Not logged in |
| **User** | Any logged-in, active user |
| **Owner** | The user who created a task (`owner_id`) |
| **Assignee** | The user a task is currently assigned to (`assigned_to`) |

A task is visible **only to its Owner and Assignee**. To everyone else it behaves as if it doesn't exist: they get `404`, not `403`. See [README → Design Decisions](../README.md#design-decisions) for the reasoning.

---

## Epic 1 — Account & authentication

### US-1.1 — Register
**The visitor should be able to create an account with an email and password, so that they can start managing tasks.**

- A valid email and a password of 8–128 characters create an active account → `201`, and the response never includes the password or its hash.
- An already-registered email → `400` "Email is already registered".
- A malformed email or too-short password → `422`, with the error shown on the form field.

**Covered by:** `POST /api/v1/auth/register` · `integration/api/test_auth_endpoints.py::test_register_creates_user`, `::test_register_rejects_duplicate_email`, `::test_register_rejects_invalid_payload` · `unit/application/test_register_user_use_case.py`

### US-1.2 — Log in
**The visitor should be able to log in with their email and password, so that they can reach their tasks.**

- Correct credentials → `200`, and the JWT is set as an **HttpOnly cookie** that JavaScript can't read.
- A wrong password, unknown email or inactive account → `401` with the same generic "Invalid email or password", so an attacker can't tell which emails are registered.
- Passwords are verified against an Argon2 hash; plaintext is never stored.

**Covered by:** `POST /api/v1/auth/login` · `integration/api/test_auth_endpoints.py::test_login_succeeds_with_correct_credentials`, `::test_login_rejects_wrong_password`, `::test_login_rejects_unknown_email`, `::test_login_rejects_inactive_user`, `::test_login_rejects_oversized_password` · `unit/application/test_login_user_use_case.py`

### US-1.3 — Stay logged in
**The user should stay logged in across page reloads until their session expires, so that they don't have to sign in again for every visit.**

- On load, the app calls `GET /auth/me` to restore the session.
- A missing, malformed, wrongly-signed or expired token → `401`, and the app sends the user to `/login`.

**Covered by:** `GET /api/v1/auth/me` · `integration/api/test_auth_endpoints.py::test_me_returns_current_user`, `::test_me_requires_authentication` · `unit/infrastructure/test_jwt_token_service.py` (expiry, wrong secret, malformed, wrong claims) · `unit/presentation/test_get_current_user.py`

### US-1.4 — Log out
**The user should be able to log out, so that no one else can use their session on a shared device.**

- The cookie is cleared → `204`; protected pages redirect to `/login` afterwards.

**Covered by:** `POST /api/v1/auth/logout` · `integration/api/test_auth_endpoints.py::test_logout_clears_session`

### US-1.5 — Brute-force protection
**The visitor should be slowed down after repeated login or registration attempts, so that passwords can't be guessed by brute force.**

- More than **5 requests per minute** per IP to `/auth/login` or `/auth/register` → `429`, in the same `{"detail": …}` error format as the rest of the API, and the message is shown on the form.
- Hitting the login limit doesn't block the rest of the API.

**Covered by:** `integration/api/test_rate_limiting.py` (all four tests)

### US-1.6 — Route guards
**The user should always land on the right screen for their session state, so that they never see a page they can't use.**

- A visitor opening the dashboard is redirected to `/login`.
- A logged-in user opening `/login` or `/register` is redirected to the dashboard.

**Covered by:** frontend `ProtectedRoute` / `PublicOnlyRoute`, checked in a headless browser (no automated frontend test suite).

---

## Epic 2 — Managing my tasks

### US-2.1 — Create a task
**The user should be able to create a task with a title and, optionally, a description, due date and assignee, so that they can keep track of work.**

- Title 1–200 characters and description up to 5,000 → `201`; the creator becomes the **Owner** and the status starts as `TODO`.
- A missing or overlong title → `422`, shown on the form field.
- An assignee id that doesn't exist → `422` "assigned_to user does not exist".

**Covered by:** `POST /api/v1/tasks` · `integration/api/test_task_crud_endpoints.py::test_create_and_get_task`, `::test_create_task_rejects_invalid_payload`, `::test_create_task_rejects_unknown_assignee`, `::test_create_task_requires_authentication` · `unit/application/test_create_task_use_case.py`

### US-2.2 — See only my tasks
**The user should see only the tasks they own or are assigned to, so that other people's work stays private.**

- The list contains exactly the tasks where the user is Owner or Assignee; `total` and `pages` count only those.
- Requesting another user's task by id → `404` "Task not found", the same response as for an id that doesn't exist.
- The scope is always applied on the server: the client can't widen it through a query parameter.

**Covered by:** `GET /api/v1/tasks`, `GET /api/v1/tasks/{id}` · `integration/api/test_task_authorization.py::test_list_only_returns_tasks_owned_or_assigned`, `::test_stranger_cannot_read_task_and_gets_404` · `integration/repositories/test_task_repository.py::test_list_paginated_visible_to_matches_owner_or_assignee` · `unit/application/test_get_and_list_tasks_use_cases.py::test_list_tasks_scope_cannot_be_widened_by_caller_filters`, `::test_get_task_hides_other_users_task_as_not_found` · `unit/domain/test_authorization_service.py::test_unrelated_user_cannot_view_or_do_anything_else`

### US-2.3 — View a task
**The Owner or Assignee should be able to view a task's details, so that they know what's due and who's responsible.**

- Shows the title, description, status, due date, assignee and, for completed tasks, when it was completed.
- An unknown id → `404`.

**Covered by:** `GET /api/v1/tasks/{id}` · `integration/api/test_task_crud_endpoints.py::test_create_and_get_task`, `::test_get_nonexistent_task_returns_404` · `unit/application/test_get_and_list_tasks_use_cases.py::test_get_task_returns_task_to_assignee`

### US-2.4 — Edit a task
**The Owner or Assignee should be able to edit a task's title, description, due date and status, so that the task reflects the current state of the work.**

- Status can be set to *To do* or *In progress*. A completed task can be reopened, which clears `completed_at`.
- Anyone else → `404`, and the UI shows no Edit button.

**Covered by:** `PATCH /api/v1/tasks/{id}` · `integration/api/test_task_crud_endpoints.py::test_owner_can_update_task`, `::test_assignee_can_update_task`, `::test_stranger_updating_task_gets_404`, `::test_reverting_completed_task_status_clears_completed_at`, `::test_update_nonexistent_task_returns_404`

### US-2.5 — Delete a task
**The Owner or Assignee should be able to delete a task after confirming, so that finished or mistaken tasks don't clutter the list.**

- The UI asks for confirmation in a dialog first → `204`.
- Anyone else → `404`, and the task is left untouched.

**Covered by:** `DELETE /api/v1/tasks/{id}` · `integration/api/test_task_crud_endpoints.py::test_owner_can_delete_task`, `::test_assignee_can_delete_task`, `::test_stranger_deleting_task_gets_404`, `::test_delete_nonexistent_task_returns_404`

### US-2.6 — Mark a task complete
**The Owner or Assignee should be able to mark a task complete in one click, so that finishing work is quick.**

- Status becomes `COMPLETED` and `completed_at` is set to the current time.
- Anyone else → `404`. An unassigned task can't be completed by someone who isn't its Owner.

**Covered by:** `POST /api/v1/tasks/{id}/complete` · `integration/api/test_task_authorization.py::test_owner_can_complete_own_task`, `::test_assignee_can_complete_assigned_task`, `::test_stranger_completing_task_gets_404`, `::test_complete_nonexistent_task_returns_404` · `unit/domain/test_authorization_service.py::test_stranger_still_cannot_complete_an_unassigned_task`

### US-2.7 — Completion is recorded in the background
**When a user completes a task, the system should record an activity entry without slowing down the response, so that completing stays fast even if activity logging is slow or failing.**

- The completion is saved first; only after the commit is a Celery job enqueued. A rolled-back completion never produces an activity entry.
- The worker writes the activity log entry and retries up to 3 times on transient errors. It doesn't retry if the task was deleted in the meantime.

**Covered by:** `unit/application/test_complete_task_use_case.py::test_completing_a_task_dispatches_activity_event` · `unit/infrastructure/test_celery_activity_dispatcher.py` · `integration/workers/test_celery_dispatch.py`

---

## Epic 3 — Assignment

### US-3.1 — Assign a task
**The Owner should be able to assign a task to another user, chosen from a list, so that the right person can pick up the work.**

- The picker lists all users by email; password hashes are never exposed.
- An assignee id that doesn't exist → `422`.

**Covered by:** `POST /api/v1/tasks/{id}/assign`, `GET /api/v1/users` · `integration/api/test_task_authorization.py::test_owner_can_reassign_task`, `::test_assign_rejects_unknown_assignee` · `integration/api/test_users_endpoints.py`

### US-3.2 — Unassign a task
**The Owner should be able to unassign a task, so that it can go back to the pool when plans change.**

**Covered by:** `unit/application/test_assign_task_use_case.py::test_owner_can_unassign_task` · `unit/application/test_update_task_use_case.py::test_update_allows_clearing_assignee_to_none`

### US-3.3 — Assignees can't hand off work
**The Assignee should not be able to reassign a task to someone else, so that only the Owner decides who is responsible.**

- An Assignee trying to reassign through `/assign` or a `PATCH` of `assigned_to` → `403`. This is `403`, not `404`, because the Assignee can see the task.
- In the UI, non-Owners see the assignee as read-only text instead of a dropdown.
- A user who can't see the task at all → `404`.

**Covered by:** `integration/api/test_task_authorization.py::test_assignee_cannot_reassign_task`, `::test_stranger_assigning_task_gets_404` · `integration/api/test_task_crud_endpoints.py::test_assignee_cannot_reassign_task_via_update` · `unit/application/test_update_task_use_case.py::test_assignee_cannot_reassign_via_update`

### US-3.4 — Deleting a user account
**When a user account is deleted, the tasks it was involved in should be cleaned up in a predictable way, so that no task is left pointing at a missing user.**

- Deleting the **Assignee** keeps the task and leaves it unassigned (`ON DELETE SET NULL`).
- Deleting the **Owner** deletes their tasks (`ON DELETE CASCADE`).

**Covered by:** `integration/repositories/test_task_repository.py::test_deleting_assignee_unassigns_but_keeps_task`, `::test_deleting_owner_cascades_to_their_tasks`

---

## Epic 4 — Finding tasks

### US-4.1 — Filter by status
**The user should be able to show only tasks with a given status, so that they can focus on what's still open.**

- An invalid status value → `422`.

**Covered by:** `integration/api/test_task_filtering_pagination.py::test_filter_by_status`, `::test_invalid_status_filter_value_is_rejected`

### US-4.2 — Filter by due date
**The user should be able to filter by an exact due date or a from/to range, combined with status, so that they can see what's due in a given period.**

- The range is inclusive. Tasks without a due date are left out of any date filter.
- `due_date_from` later than `due_date_to` → `422`.

**Covered by:** `integration/api/test_task_filtering_pagination.py::test_filter_by_exact_due_date`, `::test_filter_by_due_date_range`, `::test_due_date_range_excludes_tasks_without_a_due_date`, `::test_combined_status_and_due_date_range_filters`, `::test_due_date_from_after_due_date_to_is_rejected`

### US-4.3 — Filters survive reloads
**The user should be able to reload, bookmark or share a filtered view, and clear all filters in one click, so that they don't have to set filters up again.**

- Filters and the current page are kept in the URL (`?status=…&due_date_from=…&page=…`).
- **Clear filters** resets all of them at once.

**Covered by:** frontend `taskFilterState.ts`, checked in a headless browser.

### US-4.4 — Paginate
**The user should be able to page through their tasks 20 at a time, so that long lists stay fast and readable.**

- The dashboard shows "Page X of Y · N tasks" with Previous and Next buttons, each disabled at its end of the list.
- Changing any filter goes back to page 1.
- If the current page no longer exists (for example after deleting the last task on the last page), the app moves to the last page that does.
- The API rejects `page` < 1 and `page_size` > 100 with `422`. A page past the end returns an empty `items` list.

**Covered by:** `integration/api/test_task_crud_endpoints.py::test_list_tasks_returns_paginated_envelope`, `::test_list_tasks_rejects_page_size_over_cap` · `integration/api/test_task_filtering_pagination.py::test_pagination_reports_correct_page_count`, `::test_pagination_beyond_last_page_returns_empty_items`, `::test_list_tasks_with_no_matches_reports_zero_pages` · UI checked in a headless browser with 23 tasks (2 pages).

### US-4.5 — Spot overdue work
**The user should see incomplete tasks that are past their due date highlighted, so that late work stands out.**

- Overdue tasks show their due date in red with a warning icon, and screen readers announce "Overdue". Completed tasks show their completion date instead.

**Covered by:** frontend `dueDateStatus.ts` / `TaskListItem.tsx`.

### US-4.6 — Clear loading, empty and error states
**The user should always know whether their tasks are loading, whether there are none, or whether something went wrong, so that they're never left looking at a blank screen.**

- A spinner shows while loading. The previous page stays on screen while the next one loads, so the list doesn't flash.
- The empty state tells apart **"No tasks yet"** (with a *New task* button) and **"No tasks match these filters"**.
- Errors show a readable message and never a stack trace.

**Covered by:** frontend `DashboardPage.tsx`.

---

## Epic 5 — Cross-cutting

### US-5.1 — Works on any screen
**The user should be able to use the app on a phone as well as a desktop, so that they can check tasks on the go.**

- Below the `md` breakpoint, list rows stack into cards and the page never scrolls sideways (checked at 390px wide).

### US-5.2 — Safe errors
**The user should never see internal error details, so that implementation details don't leak to clients.**

- Expected errors (`4xx`) all use the same `{"detail": …}` format. An unexpected exception returns a generic `500 Internal Server Error` with no stack trace or exception message.

### US-5.3 — Fair use
**The API should limit how many requests one client can make, so that a single client can't overload it.**

- Default limit: 100 requests per minute per client. Exceeding it → `429`.
- The mechanism is covered by the auth-limit tests in `integration/api/test_rate_limiting.py`. The 100/minute default itself has no automated test.

---

## Known limitations

- **No automated frontend tests.** Stories marked "checked in a headless browser" were verified with a scripted Playwright run, which isn't part of CI.
- **Completing via PATCH.** `PATCH` with `status: COMPLETED` sets the status but doesn't set `completed_at` or enqueue the activity job; only `POST /tasks/{id}/complete` does both. The UI never sends it, since the edit form doesn't offer *Completed* as a new status, but a direct API caller can. Fixing it means routing that case through the completion use case.

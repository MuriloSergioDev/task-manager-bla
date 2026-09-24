# AI-Assisted Development Log

This project was built end-to-end with **Claude Code** (Anthropic) as the implementation agent, working from the specification in `claude.md` through nine phases (architecture → backend foundation → auth → task management → filtering/pagination → security/infrastructure → frontend → seed/docs → final review). This document records the significant instances where generated output was evaluated, changed, or rejected, rather than accepted uncritically — per the specification's explicit requirement that AI be used as "an engineering assistant rather than an unquestioned code generator."

Each entry follows: prompt/goal → generated approach → accepted/rejected → why → how validated.

---

## 1. Architecture: resolving the ownership/assignment ambiguity

**Prompt/goal:** Produce the Phase 1 architecture proposal — directory structure, DB schema, API endpoints, auth flow, background processing, frontend architecture, testing strategy, Docker architecture — before any code was written.

**Generated approach:** The spec's Authorization section says "users can update/delete tasks according to the application's authorization rules" without defining those rules, while the DB section only lists `assigned_to` (no `owner_id`). A literal reading would let any user with `assigned_to` set delete a task they didn't create, or leave no one able to edit an unassigned task's title.

**Accepted:** A model with both `owner_id` (creator, controls the record) and `assigned_to` (does the work) as independent columns — owner-only edit/delete/reassign, owner-or-assignee complete. This was flagged explicitly as a spec-ambiguity resolution and put to the user via `AskUserQuestion` before implementation, rather than silently picked.

**Rejected:** "any authenticated user can edit/delete any task" (simplest, but doesn't satisfy the spec's "must not manipulate another user's private resources" line — nothing would actually be restricted) and "assignee-only controls the task" (would let reassignment strip the creator of control, which is unusual and would surprise users of a task tracker).

**Why:** The rejected options either violate the explicit spec requirement or produce user-hostile behavior no one asked for. The accepted model is the minimum structure that satisfies the stated constraint without introducing RBAC complexity the spec explicitly warns against.

**Validated:** `tests/unit/domain/test_authorization_service.py`, written test-first (confirmed failing before `TaskAuthorizationService` existed, per the spec's TDD instruction for significant business behavior) — four tests covering owner/assignee/stranger permutations, including a specific check that an unassigned task's `assigned_to = None` is never treated as a wildcard match for "anyone can complete it."

---

## 2. Authentication: no user-existence leakage, access-token-only

**Prompt/goal:** Implement Phase 3 — password hashing, JWT, login/register, `get_current_user`.

**Approach considered and rejected before writing any code:** having `login_user.py` distinguish "no such user" from "wrong password" as two different exception types/messages, since that's the more obvious/naive implementation of a login check.

**Why rejected:** distinguishing them lets an attacker enumerate valid emails by observing which error comes back — a standard credential-enumeration vulnerability. `login_user.py` was written directly with a single `InvalidCredentialsError` covering unknown email, inactive user, and wrong password alike, all surfacing as the same generic "Invalid email or password" / `401`.

**Accepted separately:** Access-token-only auth, no refresh-token flow. The spec's Authentication section mentions only "Access token," never a refresh mechanism.

**Why:** Refresh-token rotation (secure storage, revocation lists, rotation-on-use) is real complexity solving a problem — silent re-auth — that wasn't requested. Adding it would be exactly the "unnecessary abstraction" the spec warns against. On expiry, the frontend simply redirects to `/login`.

**Validated:** `tests/integration/api/test_auth_endpoints.py::test_login_rejects_inactive_user` and `test_login_rejects_wrong_password` both assert the identical `401`/message; `tests/unit/infrastructure/test_jwt_token_service.py` covers expired/malformed/wrong-secret tokens.

---

## 3. Testing: a coverage tool bug that looked like missing tests

**Prompt/goal:** Reach the 80% coverage gate honestly, on real behavior, not padding.

**Generated approach / initial reading:** After Phase 4, `pytest --cov` reported `routes/auth.py` at 78% and `routes/tasks.py` at 64%, with the *success-path* `return` statements and `except` blocks in already-tested endpoints marked "missing" — despite `test_register_creates_user` and `test_login_succeeds_with_correct_credentials` demonstrably exercising exactly those lines (assertions passed).

**Rejected:** Writing more tests to "cover" lines that were already executing correctly. That would have papered over the actual problem and produced tests that didn't verify anything new.

**Why (root cause, not just symptom):** `coverage.py`'s default tracer doesn't follow execution across a greenlet switch (SQLAlchemy's async-to-sync bridge for asyncpg) or into FastAPI's thread-pool-executed sync dependencies — both of which this codebase uses. Lines that ran were invisible to the tracer, not untested.

**Accepted:** `concurrency = ["greenlet", "thread"]` in `[tool.coverage.run]`. Coverage jumped from ~91% to ~97% with zero new test code, confirming the diagnosis.

**Validated:** Re-ran `pytest --cov` before and after the config change and compared the specific line numbers reported as "missing" — they disappeared exactly where `await` calls crossed a greenlet boundary or a sync dependency ran in a worker thread, not randomly.

---

## 4. Error handling: Celery retry semantics, not just a `try/except`

**Prompt/goal:** Implement Phase 6's background task with "error handling" as an explicit deliverable, per the spec.

**Simpler approach considered and rejected before writing any code:** a flat `try/except Exception: logger.error(...)` around the DB write, with no retry — the more obvious implementation of "log and move on."

**Why rejected:** the spec explicitly asks the background task to demonstrate "error handling," and a transient failure (a momentary DB connection blip) shouldn't permanently drop an activity-log event on the first hiccup. Implemented directly using Celery's own retry machinery instead: `self.retry(exc=exc)` (3 attempts, fixed 10s backoff), catching only `MaxRetriesExceededError` to log-and-swallow — so retryable failures actually retry, and only exhausted retries are treated as final.

**Accepted:** this two-layer structure (retry loop, then terminal logging) rather than a flat catch-all.

**Validated:** `tests/integration/workers/test_celery_dispatch.py` exercises the happy path in Celery's eager mode against a real (committed, then explicitly cleaned up) Postgres row. The retry-exhaustion path itself was *not* unit-tested — simulating Celery's internal retry bookkeeping in eager mode is disproportionate effort for this scope, and this gap is stated explicitly rather than silently left, per the instruction not to claim untested behavior works.

---

## 5. Performance/correctness: two bugs the type checker and unit tests couldn't see

**Prompt/goal:** Get the Celery background task actually working end-to-end (Phase 6), then get the frontend actually working in a browser (Phase 7) — not just passing static checks.

### 5a. Backend: asyncpg connections don't survive across event loops

**Generated approach:** `record_task_completed_activity` called `asyncio.run(_record_activity(...))`, reusing the app's module-level pooled `AsyncSessionLocal` (the same one FastAPI's long-lived event loop uses).

**Rejected:** Reusing that pooled engine inside the worker task.

**Why:** `asyncio.run()` creates and tears down a fresh event loop on every call — normal for a Celery worker with no ambient loop of its own. But a connection pool holds onto its asyncpg connections across calls; a connection checked out under one loop is unusable once that loop closes. This didn't fail on the unit tests (which use a fake dispatcher, never touching the real task) — it surfaced the first time the task ran for real, in the eager-mode integration test (`tests/integration/workers/test_celery_dispatch.py`), which itself calls `asyncio.run()` once for setup before the task's own internal `asyncio.run()` reuses the same pool: `RuntimeError: Event loop is closed`. The test file had the identical bug in its own helper functions (also reusing the app's pooled session across separate `asyncio.run()` calls) and needed the same fix.

**Accepted:** A dedicated engine for the worker (and for the test that exercises it directly) using `poolclass=NullPool` — every checkout is a fresh physical connection, so no connection is ever reused across a loop boundary.

**Validated:** The integration test passed after the fix. Then, separately, ran a real Celery worker against real Redis (both locally and via `docker compose up`), completed a task through the live HTTP API, and confirmed the `activity_logs` row via `psql` — end-to-end proof beyond the test, not a substitute for having caught it there first.

### 5b. Frontend: invalid table markup that "worked" until it didn't

**Generated approach:** `TaskRow` returned a Fragment containing both `<tr>` and `<TaskFormModal>` (a fixed-overlay `<div>`), rendered inside `TaskTable`'s `<tbody>`.

**Rejected:** Rendering the modal per-row inside the fragment.

**Why:** A headless-browser pass (Playwright driving a real Chromium instance, not just `tsc`/`vite build`, both of which passed cleanly) surfaced a React hydration console error: a `<div>` is not valid inside `<tbody>`. It happened to render correctly visually because browsers "foster-parent" invalid table content out of the table, but that's undefined-behavior-adjacent, not a fix.

**Accepted:** Lifted the modal and its open/close state out of `TaskRow` into `TaskTable`, rendered once, after `</table>`, driven by a single `editingTask: Task | null` state instead of one boolean per row.

**Validated:** Re-ran the same Playwright script; the console-error array went from one hydration warning to empty, confirmed against both the local Vite dev server and the fully dockerized frontend container.

---

## 6. Security review highlights

- **Password hashing:** Argon2 (`argon2-cffi`), not a rolled-my-own or deprecated scheme.
- **No password hashes in any response:** enforced by `UserResponse` only ever exposing `id`/`email`/`is_active` — verified by an explicit assertion in `test_register_creates_user` and `test_list_users_returns_all_users_without_password_hash`.
- **JWT secret validated at startup**, not defaulted — `Settings` has no fallback value for `JWT_SECRET_KEY`; a missing one fails immediately via Pydantic, not on first request.
- **Assignee existence validated server-side** before assignment (create/update/assign all check the user repository), returning `422` instead of letting a bad UUID hit the database and surface a raw foreign-key-violation `500` with an internal stack trace.
- **Rate limiting** on login/register (5/min) stricter than the general API default (100/min), specifically to slow credential-stuffing/mass-registration — see the README's "Design Decisions" section for the documented multi-instance limitation of SlowAPI's in-memory store.

## 7. Performance review highlights

- **Composite index** `(status, due_date)` added in the *initial* migration (Phase 2), anticipating the combined-filter query Phase 5 would need — avoiding an index added reactively after the query pattern was already live.
- **Pagination is mandatory**, not optional: `GET /tasks` always returns a bounded page (`page_size` capped at 100, `422` if exceeded), never an unbounded table scan.
- **`SELECT COUNT(*)`** for pagination totals runs as a separate, indexable query rather than fetching all matching rows and counting in Python.
- Index-usage verification via `EXPLAIN` was deliberately deferred to the final review phase rather than asserted in a unit test: Postgres correctly prefers a sequential scan over an index scan on the tiny tables integration tests create, so an `EXPLAIN`-based assertion at that data volume would be testing the query planner's good judgment, not a regression.

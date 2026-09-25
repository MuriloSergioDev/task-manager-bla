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

## 6. Final review: a Docker startup race that only a true cold start revealed

**Prompt/goal:** Phase 9's validation pass — run the complete stack from scratch, not just re-use the containers that had been running (and working) across every prior phase.

**Generated approach (Phase 6):** both `api` and `celery-worker` used the same `entrypoint.sh`, which runs `alembic upgrade head` before exec-ing the real process — documented at the time as "harmless... removes ordering assumptions" since Alembic migrations are supposed to be idempotent.

**Why that documented reasoning was wrong:** idempotent refers to the *migrations*, not the bookkeeping Alembic does to track them. Alembic doesn't take a lock around creating its own `alembic_version` table. Every re-use of the stack across Phases 6–8 kept the same Postgres volume (already migrated), so this never ran twice against a truly empty database — until Phase 9 explicitly tore it down (`docker compose down -v`) and brought it back up to validate the from-scratch experience a real new clone would have. Both containers hit the empty database at once and raced on `CREATE TABLE alembic_version`; one lost with `UniqueViolationError`.

**Rejected:** leaving both containers running migrations "for safety" (the original reasoning) once it was clear that reasoning didn't hold.

**Accepted:** only `api` migrates. `celery-worker`'s Compose entry overrides the image's entrypoint to invoke `celery` directly (skipping `entrypoint.sh` entirely) and depends on `api` being **healthy** — via a new healthcheck hitting `/health` — rather than merely started, so migrations are guaranteed complete before the worker starts.

**Validated:** `docker compose down -v` (wipes the volume) → `docker compose up --build` → confirmed via `docker logs` that migrations ran exactly once and every service (api, celery-worker, frontend) started cleanly. Repeated the full smoke-test pass (register/login/CRUD/authorization/filtering/pagination/rate-limiting/Celery) against that genuinely fresh stack rather than assuming the fix generalized from the logs alone. This also surfaced a second, smaller gap: `taskdb_test` (the integration-test database) had been created by hand in an earlier phase and was never scripted — also wiped by `down -v`, also undocumented. Fixed by adding a `postgres-init/01-create-test-db.sh` script (Postgres's own `docker-entrypoint-initdb.d` convention), so a fresh volume creates it automatically.

---

## 7. Error handling, round two: a permanent error retried like a transient one

**Prompt/goal:** Phase 9's live API smoke test — complete a task, then (as owner) delete it, in quick succession, to exercise the authorization + lifecycle paths together.

**What happened:** the async activity-log write for the completion raced against the delete and lost, producing a `ForeignKeyViolationError` (the task no longer existed by the time the worker got to it). The task's error handling (section 4 above) caught this as `Exception` and retried it three times at 10s intervals — 30+ seconds spent, and three rounds of log spam, retrying something that could never succeed, since a deleted row doesn't come back.

**Rejected:** treating every exception in the task as equally retryable, which is what the original `except Exception` did.

**Why:** a foreign-key violation is a permanent condition (the referenced row is gone), not a transient one (a connection blip). Conflating the two means wasting retries — and, at scale, worker capacity — on failures that will never resolve.

**Accepted:** catch `sqlalchemy.exc.IntegrityError` specifically and log-and-return immediately, before the general `except Exception: self.retry(...)` branch that remains for genuinely transient failures.

**Validated:** `tests/integration/workers/test_celery_dispatch.py::test_record_task_completed_activity_does_not_retry_a_missing_task` calls the task directly with a nonexistent task/actor id and asserts it returns in under 5 seconds — a real retry would sleep 10s per Celery's `default_retry_delay`, so a fast return is direct evidence the new branch fired instead of the retry path. Then reproduced the *original* scenario against the live Docker stack (restarted `celery-worker` first to be certain it was running the fixed code, not a process that had been up since before the edit): completed a task via the real HTTP API, deleted it immediately after, and confirmed in `docker logs` that the worker hit the identical `ForeignKeyViolationError`, logged it once, and returned in 0.07s — not the 30+ seconds and three retry log entries the original code would have produced.

---

## 8. UX: a stale token flashing the dashboard before bouncing to login

**Prompt/goal:** Phase 9 review of the frontend's auth handling for edge cases beyond the golden path already verified in Phase 7.

**What was found:** `AuthProvider`'s initial state read `auth_user` from `localStorage` directly, with no check on whether the paired JWT was still valid. A tab left open past token expiry (or reopened after the browser was closed for a while) would render the protected dashboard shell first, only redirecting to `/login` after the first API call came back `401` — a visible flash of a screen that was never actually going to load data.

**Rejected:** leaving it as "the API rejects it anyway" — true for security (no protected data is ever exposed), but the flash is still a real, avoidable UX rough edge, not a security gap.

**Accepted:** decode the stored token's `exp` claim at `AuthProvider` init and treat an expired token as unauthenticated immediately, clearing both the token and the stale user before first render.

**Validated:** a Playwright script seeded `localStorage` with a token whose `exp` was already in the past (plus a stale cached user), navigated to `/dashboard`, and asserted an immediate redirect to `/login` with the token cleared — confirming the fix without needing to wait out a real 30-minute expiry.

---

## 9. API design: the one inconsistent error shape, found by actually triggering it

**Prompt/goal:** Phase 9's live smoke test of rate limiting — not just "does it eventually return 429" (already covered by the automated tests), but actually reading the response body of a live 429.

**What was found:** every other error in this API — `HTTPException`, Pydantic validation failures — returns `{"detail": ...}`. SlowAPI's own default exception handler, wired up back in Phase 6, returns `{"error": "Rate limit exceeded: ..."}` instead. Nobody had actually looked at a live 429 body until this pass; the automated rate-limit tests only ever asserted the status code. Worse, the frontend's `apiClient.ts` error-message extraction only reads `.detail` — a 429 would have silently fallen through to axios's generic "Request failed with status code 429" instead of the actual, more informative message.

**Rejected:** leaving SlowAPI's default handler in place and patching around it in the frontend (e.g., special-casing `.error` there too) — that fixes the symptom in one client while leaving the actual API contract inconsistent for every other consumer (Swagger, a future mobile client, `curl`).

**Accepted:** a small custom handler (`rate_limit_exceeded_handler` in `app/core/rate_limit.py`) that reuses SlowAPI's own header-injection logic but wraps the message in `{"detail": ...}`, matching the rest of the API.

**Validated:** added an integration test asserting the live 429 body has a `detail` key and no `error` key; then, separately, confirmed against the running Docker stack with raw `curl` (not just the test client) that a real rate-limited request now returns the consistent shape.

---

## 10. Security review highlights

- **Password hashing:** Argon2 (`argon2-cffi`), not a rolled-my-own or deprecated scheme.
- **No password hashes in any response:** enforced by `UserResponse` only ever exposing `id`/`email`/`is_active` — verified by an explicit assertion in `test_register_creates_user` and `test_list_users_returns_all_users_without_password_hash`.
- **JWT secret validated at startup**, not defaulted — `Settings` has no fallback value for `JWT_SECRET_KEY`; a missing one fails immediately via Pydantic, not on first request.
- **Assignee existence validated server-side** before assignment (create/update/assign all check the user repository), returning `422` instead of letting a bad UUID hit the database and surface a raw foreign-key-violation `500` with an internal stack trace.
- **Rate limiting** on login/register (5/min) stricter than the general API default (100/min), specifically to slow credential-stuffing/mass-registration — see the README's "Design Decisions" section for the documented multi-instance limitation of SlowAPI's in-memory store.
- **Login's password field had no length bound**, found during the Phase 9 review — `RegisterRequest` bounded password length (8–128) from the start, but `LoginRequest` didn't, leaving an unauthenticated endpoint that runs Argon2 (whose cost scales with input size) exposed to arbitrarily large input. Fixed by bounding it too (`max_length=128`); verified with a 129-character password returning `422` before ever reaching the password hasher.
- **SQL injection:** verified directly, not just asserted — sent `status=TODO'; DROP TABLE tasks; --` as a query parameter against the live API. Rejected at `422` by Pydantic's enum validation before reaching the database (SQLAlchemy's parameterized queries mean this was never actually reachable, but the live check confirms the validation layer that makes it unreachable is actually in front of it).
- **Error responses never leak internals:** verified a malformed UUID path parameter returns a clean Pydantic `422`, not a stack trace; no route in the app installs a custom exception handler that would echo exception details, and the app never runs with debug mode enabled.

## 11. Performance review highlights

- **Composite index** `(status, due_date)` added in the *initial* migration (Phase 2), anticipating the combined-filter query Phase 5 would need — avoiding an index added reactively after the query pattern was already live.
- **Pagination is mandatory**, not optional: `GET /tasks` always returns a bounded page (`page_size` capped at 100, `422` if exceeded), never an unbounded table scan.
- **`SELECT COUNT(*)`** for pagination totals runs as a separate, indexable query rather than fetching all matching rows and counting in Python.
- Index-usage verification via `EXPLAIN` was deliberately deferred to the final review phase rather than asserted in a unit test: Postgres correctly prefers a sequential scan over an index scan on the tiny tables integration tests create, so an `EXPLAIN`-based assertion at that data volume would be testing the query planner's good judgment, not a regression.

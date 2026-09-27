# AI-Assisted Development Log

This project was built end-to-end with **Claude Code** (Anthropic) as the implementation agent, working from [the specification](specification.md) (originally the repository's `CLAUDE.md`) through nine phases (architecture → backend foundation → auth → task management → filtering/pagination → security/infrastructure → frontend → seed/docs → final review). This document records the significant instances where generated output was evaluated, changed, or rejected, rather than accepted uncritically — per the specification's explicit requirement that AI be used as "an engineering assistant rather than an unquestioned code generator."

Each entry follows: prompt/goal → generated approach → accepted/rejected → why → how validated.

---

## 1. Architecture: resolving the ownership/assignment ambiguity

**Prompt/goal:** Produce the Phase 1 architecture proposal — directory structure, DB schema, API endpoints, auth flow, background processing, frontend architecture, testing strategy, Docker architecture — before any code was written.

**Generated approach:** The spec's Authorization section says "users can update/delete tasks according to the application's authorization rules" without defining those rules, while the DB section only lists `assigned_to` (no `owner_id`). A literal reading would let any user with `assigned_to` set delete a task they didn't create, or leave no one able to edit an unassigned task's title.

**Accepted:** A model with both `owner_id` (creator, controls the record) and `assigned_to` (does the work) as independent columns — owner-only edit/delete/reassign, owner-or-assignee complete. This was flagged explicitly as a spec-ambiguity resolution and put to the user via `AskUserQuestion` before implementation, rather than silently picked.

**Rejected:** "any authenticated user can edit/delete any task" (simplest, but doesn't satisfy the spec's "must not manipulate another user's private resources" line — nothing would actually be restricted) and "assignee-only controls the task" (would let reassignment strip the creator of control, which is unusual and would surprise users of a task tracker).

**Why:** The rejected options either violate the explicit spec requirement or produce user-hostile behavior no one asked for. The accepted model is the minimum structure that satisfies the stated constraint without introducing RBAC complexity the spec explicitly warns against.

**Validated:** `tests/unit/domain/test_authorization_service.py`, written test-first (confirmed failing before `TaskAuthorizationService` existed, per the spec's TDD instruction for significant business behavior) — four tests covering owner/assignee/stranger permutations, including a specific check that an unassigned task's `assigned_to = None` is never treated as a wildcard match for "anyone can complete it."

*Later amended:* two changes came later. The assignee may also edit and delete a task, so only reassignment stays owner-only. And viewing became restricted to the owner or assignee (§9c). The README's "Authorization model" has the current rule.

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

*Later superseded:* §9a moved the token into an httpOnly cookie, so there is no client-side token left to go stale. The session is now restored from `GET /auth/me` on load.

---

## 9. API design: the one inconsistent error shape, found by actually triggering it

**Prompt/goal:** Phase 9's live smoke test of rate limiting — not just "does it eventually return 429" (already covered by the automated tests), but actually reading the response body of a live 429.

**What was found:** every other error in this API — `HTTPException`, Pydantic validation failures — returns `{"detail": ...}`. SlowAPI's own default exception handler, wired up back in Phase 6, returns `{"error": "Rate limit exceeded: ..."}` instead. Nobody had actually looked at a live 429 body until this pass; the automated rate-limit tests only ever asserted the status code. Worse, the frontend's `apiClient.ts` error-message extraction only reads `.detail` — a 429 would have silently fallen through to axios's generic "Request failed with status code 429" instead of the actual, more informative message.

**Rejected:** leaving SlowAPI's default handler in place and patching around it in the frontend (e.g., special-casing `.error` there too) — that fixes the symptom in one client while leaving the actual API contract inconsistent for every other consumer (Swagger, a future mobile client, `curl`).

**Accepted:** a small custom handler (`rate_limit_exceeded_handler` in `app/core/rate_limit.py`) that reuses SlowAPI's own header-injection logic but wraps the message in `{"detail": ...}`, matching the rest of the API.

**Validated:** added an integration test asserting the live 429 body has a `detail` key and no `error` key; then, separately, confirmed against the running Docker stack with raw `curl` (not just the test client) that a real rate-limited request now returns the consistent shape.

---

## 9a. Security: moving the access token from `localStorage` to an httpOnly cookie

**Prompt/goal:** a post-launch security follow-up — the access token was in `localStorage`, readable by any JS running on the page, so any successful XSS payload could exfiltrate it. Requested fix: move to an httpOnly cookie.

**What changed:** `POST /api/v1/auth/login` now sets the JWT as a `Set-Cookie` response header (`HttpOnly`, `SameSite=Lax`, `Secure` outside `development`) instead of returning it in the JSON body; `get_current_user` reads it via FastAPI's `Cookie(...)` dependency instead of an `Authorization: Bearer` header. Two new endpoints followed directly from the token no longer being client-readable: `POST /api/v1/auth/logout` (clears the cookie server-side) and `GET /api/v1/auth/me` (lets the frontend ask "who am I" on page load, replacing the old client-side JWT decode). The frontend's `AuthProvider` switched from a synchronous `localStorage` read to a `useQuery(['auth','me'], getCurrentUser)` bootstrap, which meant `ProtectedRoute`/`PublicOnlyRoute` needed a real loading state (previously they could assume auth state was known synchronously on first render).

**Rejected:** a double-submit CSRF token scheme. `SameSite=Lax` already excludes the cookie from cross-site `POST`/`PATCH`/`DELETE`, and CORS was already pinned to an explicit origin allowlist rather than `*` — for this app's scope, that combination covers the realistic attack surface without the extra moving parts (a second cookie, header wiring on every mutating request, server-side comparison). Documented as a deliberate scope call in the README rather than left silent.

**A test-infrastructure snag this surfaced:** the integration tests authenticate as multiple identities (owner/assignee/stranger) against a single `httpx.AsyncClient` within one test, which the old `Authorization` header made trivial (a different header value per request) but a cookie jar can't express the same way (one client, one jar). The fix was httpx's own per-request `cookies=` override — but that emits a `DeprecationWarning` ("set cookies on the client instance instead"), which doesn't actually support "briefly act as a different identity within one test" without a much larger rewrite (a separate `AsyncClient` per identity). Rather than silently ignore all warnings, added one narrowly-scoped `filterwarnings` entry in `pyproject.toml` naming the exact message and explaining why, so a real future warning still surfaces.

**Validated, and a real bug found along the way:** backend — `pytest` (112 passed), `ruff check`, `mypy --strict`, plus a live `curl` cookie-jar walkthrough (login → cookie has `HttpOnly`/`SameSite=lax` → `/me` succeeds with the cookie and 401s without it → `/logout` clears it → `/me` 401s after). Frontend — `tsc -b`, `oxlint`, then a live Playwright pass against the actual Docker stack. The **first** Playwright run failed login with a client-side `TypeError` that looked like a bug in the new code; tracing it down (adding temporary `console.error` logging to the interceptor and to `onSuccess`, neither of which fired) pointed at something stranger than a logic bug — the running frontend container's Vite dev server hadn't picked up any of the session's file edits at all, so the browser was actually exercising the *old* pre-migration bundle (old code calling `decodeJwt(undefined)` against the new backend's response shape, which no longer includes `access_token`). Checking `docker logs` confirmed zero HMR update messages despite many saves — a known failure mode where a Windows-host bind mount doesn't reliably deliver filesystem-change events into the container's watcher. Fixed at the root with `server.watch.usePolling: true` in `vite.config.ts` (verified by editing a component, confirming an `hmr update` log line appeared without a container restart, and seeing the edit reflected in a fresh Playwright page load) rather than just restarting the container and moving on — a restart would have made this one test pass while leaving every future edit during this Docker setup silently stale, which is a worse failure mode than an easily-diagnosed crash.

---

## 9b. Frontend: Kanban board, and a plan's assumption that didn't survive contact with the real library

**Prompt/goal:** replace the task table/list with a drag-and-drop Kanban board (three columns by status), decided via two explicit clarifying questions with the user (board vs. grouped list vs. view toggle; drag-and-drop vs. a "Move to..." menu) before any code was written, then a full planning pass (research agent + a dedicated planning agent) before implementation.

**What changed:** new `@dnd-kit/core` + `@dnd-kit/utilities` dependency (added to both the host and the frontend container's separate `node_modules` volume, then a container restart — the same two-step process learned during the `lucide-react` addition). `TaskTable`/`TaskRow`/`TaskCard`/`StatusSelect`/`TaskStatusControl`/`Pagination` deleted outright rather than left dead, since the board fully replaces them (confirmed via grep before deleting). New `TaskBoard`/`BoardColumn`/`KanbanCard` components, a pure `taskBoard.ts` module (`groupByStatus`, `isValidMove`) kept framework-free and easy to reason about, and a `useTaskPermissions` hook extracting logic that used to be duplicated across the old row/card components. The board fetches once with `page_size=100` and no status filter (backend caps pagination at 100 with no "fetch all" escape hatch — documented as a deliberate limit in the README rather than a backend change), grouping by status client-side.

**Rejected:** full optimistic cache patching (`onMutate`/rollback across every cached tasks query) for the drag interaction. With the filter model simplified down to just due-date filters, there's only ever one active cached tasks query for the board, so the existing `invalidateQueries` on mutation success already refetches almost immediately — a `pendingMoves` map (cleared `onSettled`) covers the one-round-trip visual gap without introducing rollback-race risk in the mutation layer. Also rejected: letting an assignee-only user drag a card between To do and In progress. They never had that right even via the old dropdown (`can_edit` is owner-only); the drag matrix mirrors the existing REST authorization exactly (owner: any move; assignee: only into Completed; completed tasks: never draggable, since un-completing would leave `completed_at` and the dispatched activity-log event stale) rather than inventing new rules for the new interaction.

**A planning assumption that turned out wrong, caught by actually running it:** the implementation plan (written by a planning agent and reviewed before coding started) called for `@dnd-kit/sortable`'s `sortableKeyboardCoordinates` helper to handle arrow-key navigation between columns, reasoning it was "the standard way to get keyboard coordinate math without hand-rolling it." It compiled fine and looked plausible in code review. Live keyboard testing (`Tab` to a card's drag handle → `Space` to pick up → arrow key → `Space` to drop, verified against the real API response, not just visually) showed the pickup worked (`aria-pressed` flipped to `true`) but arrow keys never moved the drag position between columns at all. Digging into `@dnd-kit`'s own type definitions clarified why: that helper is built for reordering *within* a single `SortableContext` list, not jumping between independent `useDroppable` containers — a board's three columns are exactly the case it doesn't handle. Replaced it with a small custom `KeyboardCoordinateGetter` (`boardKeyboardCoordinates.ts`) that ranks the board's droppable columns left-to-right by their live rects and moves the virtual drag position to the next/previous column's center on arrow keys, then removed the now-unused `@dnd-kit/sortable` dependency entirely. Re-verified the same keyboard sequence afterward: correct column highlight during the move, correct status transition on drop, `completed_at` correctly set when dropped on Completed — and separately confirmed dnd-kit's `aria-live` announcement region actually receives text ("... is over the To do column.") rather than assuming the `announcements` prop wiring was sufficient on its own.

**Validated:** `tsc -b` + `oxlint` clean; a live Playwright pass against the real Docker stack covering every branch of the authorization matrix with server-side confirmation, not just visual state — owner dragging To do → In progress → Completed (checked via `GET /tasks/{id}` that `status` and `completed_at` land correctly at each step); an assignee-only user dragging an invalid target (confirmed *no* PATCH request was even sent, via network interception, not just that the UI looked unchanged) and a valid one (confirmed the `/complete` POST fired and `completed_at` was set); the keyboard path end-to-end with API confirmation; a create/edit/delete smoke pass on the new cards; and a 390px mobile viewport check (columns stack to `grid-cols-1`, no horizontal page scroll). Test tasks created for the authorization scenarios were deleted again afterward rather than left in the seeded data.

## 9c. Authorization: writing user stories exposed a client-only privacy rule

**Prompt/goal:** "define user stories for user actions, e.g. 'the user should be able to …'". The stories were derived from what the code actually does, not from the spec, so every acceptance criterion could name the endpoint and test that proves it.

**What that surfaced:** three gaps between the documented behavior and the real behavior. (1) `TaskAuthorizationService.can_view` returned `True` for everyone, and `GET /tasks` had no user scope, yet the board hid other users' tasks with a client-side `isVisibleToUser` filter. The UI *looked* private while any authenticated user could read every task with `curl`. (2) The board fetched one 100-item page, and there was no pagination UI. (3) Because of (1) and (2), totals were counted before the client filter, so they were wrong. None of this was caught by the test suite, which tested each layer's rule faithfully; the layers just disagreed with each other. The question "what exactly should a user be able to see?" is what exposed it.

**Decided with the user** (two explicit questions, not picked silently): visibility is limited to Owner or Assignee and **enforced on the server**, and the Kanban board is replaced by a paginated list.

**Accepted:**
- `ListTasksUseCase` always sets `TaskFilters.visible_to = current_user.id`. The scope lives in the use case, not in a route or query parameter, so no caller can forget it or widen it. A dedicated unit test passes someone else's id and asserts it's overridden.
- One `get_visible_task` helper is used by all five single-task use cases, instead of five copies of "load, then check".
- A task the user can't see returns **404, identical to a nonexistent id**. `403` is kept for "you can see it but can't do this" (an assignee reassigning).

**Rejected:**
- **403 for strangers:** it confirms the task exists, so task ids could be probed.
- **Keeping the client-side filter as well as the server scope:** redundant, and it would hide a future server regression.
- **Per-column "load more" for the board:** offered to the user, who chose a plain list instead.

**Two bugs found by running it, not by type-checking or linting:**
- A headless-browser check found that the edit form's new status `<select>` and the filter bar's both rendered `id="status"`, because `Select` derives its id from `name`. The modal's label pointed at the wrong control. The same issue existed on every row's assignee dropdown (`id="assigned_to"` ×20), which the old board also had. Both now get explicit ids.
- The first version of the seed backlog cycled status and assignee on the same `index % 3`, so every carol task came out COMPLETED and every bob task IN_PROGRESS. A `GROUP BY` over a throwaway seeded database caught it. It now uses `index // 3`, which covers all nine combinations.

**Consciously left as-is:** `PATCH` with `status: COMPLETED` doesn't set `completed_at` or enqueue the activity job; only `POST /complete` does. The UI no longer offers that transition in the edit form, and it's listed as a known limitation in `docs/user-stories.md` rather than fixed quietly beyond the agreed scope.

**Validated:**
- Unit tests were changed or added first and confirmed failing (15 red) before implementation.
- The full backend suite passes (127 tests, 97.75% coverage), with `ruff` and `mypy --strict` clean.
- Live API check as two seeded users: each list contains only their own or assigned tasks with the correct `total`, and a stranger gets `404` on GET, PATCH and DELETE.
- Playwright run against the Docker stack with 23 tasks: 20 + 3 rows over two pages, Next disabled on the last page, a filter change resets to page 1, another user's task never appears, no horizontal overflow at 390px, and no React warnings in the console.

## 9d. Frontend: a visual design pass, and a time-zone bug hiding in "overdue"

**Prompt/goal:** "review and improve the frontend design", run through a design-review skill that asks for a written plan (palette, type, layout) and a check of that plan against generic defaults before any code.

**Review finding:** the UI worked but was the stock template: `blue-600` accents, `gray-50` page, rounded cards with soft shadows, ALL-CAPS column headers, pill badges. Nothing in it was specific to tasks or deadlines.

**Accepted:**
- Design tokens in `index.css` (`@theme`): a sage "paper" with a green-black ink. Colour is kept for meaning only: indigo for in progress and focus, green for done, brick for overdue and destructive actions. The primary button is ink rather than a brand blue.
- A **date stub** (`DateStub.tsx`), a small calendar leaf that leads each row, because due date is what people scan a queue by. It's brick when overdue, inverted when due today, dashed when there's no date, and faded when done. Screen readers get a full sentence ("Overdue, was due Sep 21, 2026").
- Status as a progress glyph (empty ring, half-filled ring, check) instead of three colour pills. The status filter became a segmented control built on native radios, so arrow-key navigation comes free.
- "6 days late" and "Due today" next to the status. Specific action labels ("Create task" / "Save changes" instead of "Save"). Pagination shows "21–35 of 35". Shared `AuthLayout` for login and register (the markup had been duplicated). A real `Textarea` for descriptions.

**Rejected:** a dark mode (no requirement asked for it, and it doubles the visual QA). Also a strikethrough on done titles, which hurts readability; done rows are muted instead.

**Found by looking, not by the compiler:**
- `isOverdue` computed "today" with `new Date().toISOString()`, which is the **UTC** date. West of UTC in the evening, a task due today was already flagged overdue (and the reverse happened east of UTC after midnight). It now uses the local calendar date, and a date-only `due_date` is parsed at local midnight.
- In the first screenshot the edit/delete icons rendered 8px wide. Measuring the element showed why: the icon-only buttons combined `size="sm"` (`px-3`) with an override `px-0`, and which class wins depends on stylesheet order, not on the order in `className`. The fix was an explicit `size="icon"` variant on `Button` rather than a stronger override. The same reasoning produced a `compact` option on `Select` for the in-row assignee picker, instead of fighting `h-10` with `h-8`.

**Validated:** `tsc -b` + `vite build` clean. `oxlint` shows no new warnings; one fast-refresh warning my change introduced was fixed by moving `STATUS_LABELS` to `lib/taskStatus.ts`. Playwright screenshots against the Docker stack at 1360px and 390px covered login (empty and error states), the dashboard, the new-task and delete dialogs, a filtered empty state and the icon measurement. No console errors apart from the expected 401 from the session probe before sign-in.

## 9e. Frontend: turning the tokens into a documented design system

**Prompt/goal:** "add a design system". Planned before coding, with two decisions put to the user: how to document it (a dev-only preview page, **Storybook**, or docs only) and whether to adopt a component library (**stay home-made** on Tailwind, or rebuild on shadcn/Radix). The user chose Storybook and home-made.

**Accepted:**
- `src/styles/tokens.css` as the single source of visual values. Beyond colour, it now defines a named type scale (`text-label`, `text-lead`, `text-title`, `text-display`…), radius by hierarchy (`segment` < `control` < `sheet`), `max-w-auth`, and the modal animations. The 14 kinds of one-off value (`text-[13px]` ×8 and so on) are gone; three layout/selector exceptions remain, each with a comment.
- An `Alert` component. The same error markup had been copied into four places (login, register, task form, confirm dialog), with a fifth near-copy for success.
- `components/ui/index.ts` as the component layer's single entry point, and `Badge.tsx` renamed `StatusBadge.tsx` to match what it exports.
- Storybook 10 (`@storybook/react-vite`) with only two addons: docs and a11y. It has 40 stories and 9 docs pages (Foundations plus one per component group). *Corrected in §9f:* this entry first said 41 stories and 8 docs pages, a count that was never checked against the build. The **Foundations** page imports `tokens.css` as raw text and parses it, so the values and their comments on the page can't drift from the source.

**Rejected:**
- `storybook init`: it adds example stories, extra addons and a Vitest setup, all of which would then need removing. The four packages were installed directly instead.
- `@theme static` to expose every token as a CSS variable for the docs: it would also emit all of Tailwind's default palette into the app's CSS.
- Stories for `Header`, `TaskListItem` and `AssigneeSelect`: they need auth and React Query providers, so mocking those would test wiring rather than design.
- Raising Vite's chunk-size warning for the app: it's raised only in `.storybook/main.ts`. The large chunks there are Storybook's runtime and axe-core, which no end user downloads.

**Found by the tooling, not by review:**
- **Four WCAG contrast failures that were in the app, not just in Storybook.** axe (the a11y addon's engine) flagged `done` at 4.37:1 on `paper` (AA needs 4.5), and `faint` at 2.6–3.0:1 on text that carried real information: the done date stub, the completion date and "Unassigned". The fix was partly a value change and partly a rule. `done` was darkened to `#2a7352` (at least 4.79:1). `faint` can't reach 4.5 without becoming `muted` and losing the hierarchy, so it's now **non-text only** (icons, spinners, disabled states, at least 3:1), and informational text moved to `muted`. The rule is written into the token comments, the Foundations page and `docs/design-system.md`.
- **No `<main>` landmark on the login and register pages**, found by running axe against the live app as well as the stories. `AuthLayout`'s wrapper is now `<main>`.

**Validated:**
- **Pixel-identical refactor.** Before touching anything, Playwright captured 10 screens (login, login errors, dashboard, the new-task and delete dialogs, filtered and empty states) at 1360px and 390px, and these were diffed with `pixelmatch` after the migration. The comparison itself had to be made deterministic first. Two runs of the *unchanged* app differed because of three things: a users-query loading race (the selects were captured while still disabled), a focus-colour transition, and native `<select>` text landing on different sub-pixel positions from run to run. The fixes were waiting for the selects to be enabled, disabling animations, turning off LCD antialiasing and masking the `<select>` boxes.
- With that in place, the token migration, the `Alert` extraction and the barrel imports produced **0 changed pixels on all 10 screens**. Before trusting that, I checked the dev server really was serving the new CSS, since §8 records a stale-bundle failure in this same setup. The later contrast fix changed pixels only where expected: the done rows and one placeholder.
- A Playwright pass over all 49 Storybook entries with axe injected showed no console errors and no violations. axe on the live app came back clean for 6 of the 7 screens it claimed. *Corrected in §9f:* the "register" check had been redirected to `/login` by an app bug, so it audited the login page a second time and never audited registration.
- `tsc -b`, `oxlint` (no new warnings), `vite build` and `storybook build` all pass.

---

## 9f. Pre-evaluation audit: moving the checks into the repo exposed a bug and two of my own false claims

**Prompt/goal:** "Make sure everything is ready to be evaluated... don't leave anything that would relate to bad usage of AI." This was read as an audit for the tells of careless AI use: unverified numbers, stale docs, template leftovers, dead code, suppressed warnings, and checks that exist only in a chat transcript.

**Audit findings, all fixed:**
- **Template leftovers.** `frontend/README.md` was still the stock Vite template, and `public/icons.svg`, `src/assets/vite.svg` and `alembic/README` were unused boilerplate. The README was rewritten and the rest deleted.
- **`strict` was never enabled** in `tsconfig.app.json` or `tsconfig.node.json`. Enabling it produced zero errors, so the code was already strict-clean and only the guarantee was missing. It's now on for app, node and e2e code.
- **Three long-standing lint warnings**, fixed at the cause rather than silenced:
  - `authContext.tsx` exported a hook next to a component, which breaks Fast Refresh. It's now split into `authContext.ts`, `AuthProvider.tsx` and `useAuth.ts`.
  - `RegisterForm` called react-hook-form's `watch()` inside a validator. Validators already receive the form values, so it now uses those.
  - `TaskFormModal` wired `watch`/`setValue` to a custom select by hand. It now uses `Controller`.

  `npm run lint` now runs with `--deny-warnings`, so warnings can't creep back.
- **Stale docs.** The README and a user story still described the pagination text as "Page X of Y · N tasks". A "known limitation" said there were no automated frontend tests, which was no longer true.
- **Claims re-verified, not assumed.**
  - The README's seed figures were checked against a throwaway database (created, migrated, seeded, counted, dropped): 37 tasks, 35 visible to alice, all three statuses, and overdue, undated and unassigned tasks present.
  - Coverage (97.75%), the test count (127) and `ruff format` (108 files clean) were re-run.

**The ad-hoc checks from earlier sessions became real test suites**, using Playwright Test with `@axe-core/playwright` instead of scripts in a scratch directory:
- `frontend/e2e/app/` has smoke flows, route guards and axe on every screen, at desktop and mobile widths.
- `frontend/e2e/storybook/` generates one test per story from the built index.
- `visual.spec.ts` is the before/after pixel-diff workflow.

Rewriting them properly exposed:
- **A real app bug.** A signed-out visitor opening `/register` by URL was bounced to `/login`. The `/auth/me` session probe returns 401 when nobody is signed in, and the API client's global "401 → redirect to /login" handler fired on it. Only the in-app link to the page worked. The fix exempts `/api/v1/auth/*` responses from that redirect (a 401 there just means "not signed in", which the route guards already handle). A regression test (`e2e/app/smoke.spec.ts` › *can open the registration page directly*) and a user-story criterion were added.
- **My own false claim, caused by that bug.** §9e reported "axe on 7 live app screens came back clean". The earlier throwaway script visited `/register`, was silently redirected, and audited the login page again. Registration had never been audited. §9e is corrected in place rather than rewritten.
- **A misreported number of mine.** §9e said 41 stories across 8 docs pages. The generated suite enumerates 40 stories, and there are 9 docs pages. That count had been typed from memory, not read from the build.
- **Test-design mistakes**, fixed in the tests, not the app:
  - Locators matched several elements (the user's email is also in the assignee options, and a task's title is also in the delete dialog's preview).
  - One test expected the header email on mobile, where it is hidden by design.
  - A filter test assumed the dev database held in-progress tasks. It now checks the wiring whatever the data: the request carries `status=IN_PROGRESS`, the server returns only in-progress tasks, and the list renders exactly that many rows.
- **A flaky accessibility result.** In the full run, axe reported a colour-contrast failure in the delete dialog that didn't reproduce on its own. The cause: axe measured text while the dialog was still fading in, at partial opacity. The fix waits for the dialog's animations to finish (`waitForDialog`). The alternatives were forcing reduced motion, which would test different CSS than users get, or loosening the rule.

**Rejected:**
- **Committed visual baselines.** The seed data's due dates are relative to the seed day, and screenshots differ by OS, so a committed baseline would fail for reasons unrelated to the code. The visual suite is an explicit before/after tool instead.
- **Storybook's Vitest addon** for story tests: it adds more configuration, and Playwright was already the browser-test tool.

**Validated:**
- `npm run test:e2e`: 26 passed (13 tests × 2 viewports), after two consecutive clean runs of the previous 24-test version.
- `npm run test:storybook`: 40 passed.
- Visual baseline then compare on unchanged code: 12 of 12 identical.
- `tsc -b` (strict) clean, and `oxlint --deny-warnings` clean.
- Backend: 127 passed, 97.75% coverage, and `ruff`, `ruff format` and `mypy --strict` clean.

---

## 9g. Testing: frontend unit tests, written to fail first, and a bug found by writing them

**Prompt/goal:** "Is there a unit test for the frontend?" There wasn't. All frontend tests ran in a real browser, and two of this project's frontend bugs (the UTC "overdue" check in §9d, the `/register` redirect in §9f) were in plain logic that a unit test would have caught directly. The user approved adding them.

**Accepted:**
- **Vitest** with jsdom, Testing Library and `user-event`. `vitest.config.ts` reuses the app's Vite config, so no second build pipeline is needed. Tests sit next to the code (`src/**/*.test.ts(x)`), with shared factories and a provider-wrapping render helper in `src/test/`.
- **A pinned timezone.** `vitest.config.ts` pins the timezone to `America/Sao_Paulo` (UTC-3, no daylight saving). Date logic can only be wrong about "local versus UTC" in a zone that isn't UTC, so pinning one makes that class of bug testable, and identical on every machine and in CI.
- **59 tests in 7 files**, aimed at the frontend's own logic rather than markup:
  - due-date rules (`dueDateStatus`);
  - URL filter state and the `useTaskFilters` hook;
  - the API client's 401 and error rules;
  - `useTaskPermissions`, checked against the backend's rules;
  - `Pagination`;
  - `RegisterForm` and `TaskFormModal` (validation, exact request payloads, API errors).

**Test-first, and each regression test shown to catch its bug:**
- **The 401 rule.** It lived inside an axios interceptor, where it couldn't be tested. I wrote the tests first against the functions I wanted, `shouldRedirectToLogin` and `toApiError`. They ran red (9 failures, "not a function"), then the interceptor was refactored to call them and they went green.
- **Putting the old bugs back.** Reinstating the old UTC `localToday()` made exactly the two timezone tests fail, with the other 12 passing. Reinstating the old redirect behaviour failed exactly the session-probe test.
- **The form tests.** Disconnecting the `Controller`-wired assignee failed the payload test. Always sending `status` on edit failed the "unchanged fields" test.

  All of these were temporary edits, restored and confirmed with `git diff`.

**Found by writing the tests: a URL could break the dashboard.** `parseTaskFilters` cast `?status=` from the URL without checking it. I reproduced it in the live app before changing anything: `/dashboard?status=DONE` sent `status=DONE` to the API, got a 422 twice (the query retries once), and showed "Tasks couldn't be loaded". The same module already guarded `page` against exactly this, so status and the dates now get the same treatment. `isTaskStatus` (using `Object.hasOwn`, not `in`, which would accept `"toString"`) and a `YYYY-MM-DD` check drop values the API would reject. The two new tests were red before the fix and green after, and the live URL now shows the unfiltered list.

**Rejected:**
- **Jest:** it needs its own transform configuration, whereas Vitest reuses Vite's.
- **`jest-dom` matchers:** plain assertions are enough, and it's one less dependency.
- **MSW for network mocking:** spying on the API module functions tests the same boundary without adding a service-worker layer.
- **A coverage threshold for the whole frontend.** Line coverage is 48.7% overall, but the logic modules are at 90–100%. The uncovered code is presentational components and data-fetching hooks, which the Storybook and e2e suites cover. A blanket threshold would push towards tests of markup.

**Validated:**
- `npm run test:coverage`: 59 passed.
- `tsc -b` (strict, which now includes the test files) and `oxlint --deny-warnings` are clean.
- `npm run test:e2e`: 26 passed after the `apiClient` and `taskFilterState` changes.
- CI's frontend job now runs the unit tests with coverage.

---

## 10. Security review highlights

- **Access token in an httpOnly cookie, not `localStorage`:** see §9a — closes off token theft via XSS; CSRF mitigated via `SameSite=Lax` plus a strict CORS origin allowlist rather than a separate token scheme.
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

---

## 12. Harness: how the repo is set up for AI-assisted work

**Prompt/goal:** "Should we structure skills, subagents and other harness stuff for the project?" The answer was yes, but only where it pays for itself.

**Accepted:**
- **A short `CLAUDE.md`.** The original was the 1,018-line build specification. It's kept word for word as [specification.md](specification.md), with a note explaining its role. There were three reasons to replace it:
  - Its phases were finished, so every session paid context for instructions that no longer applied.
  - It lacked the operational knowledge that had actually caused mistakes: the login rate limit, the dev tools living in the venv rather than the container, the Windows bind mount, cookie-only auth, and the `faint`-is-not-for-text rule.
  - It was named `claude.md` in lowercase, which only loads on case-insensitive filesystems.

  The new file is about 100 lines: a code map, commands, the rules that matter here, those gotchas, and working agreements ("verify before claiming").
- **Two project skills** (`.claude/skills/`), each for a workflow that was repeated and has non-obvious steps:
  - `/validate` runs the whole validation pass in the right order. It includes the lessons above: don't report a step you didn't run, work out whether the app or the test is wrong before changing either, and explain every changed pixel.
  - `/log-ai-decision` keeps this document in its format and holds it to the same honesty rules (real numbers only, include your own mistakes, amend instead of contradicting).
- **CI** (`.github/workflows/ci.yml`), the guardrail that doesn't depend on the agent:
  - backend `ruff`, `ruff format`, `mypy --strict` and pytest with coverage against a Postgres service;
  - frontend lint (warnings fail), strict build, Storybook build and Storybook accessibility;
  - the Playwright e2e suite against a freshly built and seeded `docker compose` stack, set up with the same commands the README gives a new developer.

**Rejected:**
- **Custom subagents.** The built-in review, security-review, explore and plan agents already cover this project's needs, so a custom "reviewer" would repeat them with a narrower prompt.
- **Hooks.** Format-on-edit repeats the linters CI already enforces and slows every edit. A local commit-blocking hook would be invisible to reviewers, whereas CI is visible on every commit.
- **MCP servers.** Nothing in this project needs an external system.

Each of these can be added the day a real need appears. Adding them pre-emptively would be the "unnecessary abstraction" the specification warns against.

**Validated:** every command in `CLAUDE.md` and in the `/validate` skill was run as written during this pass. The results are in §9f.

**Found by CI on its first run: the stack didn't start on Linux or macOS.** The backend and frontend jobs passed, but the e2e job failed before any test ran: `exec: "./entrypoint.sh": permission denied`. Compose bind-mounts `./backend` over the image's `/app`, so the host copy of `entrypoint.sh` replaces the one the Dockerfile marks executable. That copy was committed from Windows with mode `100644`. Docker Desktop on Windows presents bind-mounted files as executable, which is why every local run (and every earlier validation pass) worked. In other words, `docker compose up` on a fresh Linux or macOS clone had never actually been tried. The fix records the executable bit in git (`git update-index --chmod=+x`) for `backend/entrypoint.sh` and `postgres-init/01-create-test-db.sh`. `.gitattributes` already forced LF line endings for `*.sh`, so those weren't a second problem. This is the case for CI running the real stack on a different OS: no amount of local testing on Windows would have found it.

The second run got the stack up and then failed at `npm ci` with `EACCES` on `frontend/node_modules`. Compose's anonymous `node_modules` volume needs a mount point, and Docker had created that directory on the host as root. The e2e job now installs frontend dependencies before starting the stack. The same trap affects a Linux developer who starts the stack before running `npm install` on the host, so the README and `CLAUDE.md` now say to install first.

The third run was green on all three jobs, with the same numbers as the local runs: backend 127 passed at 97.75% coverage, 40 Storybook stories, and 26 e2e tests against a freshly built and seeded stack (37 seeded tasks).

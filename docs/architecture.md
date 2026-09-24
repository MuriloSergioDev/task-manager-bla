# Architecture Proposal (Phase 1)

This document is the Phase 1 deliverable required by `claude.md` before any implementation begins: directory structure, database schema, API endpoint list, authentication flow, background-processing flow, frontend architecture, testing strategy, and Docker architecture. No code has been written yet — this is the design that Phase 2 onward will implement against.

Two points in `claude.md` were ambiguous and have been resolved with the user before writing this document; both are reflected throughout below and are restated in [Recorded Decisions](#recorded-decisions).

---

## 1. Directory Structure

### Backend

```
backend/
├── alembic/
│   ├── versions/
│   │   ├── 0001_create_users_table.py
│   │   ├── 0002_create_tasks_table.py
│   │   └── 0003_create_activity_logs_table.py
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── app/
│   ├── main.py                          # FastAPI app factory, middleware, router mounting, exception handlers
│   ├── core/
│   │   ├── config.py                    # Pydantic Settings: env vars, validated at startup
│   │   ├── security.py                  # password hashing (Argon2), JWT encode/decode helpers
│   │   ├── database.py                  # async engine/session factory, declarative Base
│   │   ├── dependencies.py              # get_db, get_task_repository, get_user_repository, etc.
│   │   ├── exceptions.py                # domain exception -> HTTP mapping (no internal leakage)
│   │   ├── logging.py                   # structured logging setup
│   │   └── rate_limit.py                # SlowAPI limiter instance + key func
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── user.py                  # User entity (framework-independent)
│   │   │   ├── task.py                  # Task entity + TaskStatus enum
│   │   │   └── activity_log.py          # ActivityLog entity
│   │   ├── repositories/                # abstract interfaces (Protocol) — no I/O
│   │   │   ├── user_repository.py
│   │   │   ├── task_repository.py
│   │   │   └── activity_log_repository.py
│   │   └── services/
│   │       ├── password_hasher.py       # Protocol for hashing (impl in infrastructure)
│   │       └── authorization_service.py # can_edit, can_delete, can_complete, can_assign
│   ├── application/
│   │   ├── schemas/                     # Pydantic v2 DTOs — the API boundary
│   │   │   ├── auth_schemas.py          # RegisterRequest, LoginRequest, TokenResponse
│   │   │   ├── task_schemas.py          # TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
│   │   │   └── user_schemas.py          # UserResponse (no password_hash)
│   │   └── use_cases/
│   │       ├── auth/
│   │       │   ├── register_user.py
│   │       │   └── login_user.py
│   │       ├── tasks/
│   │       │   ├── create_task.py
│   │       │   ├── get_task.py
│   │       │   ├── list_tasks.py        # filtering + pagination orchestration
│   │       │   ├── update_task.py
│   │       │   ├── delete_task.py
│   │       │   ├── complete_task.py     # sets status/completed_at, dispatches Celery event
│   │       │   └── assign_task.py
│   │       └── users/
│   │           └── list_users.py         # backs the assignee dropdown
│   ├── infrastructure/
│   │   ├── database/
│   │   │   └── models.py                # SQLAlchemy 2.x ORM models
│   │   ├── repositories/
│   │   │   ├── sqlalchemy_user_repository.py
│   │   │   ├── sqlalchemy_task_repository.py
│   │   │   └── sqlalchemy_activity_log_repository.py
│   │   └── services/
│   │       ├── argon2_password_hasher.py
│   │       └── jwt_token_service.py
│   ├── presentation/
│   │   └── api/
│   │       ├── routes/
│   │       │   ├── health.py            # GET /health
│   │       │   ├── auth.py              # POST /api/v1/auth/register, /login
│   │       │   ├── tasks.py             # /api/v1/tasks*
│   │       │   └── users.py             # GET /api/v1/users
│   │       └── dependencies/
│   │           ├── auth.py              # get_current_user — reused by every protected route
│   │           └── pagination.py        # shared pagination query-param model
│   └── workers/
│       ├── celery_app.py                # Celery app config (broker, backend, task routes)
│       └── tasks.py                     # record_task_completed_activity(...)
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   │   ├── test_authorization_service.py
│   │   │   └── test_task_entity.py
│   │   ├── application/
│   │   │   ├── test_register_user_use_case.py
│   │   │   ├── test_login_use_case.py
│   │   │   ├── test_create_task_use_case.py
│   │   │   ├── test_list_tasks_use_case.py
│   │   │   └── test_complete_task_use_case.py
│   │   └── infrastructure/
│   │       └── test_jwt_token_service.py
│   ├── integration/
│   │   ├── conftest.py                  # real Postgres fixtures, migrated schema, per-test rollback
│   │   ├── repositories/
│   │   │   ├── test_task_repository.py
│   │   │   └── test_user_repository.py
│   │   ├── api/
│   │   │   ├── test_auth_endpoints.py   # register + login
│   │   │   ├── test_task_crud_endpoints.py
│   │   │   ├── test_task_filtering_pagination.py
│   │   │   ├── test_task_authorization.py
│   │   │   ├── test_rate_limiting.py
│   │   │   └── test_health.py
│   │   └── workers/
│   │       └── test_celery_dispatch.py  # eager mode + mocked .delay()
│   ├── fixtures/
│   │   └── factories.py                 # test data builders for User/Task
│   └── conftest.py                      # shared fixtures (app, client, settings override)
├── scripts/
│   └── seed.py                          # idempotent demo data seeding
├── pyproject.toml                       # ruff, mypy, pytest config, deps
├── Dockerfile
├── .env.example
└── entrypoint.sh                        # wait-for-db -> alembic upgrade head -> exec process
```

### Frontend

```
frontend/
├── src/
│   ├── app/
│   │   ├── App.tsx                      # composes providers only, no business logic
│   │   ├── router.tsx                   # route table incl. ProtectedRoute wrapper
│   │   └── providers.tsx                # QueryClientProvider, AuthProvider, etc.
│   ├── components/
│   │   ├── ui/                          # Button, Input, Select, Modal, Badge, Spinner, Pagination
│   │   └── layout/                      # AppShell, Header, ProtectedRoute
│   ├── features/
│   │   ├── auth/
│   │   │   ├── components/LoginForm.tsx
│   │   │   ├── components/RegisterForm.tsx
│   │   │   ├── hooks/useLogin.ts
│   │   │   ├── hooks/useRegister.ts
│   │   │   ├── authContext.tsx          # token/user in memory + localStorage sync
│   │   │   └── authApi.ts
│   │   └── tasks/
│   │       ├── components/
│   │       │   ├── TaskTable.tsx
│   │       │   ├── TaskRow.tsx
│   │       │   ├── TaskFormModal.tsx    # create/edit, RHF-driven
│   │       │   ├── TaskFilters.tsx      # status + due-date filter controls
│   │       │   ├── AssigneeSelect.tsx
│   │       │   └── CompleteTaskButton.tsx
│   │       ├── hooks/
│   │       │   ├── useTasks.ts          # useQuery(['tasks', filters, page])
│   │       │   ├── useCreateTask.ts
│   │       │   ├── useUpdateTask.ts
│   │       │   ├── useDeleteTask.ts
│   │       │   └── useCompleteTask.ts
│   │       ├── tasksApi.ts
│   │       └── taskFilterState.ts       # URL-synced filter/pagination state helpers
│   ├── hooks/
│   │   └── useDebouncedValue.ts
│   ├── lib/
│   │   ├── apiClient.ts                 # axios instance: baseURL, JWT interceptor, 401 handler
│   │   └── queryClient.ts
│   ├── types/
│   │   ├── task.ts                      # Task, TaskStatus, TaskListResponse — mirrors backend schemas
│   │   ├── user.ts
│   │   └── api.ts                       # ApiError shape
│   ├── routes/
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   └── DashboardPage.tsx
│   └── main.tsx
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── Dockerfile
└── .env.example
```

---

## 2. Database Schema

```sql
-- TaskStatus enum (native Postgres enum type: task_status)
--   TODO, IN_PROGRESS, COMPLETED

users
  id             UUID PK DEFAULT gen_random_uuid()
  email          VARCHAR(255) NOT NULL UNIQUE      -- unique index; login/register lookup
  password_hash  VARCHAR(255) NOT NULL              -- never serialized in any response
  is_active      BOOLEAN NOT NULL DEFAULT true
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()

tasks
  id             UUID PK DEFAULT gen_random_uuid()
  title          VARCHAR(200) NOT NULL
  description    TEXT NULL
  status         task_status NOT NULL DEFAULT 'TODO'
  due_date       DATE NULL                          -- date only, no time-of-day (see decisions)
  completed_at   TIMESTAMPTZ NULL                    -- set only when status -> COMPLETED
  owner_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE     -- creator; controls the record
  assigned_to    UUID NULL REFERENCES users(id) ON DELETE SET NULL        -- who's doing the work
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()

activity_logs                                        -- append-only background-job output
  id             UUID PK DEFAULT gen_random_uuid()
  task_id        UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE
  event_type     VARCHAR(50) NOT NULL                -- e.g. 'TASK_COMPLETED'
  actor_user_id  UUID NOT NULL REFERENCES users(id)
  payload        JSONB NULL                          -- e.g. {"previous_status": "IN_PROGRESS"}
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()

-- Indexes
ix_tasks_status          ON tasks(status)
ix_tasks_due_date        ON tasks(due_date)
ix_tasks_assigned_to     ON tasks(assigned_to)
ix_tasks_owner_id        ON tasks(owner_id)
ix_tasks_status_due_date ON tasks(status, due_date)   -- composite, common combined filter
ix_activity_logs_task_id ON activity_logs(task_id)
-- users.email already unique-indexed via the UNIQUE constraint
```

**Ownership vs. assignment.** `owner_id` (creator, who controls the record) is deliberately separate from `assigned_to` (who's doing the work) — see [Recorded Decisions](#recorded-decisions) #1.

**Cascade rationale.** Deleting a user deletes tasks they *own* (`owner_id` CASCADE — no orphaned, unmanaged records) but only unassigns tasks they were merely *assigned to* (`assigned_to` SET NULL — deleting a user shouldn't destroy someone else's task). Activity logs cascade with their task.

---

## 3. API Endpoint List

Base path: `/api/v1`. Everything except `/health`, `/auth/register`, and `/auth/login` requires `Authorization: Bearer <token>`.

| Method | Path | Auth | Request | Response | Status codes |
|---|---|---|---|---|---|
| GET | `/health` | none | — | `{status: "ok"}` | 200 |
| POST | `/auth/register` | none (rate-limited, strict) | `{email, password}` | `UserResponse` | 201, 400, 422, 429 |
| POST | `/auth/login` | none (rate-limited, strict) | `{email, password}` | `{access_token, token_type, expires_in}` | 200, 401, 422, 429 |
| GET | `/users` | required | — | `{items: UserResponse[]}` | 200, 401 |
| GET | `/tasks` | required | query: `status?, due_date?, due_date_from?, due_date_to?, page=1, page_size=20` | `{items: TaskResponse[], page, page_size, total, pages}` | 200, 401, 422 |
| POST | `/tasks` | required | `{title, description?, due_date?, assigned_to?}` | `TaskResponse` | 201, 401, 422 |
| GET | `/tasks/{id}` | required | — | `TaskResponse` | 200, 401, 404 |
| PATCH | `/tasks/{id}` | required, **owner-only** | partial `{title?, description?, due_date?, status?, assigned_to?}` | `TaskResponse` | 200, 401, 403, 404, 422 |
| DELETE | `/tasks/{id}` | required, **owner-only** | — | — | 204, 401, 403, 404 |
| POST | `/tasks/{id}/complete` | required, **owner or assignee** | — | `TaskResponse` | 200, 401, 403, 404 |
| POST | `/tasks/{id}/assign` | required, **owner-only** | `{assigned_to: uuid \| null}` | `TaskResponse` | 200, 401, 403, 404, 422 |

**Register endpoint details.** `POST /auth/register` checks email uniqueness (duplicate → `400`, staying within the status codes `claude.md` enumerates rather than introducing a `409`), hashes the password the same way login-created seed users are hashed, and creates the user as `is_active=true`. It does **not** auto-login — registration and login stay separate use cases (`register_user.py` / `login_user.py`), so the client calls `/auth/login` afterward. It shares the login endpoint's strict rate-limit tier since both are abuse-prone, unauthenticated, credential-adjacent endpoints.

**Why separate `/complete` and `/assign` instead of overloading PATCH.** `PATCH` still accepts `status`/`assigned_to` for flexibility, but dedicated actions exist because `claude.md` calls out "mark completed" and "assign" as first-class actions with distinct authorization (assignee *can* complete but *cannot* reassign) — folding that into one generic PATCH would blur field-level authorization. Frontend action buttons map 1:1 to these endpoints.

---

## 4. Authentication Flow

**Register:**
1. `POST /auth/register {email, password}` → `register_user` use case checks email uniqueness via the user repository (indexed lookup) → `400` if taken.
2. Password hashed via `PasswordHasher.hash()` (Argon2); user row inserted with `is_active=true`.
3. Response: `UserResponse` (`id`, `email`, `is_active` — no hash), `201`.

**Login:**
1. `POST /auth/login {email, password}` → repository looks up user by email.
2. Not found or `is_active=False` → generic `401 Invalid credentials` (no user-existence leakage).
3. `PasswordHasher.verify(plain, user.password_hash)` mismatch → same generic `401`.
4. On success, `JWTTokenService.create_access_token`: claims `sub` (user id), `email`, `iat`, `exp` (now + `ACCESS_TOKEN_EXPIRE_MINUTES`), `type: "access"`; signed HS256 with `JWT_SECRET_KEY`.
5. Response: `{access_token, token_type: "bearer", expires_in}`.

**Subsequent requests:**
1. Client sends `Authorization: Bearer <token>`.
2. `get_current_user` dependency (in `presentation/api/dependencies/auth.py`, reused via `Depends` on every protected route): missing header → `401`; invalid signature/malformed/expired → `401`; user missing or inactive → `401`.
3. Route handlers never inline this logic — they only declare `current_user: User = Depends(get_current_user)`.
4. `403` is reserved for authorization failures on resources that exist and are viewable (e.g., non-owner PATCH/DELETE) — distinct from `401`'s identity failures.

Access-token-only, no refresh flow (see [Recorded Decisions](#recorded-decisions) #3): on expiry, the frontend simply redirects to login.

---

## 5. Background Processing Flow

**Trigger.** The `complete_task` use case (invoked by `POST /tasks/{id}/complete`, and also when `PATCH` sets `status=COMPLETED`) commits the status change synchronously, then dispatches a Celery task — off the request's critical path.

**Entity.** `ActivityLog` — an append-only audit trail, chosen to be self-descriptive and extensible if more event types are ever added, though only `TASK_COMPLETED` is used here (satisfies "at least one meaningful async job").

**Celery task** (`app/workers/tasks.py`):

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=10, acks_late=True)
def record_task_completed_activity(self, task_id: str, actor_user_id: str, previous_status: str) -> None:
    # opens its own short-lived sync DB session — the worker is a separate
    # process and does not share the async request-scoped session
    # inserts an ActivityLog row; retries on transient DB errors
    # logs and swallows the error after retries are exhausted (non-critical op)
```

**Dispatch point.** `complete_task` calls `.delay(...)` **after** the DB commit succeeds — never before, so a rolled-back transaction never produces a phantom activity event.

**Error handling.** Bounded retries (3, fixed backoff) for transient errors; permanent failure is logged, never surfaced to the user or allowed to fail the completion request — this is explicitly a non-critical async operation.

**Testability without a real worker.**
- `CELERY_TASK_ALWAYS_EAGER=True` in test config makes `.delay()` execute synchronously in-process against the test DB — validates end-to-end logic with no running broker/worker.
- A narrower unit test mocks/spies `record_task_completed_activity.delay` to assert the use case dispatches with the right arguments, independent of the task's own implementation.

**Why async (for the README).** Activity logging isn't required for the completion response to succeed and may involve extra I/O; decoupling it avoids adding latency or failure-coupling to the primary user-facing action.

---

## 6. Frontend Architecture

**API client (`lib/apiClient.ts`).** Single axios instance, `baseURL` from `VITE_API_BASE_URL`. Request interceptor attaches `Authorization: Bearer <token>` from `authContext`/localStorage. Response interceptor: on `401`, clears auth state and redirects to `/login`; normalizes errors into a typed `ApiError {status, message, details?}`. All feature `*Api.ts` files (`authApi.ts`, `tasksApi.ts`) import this one instance — no duplicated fetch/axios setup anywhere.

**TanStack Query.**
- `['tasks', filters]` where `filters` is the normalized `{status, dueDateFrom, dueDateTo, page, pageSize}` object — same shape drives caching and refetch-on-filter-change.
- `['users']` for the assignee dropdown (long `staleTime`; near-static demo data).
- Mutations (`useCreateTask`, `useUpdateTask`, `useDeleteTask`, `useCompleteTask`) call `queryClient.invalidateQueries({queryKey: ['tasks']})` on success — broad list invalidation is the simplest correct approach at this scope; optimistic updates are deliberately not added (avoids an unrequested abstraction).
- `useLogin`/`useRegister` store the token via `authContext` on success and navigate accordingly.

**Routing.** `react-router` with a `ProtectedRoute` wrapper checking `authContext.isAuthenticated`; unauthenticated access to `/dashboard` redirects to `/login`; authenticated access to `/login`/`/register` redirects to `/dashboard`. Route table lives in `app/router.tsx`, kept out of `App.tsx` (which only composes providers + `<RouterProvider>`).

**Forms.** React Hook Form + validation for `LoginForm`, `RegisterForm` (email format, password rules), and `TaskFormModal` (title required/max length, valid due date, optional description). Inline field errors; API `400`/`422` responses map to field-level errors where possible, otherwise a form-level banner.

**Dashboard filter/pagination state.** Held in the URL query string (`useSearchParams`) as the single source of truth — shareable/bookmarkable, survives refresh, and feeds directly into the TanStack Query key. `taskFilterState.ts` parses/serializes `{status, dueDateFrom, dueDateTo, page}` to/from `URLSearchParams` with defaults, avoiding parallel React state that could drift from the URL.

---

## 7. Testing Strategy

Mapped to `claude.md`'s required coverage list:

- `tests/unit/domain/test_authorization_service.py` — owner can edit/delete; assignee can complete but not edit; non-owner forbidden.
- `tests/unit/application/*` — use-case logic in isolation with in-memory fake repositories (fast, no DB), including `register_user` (duplicate email rejection) and `login_user`.
- `tests/integration/api/test_auth_endpoints.py` — register success, duplicate-email register, login success, wrong password, inactive user, malformed body (`422`), expired/garbled token (`401`).
- `tests/integration/api/test_task_crud_endpoints.py` — create/get/update/delete happy paths, `404` for missing task, `422` for invalid payloads.
- `tests/integration/api/test_task_filtering_pagination.py` — each filter individually, combined filters, pagination edges, envelope shape.
- `tests/integration/api/test_task_authorization.py` — non-owner PATCH/DELETE → `403`; assignee completing → `200`; assignee attempting to reassign/edit → `403`.
- `tests/integration/api/test_rate_limiting.py` — see flakiness note below.
- `tests/integration/workers/test_celery_dispatch.py` — eager-mode end-to-end + mocked-`.delay()` assertion.

**DB integration strategy: real Postgres, not SQLite.** Integration/API tests run against an actual Postgres instance (a `db-test` Compose service). The schema relies on Postgres-native features (native `ENUM`, `gen_random_uuid()`, `JSONB`) that SQLite doesn't faithfully emulate, and `claude.md` explicitly names PostgreSQL — testing against a different engine would risk false confidence. Each integration test runs inside a transaction rolled back afterward (fixture-wrapped async session), keeping tests isolated and fast without full teardown/recreation per test. Alembic migrations run once per test session to guarantee schema parity with production. Unit tests use in-memory fakes only — no DB — keeping the pyramid's base fast, which is exactly why the repository interfaces in `domain/repositories/` exist.

**Rate-limit test flakiness avoidance.** No wall-clock timing. A test-only settings override lowers the limiter's configured limit (e.g., `2/minute`) so a handful of fast requests deterministically exceeds it, and the limiter's in-memory storage is reset between tests so prior tests' counts don't leak forward.

**Celery dispatch tests without a worker.** `CELERY_TASK_ALWAYS_EAGER` for integration-style verification; `.delay()` mocking for unit-style dispatch verification. No real Redis broker or worker process needed for the automated suite; the `celery-worker` Compose service is exercised only in manual/smoke validation (Phase 9).

**Coverage.** `pytest-cov` gate at 80%, configured in `pyproject.toml`; unit tests carry most of the coverage cheaply, integration tests validate the wiring.

---

## 8. Docker Architecture

`docker-compose.yml` services:

| Service | Build/Image | depends_on | Key env vars | Ports | Volumes |
|---|---|---|---|---|---|
| `postgres` | `postgres:16-alpine` | — | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | 5432 (dev) | named volume `pgdata` |
| `redis` | `redis:7-alpine` | — | — | 6379 (dev) | none |
| `api` | build `./backend` | `postgres` (healthy), `redis` (healthy) | `DATABASE_URL, JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND, CORS_ORIGINS` | 8000:8000 | `./backend:/app` (hot reload via `uvicorn --reload`) |
| `celery-worker` | build `./backend` (same image, different command) | `redis`, `postgres` | same DB/Redis vars as `api` | none | `./backend:/app` |
| `frontend` | build `./frontend` | `api` | `VITE_API_BASE_URL` | 5173:5173 | `./frontend:/app` + anonymous volume for `node_modules` |

**Health-gated startup.** `postgres`/`redis` define `healthcheck` blocks; `api`/`celery-worker` use `depends_on: condition: service_healthy` so the app never races migrations against a not-yet-ready DB.

**Migrations via entrypoint, not manual exec.** `backend/entrypoint.sh` runs `alembic upgrade head` before `exec`-ing the real process (`uvicorn` for `api`, `celery -A app.workers.celery_app worker` for `celery-worker`). `docker compose up --build` alone yields a fully migrated, working stack — no manual `docker compose exec api alembic upgrade head` needed for normal dev flow (documented as an available fallback for one-off migration debugging).

**Secrets.** `.env` (gitignored) feeds real values to Compose via `env_file:`; `.env.example` (repo root and `backend/`) commits only placeholders. No secrets hardcoded in `docker-compose.yml` or Dockerfiles.

---

## Recorded Decisions

Decisions made explicit due to ambiguity in `claude.md`, confirmed with the user before this document was written:

1. **Authorization model.** Any authenticated user can **view** all tasks. Any authenticated user can **create** a task, becoming its `owner_id`. Only the **owner** can **update**, **delete**, or **reassign** a task — this is the "private resource" `claude.md` says must not be manipulated by another user. The **owner or the current assignee** can **complete** a task, since completing is the act of doing assigned work, not a structural edit. This required adding an `owner_id` column to `tasks` distinct from the spec's literally-enumerated `assigned_to`.
2. **Self-registration.** A public `POST /api/v1/auth/register` endpoint exists, in addition to seed-provided demo users — `claude.md` only mentions login and seed data, so this is an addition beyond the literal spec, made at the user's request.
3. **Access-token-only authentication.** No refresh-token flow; a single short-lived (default 30 min, configurable) JWT. `claude.md` mentions only "Access token," never a refresh flow — adding one would be an unrequested abstraction.
4. **Database testing strategy.** Real Postgres (via a Compose test service + per-test transactional rollback) for integration/API tests; in-memory fakes (no DB) for unit tests. Chosen over SQLite because the schema uses Postgres-specific features `claude.md` explicitly asks for.
5. **`due_date` is a `DATE`, not a timestamp** — tasks are "due on a day," and this keeps `due_date_from`/`due_date_to` simple inclusive date bounds with no timezone ambiguity.
6. **Pagination:** default `page_size=20`, hard cap `page_size<=100` (422 if exceeded).
7. **Rate limits:** general API `100/minute` per client key (IP or user id), `/auth/login` and `/auth/register` both `5/minute` per IP — documented as tunable via config, with SlowAPI's in-memory/per-instance limitation called out in the README per `claude.md`'s instruction.
8. **`/tasks/{id}/assign` never transfers ownership** — `assigned_to` and `owner_id` are fully independent; reassigning work never changes who controls the record.

---

## Next Step

Per `claude.md`'s explicit instruction not to implement the entire project in one step, Phase 2 (backend foundation: project config, database setup, SQLAlchemy models, Alembic, health check, base API structure, and tests) is a separate step to be started only after this architecture is reviewed.

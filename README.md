# Task Management App

A full-stack task management application built as a technical-interview exercise, demonstrating Clean Architecture on the backend, a typed React frontend, JWT authentication, background job processing, and a fully containerized development stack.

## Overview

Users can register, log in, create/view/update/delete tasks, assign tasks to other users, mark tasks complete, filter tasks by status and due date, and paginate results. The application demonstrates production-quality engineering practices at interview scope: layered backend architecture, comprehensive automated testing (unit + integration + API), rate limiting, async background processing, and a responsive typed frontend.

## Architecture

```mermaid
flowchart TB
    Browser["Browser<br/>(React SPA)"]

    subgraph Docker["docker compose"]
        Frontend["frontend<br/>Vite dev server :5173"]
        API["api<br/>FastAPI + Uvicorn :8000"]
        Worker["celery-worker<br/>Celery consumer"]
        Postgres[("postgres :5432")]
        Redis[("redis :6379")]
    end

    Browser -->|serves JS/HTML| Frontend
    Browser -->|REST + JWT| API
    API -->|SQLAlchemy async| Postgres
    API -->|enqueue .delay()| Redis
    Worker -->|consume| Redis
    Worker -->|write activity_logs| Postgres
```

**Request flow:** the browser talks directly to the FastAPI `api` service (not through the Vite server) using a bearer JWT obtained from `POST /api/v1/auth/login`. Every protected route resolves the current user through a single `get_current_user` dependency, and authorization (who may edit/delete/complete/assign a task) is centralized in `TaskAuthorizationService` rather than duplicated across route handlers.

**Background flow:** when a task is marked complete, the API commits the status change synchronously, then dispatches `record_task_completed_activity` to Celery. The Celery worker (a separate process, own DB connection) writes an `activity_logs` row recording the event. This is asynchronous because activity logging isn't required for the completion response to succeed — coupling it to the request would add latency and a failure mode to a primary user action for no benefit.

**Backend layering** (`backend/app/`):

```
domain/          entities, repository protocols, and pure business rules
                 (TaskAuthorizationService, TaskStatus) — no framework imports
application/     use cases (one class per operation) + Pydantic request/response schemas
infrastructure/  SQLAlchemy repository implementations, Argon2 hashing, JWT, Celery dispatch
presentation/    FastAPI routes and dependencies — thin, delegate to use cases
workers/         Celery app config and the background task
```

Route handlers never contain business logic: they resolve dependencies, call a use case, and translate domain exceptions to HTTP status codes. This is what lets the domain/application layers be unit-tested with in-memory fakes, with no database or FastAPI involved.

**Frontend layering** (`frontend/src/`): `features/{auth,tasks}` hold feature-specific API calls, TanStack Query hooks, and components; `components/{ui,layout}` hold generic/reusable pieces; `lib/` holds the shared axios client and query client; state that should survive a refresh or be shareable (task filters, pagination) lives in the URL, not React state.

## Technology Choices

| Choice | Why |
|---|---|
| **FastAPI** | Async-native, Pydantic-integrated validation, automatic OpenAPI docs — minimal boilerplate for a typed REST API. |
| **SQLAlchemy 2.x (async) + asyncpg** | Modern typed ORM API; async avoids blocking the event loop under concurrent requests. |
| **PostgreSQL** | Native `ENUM`, `JSONB`, and row-level FK cascade behavior are used directly (task status, activity payloads, owner/assignee cleanup) — features a generic SQL layer would have to emulate. |
| **Alembic** | Standard migration tooling for SQLAlchemy; autogenerate keeps migrations in sync with models. |
| **Argon2** (`argon2-cffi`) | Current OWASP-recommended password hash, memory-hard against GPU cracking. |
| **PyJWT** | Minimal, well-maintained JWT library; access-token-only (no refresh flow) matches the scope actually requested. |
| **Celery + Redis** | Celery is the standard Python task queue; Redis doubles as broker and result backend, avoiding a second infrastructure dependency. |
| **SlowAPI** | Thin FastAPI-native wrapper over a well-tested rate-limiting algorithm; documented in-memory/per-instance limitation below. |
| **React + TypeScript + Vite** | Fast dev server, typed components, no build-config yak-shaving. |
| **TanStack Query** | Server state (tasks, users) doesn't belong in component state — Query handles caching, invalidation, and loading/error states without hand-rolled reducers. |
| **React Router** | Standard SPA routing; used for auth guards and URL-synced filter/pagination state. |
| **Tailwind CSS v4** | Utility classes keep styling co-located with markup without a separate design-system build step, appropriate for this scope. |
| **React Hook Form** | Uncontrolled-input form state avoids re-rendering on every keystroke; built-in validation rules cover this app's needs without adding a schema-validation library. |

## Setup

### Docker (recommended — single command)

```bash
cp .env.example .env
cp backend/.env.example backend/.env      # edit JWT_SECRET_KEY for anything beyond local dev
cp frontend/.env.example frontend/.env
docker compose up --build
```

This starts `postgres`, `redis`, `api` (migrated automatically on startup), `celery-worker`, and `frontend`. Once healthy:

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

Seed demo data (see [Demo Credentials](#demo-credentials)):

```bash
docker compose exec api python -m scripts.seed
```

### Local development (without Docker)

Backend:

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate   # or source .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
cp .env.example .env       # point DATABASE_URL at a local Postgres
alembic upgrade head
uvicorn app.main:app --reload
```

Redis and Postgres still need to run somewhere reachable at the URLs in `.env` — `docker compose up -d postgres redis` is the easiest way to get just those two.

To run the background worker locally: `celery -A app.workers.celery_app worker --loglevel=info` (Windows: add `--pool=solo`).

Frontend:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Environment Variables

**Root `.env`** (consumed by `docker-compose.yml` for the `postgres` service):

| Variable | Purpose |
|---|---|
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Database name and credentials, also used to build `DATABASE_URL` for `api`/`celery-worker` in Compose. |

**`backend/.env`**:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Async SQLAlchemy connection string (`postgresql+asyncpg://...`). |
| `JWT_SECRET_KEY` | Signs/verifies access tokens. **Must** be changed for anything beyond local dev. |
| `JWT_ALGORITHM` | Defaults to `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime (default 30). |
| `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis connection (broker + result backend). |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins. |

**`frontend/.env`**:

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Base URL the browser calls for the API (not resolved inside Docker's network — the browser hits it directly). |

Required configuration is validated at startup (missing `DATABASE_URL`/`JWT_SECRET_KEY` fails immediately via Pydantic Settings, not on first use).

## Database

**Migrations:** Alembic, autogenerated from the SQLAlchemy models in `app/infrastructure/database/models.py`.

```bash
# Docker
docker compose exec api alembic upgrade head
docker compose exec api alembic revision --autogenerate -m "description"

# Local
cd backend && alembic upgrade head
```

The `api` and `celery-worker` containers both run `alembic upgrade head` on startup (via `entrypoint.sh`) before starting their actual process, so a fresh `docker compose up --build` always ends up migrated — no manual step required.

**Seeding:**

```bash
docker compose exec api python -m scripts.seed
# or locally: python -m scripts.seed  (from backend/, with DATABASE_URL set)
```

The seed script is idempotent — it checks whether `alice@example.com` already exists and skips entirely if so.

## Running Tests

```bash
cd backend
pytest                              # full suite (unit + integration)
pytest tests/unit                   # unit tests only — no database needed
pytest tests/integration            # integration/API tests — needs Postgres reachable
```

Integration tests run against a **real** Postgres database (the schema uses native `ENUM`/`JSONB`/UUID types that SQLite doesn't faithfully emulate) via a dedicated `taskdb_test` database, wrapped in a per-test transaction that's always rolled back — tests never see each other's data, and nothing they write persists.

## Coverage

```bash
cd backend
pytest --cov=app --cov-report=term-missing
```

Gate: 80% (configured in `pyproject.toml`); actual coverage is in the high 90s. Note: `[tool.coverage.run] concurrency = ["greenlet", "thread"]` is required — without it, coverage.py reports false "uncovered" lines for code that runs after an `await` crossing a greenlet boundary (SQLAlchemy's async-to-sync bridge) or inside FastAPI's threaded sync dependencies.

## API Documentation

Interactive Swagger UI: **http://localhost:8000/docs** (also `/redoc`). Generated from the FastAPI route definitions and Pydantic schemas — always in sync with the actual API, documents auth (bearer JWT), request/response shapes, query parameters, and error responses.

## Demo Credentials

Seeded by `python -m scripts.seed` (see [Database](#database)):

| Email | Password |
|---|---|
| `alice@example.com` | `DemoPass123!` |
| `bob@example.com` | `DemoPass123!` |
| `carol@example.com` | `DemoPass123!` |

Seed data includes tasks in all three statuses, with and without due dates (including one overdue), assigned and unassigned, and some already completed — enough variety to exercise every filter combination immediately after seeding.

These are local-development-only credentials for a project with no real users. Never reuse this pattern for a real deployment.

## Design Decisions

**Authorization model.** Any authenticated user can view all tasks — there's no per-user visibility restriction, matching the spec's "authenticated users can view tasks." Only the **owner** (creator) may update, delete, or reassign a task; the **owner or current assignee** may mark it complete. This required adding an `owner_id` column distinct from `assigned_to`: ownership (who controls the record) and assignment (who's doing the work) are different concerns, and collapsing them would either let any assignee delete a task they didn't create, or block the person actually doing the work from marking it done.

**No refresh tokens.** A single short-lived (30 min default) access token; on expiry, the frontend redirects to login. Refresh-token rotation is real complexity (secure storage, revocation, rotation-on-use) that wasn't asked for.

**Self-registration exists, but isn't the primary path.** `POST /api/v1/auth/register` is a real, tested endpoint, but the demo credentials above (via the seed script) are the intended way to explore the app with realistic data already in place.

**Rate limiting is in-memory and per-instance.** SlowAPI's default storage is per-process. Running multiple `api` replicas behind a load balancer means each replica enforces its own 100/min (general) or 5/min (login/register) quota independently — a client could get up to `N × limit` requests across `N` replicas before being universally blocked. A production multi-instance deployment would need a shared store (Redis-backed limiter) for a single global quota.

**Database testing strategy.** Unit tests (`tests/unit/`) use in-memory fake repositories — no database, no network, fast. Integration/API tests (`tests/integration/`) run against real Postgres in a per-test rolled-back transaction. This was a deliberate rejection of SQLite-for-speed: the schema leans on Postgres-specific behavior (native `ENUM`, `JSONB`, FK cascade semantics for owner/assignee cleanup) that a different engine would either reject or silently emulate differently, which would validate the wrong thing.

**Task filtering and pagination.** `GET /api/v1/tasks` combines `status`, `due_date`, `due_date_from`/`due_date_to`, and pagination via AND semantics. An invalid range (`due_date_from` after `due_date_to`) is rejected with `422` before touching the database. Page size is capped at 100 to prevent an unbounded response.

**Background task error handling.** `record_task_completed_activity` retries up to 3 times with a fixed 10s backoff on failure; if retries are exhausted, the error is logged and swallowed rather than raised — this is documented as a non-critical operation, so a logging failure must never surface to the user or be retried by the client.

## AI-Assisted Development

**Tool.** Claude Code (Anthropic) was the implementation agent across all nine phases of `claude.md`'s workflow — architecture proposal through final review — not a one-off autocomplete or a single "generate the app" prompt.

**How prompts were structured.** Each phase was driven by the corresponding section of `claude.md` plus the accumulated context of prior phases (existing schema, existing use-case patterns, existing test fixtures), so later code stayed consistent with earlier decisions rather than reinventing patterns per file. Where the spec was genuinely ambiguous (see "Design Decisions" above), the ambiguity was surfaced as an explicit question before writing code, not resolved by guessing silently.

**How generated code was validated.** Every phase ended with the same gate before moving on: the full test suite, `ruff check` + `ruff format --check`, `mypy --strict` (backend) or `tsc --noEmit` + `oxlint` (frontend) — and, critically, a live smoke test against the real stack (a running `uvicorn`/Celery worker/Postgres/Redis, or a real headless browser via Playwright), not just green checkmarks from static tools. Two examples where that live step caught something static checks missed:

- The Celery background task reused the app's pooled async database engine. Unit tests (which use a fake dispatcher) never touch it, so this passed every unit test — but failed the first time the task actually ran, in its own integration test, because `asyncio.run()` tears down its event loop on every call and a pooled asyncpg connection can't survive across loops.
- `TaskFormModal` rendered inside each table row's fragment, landing as a direct child of `<tbody>` — invalid HTML that browsers silently "fix" visually, so `tsc` and a lint pass both stayed clean. A real headless-Chromium pass (Playwright) surfaced the React hydration warning in the console.

**How edge cases were handled.** Inactive users, expired/malformed/wrong-secret tokens, duplicate-email registration, unknown assignees, tasks with no due date under a range filter, pagination past the last page, and rate-limit exhaustion are each an explicit test case (see `backend/tests/`), not just the happy path. On the frontend, loading/empty/error states are handled explicitly per screen (not just the "data arrived" case), and the dashboard's table scrolls horizontally within its own container on narrow viewports rather than squishing content or letting the page body scroll sideways — verified visually via the Playwright screenshots described above, at a 375px mobile viewport specifically.

**How security was reviewed:** covered in the [Security review highlights](docs/ai-development.md#6-security-review-highlights) section of the AI development log — password hashing, no-hash-in-response, startup secret validation, server-side assignee validation, rate-limit tiers.

**How performance was evaluated:** covered in the [Performance review highlights](docs/ai-development.md#7-performance-review-highlights) section — index placement, mandatory pagination, count-query shape, and why `EXPLAIN`-based assertions were deliberately not added to the test suite.

The full log of what was accepted, rejected, and why — spanning architecture, authentication, testing, error handling, performance, security, and frontend implementation, with the two examples above in complete detail — is in **[docs/ai-development.md](docs/ai-development.md)**.

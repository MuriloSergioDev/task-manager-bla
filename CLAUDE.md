# CLAUDE.md

Instructions for AI coding agents (Claude Code) working in this repository.
The original build specification is in [docs/specification.md](docs/specification.md);
this file is the short, current version for ongoing work.

## What this is

A full-stack task manager built as a technical-interview exercise, and
evaluated on engineering judgement and on how AI was used. It has a FastAPI
backend with a Clean Architecture layout, a React + TypeScript frontend,
Postgres, Redis and Celery, all run with Docker Compose.

## Map

- `backend/app/`: `domain/` (entities, repository interfaces, services; no
  frameworks) → `application/` (use cases, schemas) → `infrastructure/`
  (SQLAlchemy, Argon2, JWT, Celery) → `presentation/api/` (routes,
  dependencies). `workers/` holds Celery.
- `frontend/src/`: `features/{auth,tasks}` (API calls, query hooks,
  components), `components/ui` (design-system components), `styles/tokens.css`
  (design tokens), `lib/` (API client, query client).
- `docs/`: [architecture](docs/architecture.md), [user stories](docs/user-stories.md),
  [design system](docs/design-system.md), [AI development log](docs/ai-development.md).

## Commands

Start the stack: `docker compose up --build`. Seed it with
`docker compose exec api python -m scripts.seed`. The seed script is idempotent
and skips if alice already exists.

Backend (from `backend/`). Dev tools are **not** in the `api` container, so use
the local venv (`.venv/bin/python` on macOS/Linux):

```bash
.venv/Scripts/python -m pytest                 # 127 tests; integration tests need Postgres (taskdb_test)
.venv/Scripts/python -m ruff check . && .venv/Scripts/python -m ruff format --check .
.venv/Scripts/python -m mypy app               # strict
```

Frontend (from `frontend/`):

```bash
npm run lint && npm run build                  # oxlint; tsc -b (strict) + vite build
npm test                                       # Vitest unit tests (TZ pinned to UTC-3 on purpose)
npm run build-storybook && npm run test:storybook   # axe + console errors on every story
npm run test:e2e                               # Playwright against the running, seeded stack
npm run test:visual:baseline / test:visual     # before/after pixel diff for UI-neutral refactors
```

Run the whole validation pass with the `/validate` skill.

## Rules that matter here

- **Business logic lives in use cases, not routes.** Routes resolve
  dependencies, call one use case, and map domain exceptions to HTTP.
- **Authorization is server-side.** `ListTasksUseCase` always scopes results to
  the current user (owner or assignee), and single-task use cases load through
  `get_visible_task`. A task the user can't see returns `404` (never `403`,
  which would reveal that it exists). The frontend's `useTaskPermissions` only
  mirrors these rules for the UI.
- **Auth is an httpOnly cookie.** Never add `Authorization: Bearer`, token
  storage, or JWT decoding on the client. The session comes from
  `GET /auth/me`.
- **Styling uses design tokens only.** Use the utilities from
  `styles/tokens.css` and no one-off values (`text-[13px]`, hex colours).
  `faint` is never used for text, only for icons and disabled states (WCAG
  contrast). New UI components get a story. See
  [docs/design-system.md](docs/design-system.md).
- **Test first for business behaviour.** Integration tests run against real
  Postgres, not SQLite. Frontend logic (dates, URL state, permissions, API
  error handling, form payloads) gets Vitest unit tests next to the code; a
  regression test must be shown to fail against the old code. Test behaviour, not implementation. Coverage must stay
  at 80% or more (it's about 98% now).
- **No new dependency without a clear reason**, and no abstraction without a
  second use.

## Environment gotchas

- **Login is rate-limited** to 5 per minute per IP. Scripts and e2e tests sign
  in once and reuse the cookie (see `frontend/e2e/app/global-setup.ts`).
- **The frontend container uses a Windows bind mount**, so Vite polls for
  changes, and the container has its own `node_modules` volume. If you add a
  dependency the app imports at runtime, install it in the container as well.
- **On Linux, install frontend dependencies before the first `docker compose up`.**
  Otherwise Docker creates `frontend/node_modules` as root (it's the mount point for
  the container's `node_modules` volume), and `npm install` on the host fails with
  `EACCES`. CI orders its e2e steps this way for the same reason.
- **The dev database is not in its seeded state.** Tests must not assume
  specific tasks exist; assert on what the API returns.
- **A green run isn't proof that a UI change worked.** Verify in a browser
  (Playwright), and check that the dev server is serving the new code before
  trusting an unchanged screenshot.

## Working agreements

- **Verify before claiming.** Every number or "works" in docs or commit
  messages must come from something you actually ran. If something wasn't
  verified, say so.
- **Record significant decisions** (a design choice, a rejected approach, a
  bug found by validation) in `docs/ai-development.md` with the
  `/log-ai-decision` skill.
- **Keep commits logical**, one concern each, with a message that explains
  why.
- **Never commit secrets.** `.env` files are git-ignored, and `.env.example`
  documents every variable.

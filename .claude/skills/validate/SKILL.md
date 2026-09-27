---
name: validate
description: Run the project's full validation pass (backend tests, lint and types; frontend lint, strict build, Storybook a11y; end-to-end, a11y and optional visual checks against the running stack) and report results honestly. Use before committing a significant change, before a release or review, or when asked to "validate", "check everything" or "make sure it works".
---

# Validate

Run every check below, in this order. Report what ran and what it returned.
Never report a step as passing without running it, and don't skip a step
because a similar one passed.

## 0. Preconditions

- The stack is up: `docker compose ps` shows `api`, `frontend`, `postgres`,
  `redis` and `celery-worker` running, and `api` is healthy.
- Demo data exists. Signing in as `alice@example.com` must work. If it
  doesn't, run `docker compose exec api python -m scripts.seed`.
- The dev server is serving the current code (the Vite container polls a
  Windows bind mount). After edits, `curl -s localhost:5173/src/<changed file>`
  should show the change.

## 1. Backend (from `backend/`, using the local venv)

```bash
.venv/Scripts/python -m pytest --cov=app -q    # all pass, coverage >= 80%
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
.venv/Scripts/python -m mypy app
```

## 2. Frontend static checks (from `frontend/`)

```bash
npm run lint              # expect 0 warnings, not just 0 errors
npm run build             # tsc -b in strict mode (app, node and e2e configs) + vite build
npm run build-storybook
npm run test:storybook    # every story: no console errors, no axe violations
```

## 3. Frontend against the running app

```bash
npm run test:e2e          # smoke flows + axe on every screen, desktop and mobile
```

Login is rate-limited to 5 per minute. If a rerun fails in global setup with
"Could not sign in", wait a minute and rerun; don't loosen the limit.

If a test fails, find out whether the **app or the test** is wrong before
changing either. A test that asserts on specific tasks in the dev database is
wrong, because the data isn't fixed.

## 4. Visual regression (only for changes that shouldn't alter the UI)

```bash
npm run test:visual:baseline   # BEFORE the change
# ...make the change...
npm run test:visual            # AFTER: any differing pixel fails
```

Every difference must be explained (for example, "only the done rows changed,
because the done colour was darkened"). If the UI was meant to change, say
which screens changed and why, instead of re-baselining silently.

## 5. Report

Summarise each step as passed or failed, with its numbers (tests, coverage,
warnings). For failures, give the cause and what you did about it. If a real
bug was found, fix it, add a regression test, and record it with
`/log-ai-decision`.

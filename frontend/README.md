# Frontend

React 19 + TypeScript (strict) + Vite, with TanStack Query for server state,
React Router, React Hook Form and Tailwind CSS v4. The project overview,
architecture and setup are in the [root README](../README.md).

## Structure

| Path | Contents |
|---|---|
| `src/features/auth`, `src/features/tasks` | Feature code: API calls, TanStack Query hooks, components |
| `src/components/ui` | Design-system components (import from `components/ui`) |
| `src/components/layout` | App shell, route guards, auth layout |
| `src/styles/tokens.css` | Design tokens, the only place visual values are defined |
| `src/lib` | Shared API client (cookie session, error normalisation) and query client |
| `e2e/app` | Playwright tests against the running app: smoke, a11y, visual |
| `e2e/storybook` | Playwright + axe over every Storybook story |

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Vite dev server on http://localhost:5173 (normally run by Docker Compose) |
| `npm run lint` | oxlint; fails on warnings |
| `npm run build` | `tsc -b` (strict: app, node and e2e configs) + production build |
| `npm run storybook` | Design system on http://localhost:6006 |
| `npm run build-storybook` | Static Storybook in `storybook-static/` |
| `npm run test:storybook` | Every story: no console errors, no axe violations (needs `build-storybook` first) |
| `npm run test:e2e` | Smoke flows + axe on every screen, desktop and mobile. Needs the stack running and seeded |
| `npm run test:visual:baseline` / `test:visual` | Before/after pixel comparison for changes that shouldn't alter the UI |

Install the test browser once with `npx playwright install chromium`.

`test:e2e` signs in once per run as the seeded demo user, because login is
rate-limited to 5 per minute. Point it at another URL with `E2E_BASE_URL`.

## Conventions

See [docs/design-system.md](../docs/design-system.md) for styling rules (tokens
only, WCAG AA text contrast, a story for every component) and
[CLAUDE.md](../CLAUDE.md) for the project's working rules.

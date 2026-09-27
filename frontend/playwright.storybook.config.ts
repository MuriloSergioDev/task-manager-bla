import { defineConfig } from '@playwright/test'

// Checks every Storybook story in a real browser: no console errors and no
// axe violations. Runs against the static build (npm run build-storybook),
// so it needs no backend and runs in CI.

const port = 6007

export default defineConfig({
  testDir: './e2e/storybook',
  forbidOnly: Boolean(process.env.CI),
  reporter: 'list',
  use: { baseURL: `http://localhost:${port}` },
  webServer: {
    command: `npx vite preview --outDir storybook-static --port ${port} --strictPort`,
    url: `http://localhost:${port}/index.json`,
    reuseExistingServer: !process.env.CI,
  },
})

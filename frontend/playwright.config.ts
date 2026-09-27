import { defineConfig } from '@playwright/test'

// Browser tests against the running app (`docker compose up` + seeded demo
// data). Storybook has its own config: playwright.storybook.config.ts.
//
// Visual tests (tagged @visual) are a before/after tool for refactors that
// shouldn't change the UI, not committed baselines: the seed data's due
// dates are relative to the day it was seeded, and screenshots differ by OS.
// `npm run test:visual:baseline` before the change, `npm run test:visual`
// after. See docs/design-system.md.

const baseURL = process.env.E2E_BASE_URL ?? 'http://localhost:5173'

export default defineConfig({
  testDir: './e2e/app',
  // One shared demo account, and login is rate-limited to 5/min per IP:
  // run serially and sign in once (global-setup.ts) for the whole run.
  workers: 1,
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  reporter: 'list',
  globalSetup: './e2e/app/global-setup.ts',
  snapshotPathTemplate: 'e2e/.visual-baseline/{projectName}/{arg}{ext}',
  expect: {
    // threshold: per-pixel colour tolerance (absorbs antialiasing only);
    // maxDiffPixels: 0 means any real change fails.
    toHaveScreenshot: { animations: 'disabled', caret: 'hide', threshold: 0.1, maxDiffPixels: 0 },
  },
  use: {
    baseURL,
    storageState: 'e2e/.auth/demo-user.json',
    // Grayscale text AA: LCD sub-pixel rendering varies between runs and
    // would make screenshot comparison flaky.
    launchOptions: { args: ['--disable-lcd-text', '--font-render-hinting=none'] },
  },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1360, height: 900 } } },
    { name: 'mobile', use: { viewport: { width: 390, height: 844 } } },
  ],
})

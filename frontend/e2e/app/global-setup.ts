import { chromium, type FullConfig } from '@playwright/test'

import { DEMO_USER } from './demo-user.ts'

/** Signs in once and saves the session cookie for every test. Logging in per
 *  test would trip the API's 5-per-minute login rate limit. */
export default async function globalSetup(config: FullConfig) {
  const { baseURL, storageState } = config.projects[0].use
  const browser = await chromium.launch()
  const page = await browser.newPage()

  await page.goto(`${baseURL}/login`)
  await page.getByLabel('Email').fill(DEMO_USER.email)
  await page.getByLabel('Password').fill(DEMO_USER.password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await page.waitForURL('**/dashboard', { timeout: 15_000 }).catch(() => {
    throw new Error(
      `Could not sign in as ${DEMO_USER.email} at ${baseURL}. Is the stack running ` +
        '(docker compose up) and seeded (python -m scripts.seed)?',
    )
  })

  await page.context().storageState({ path: storageState as string })
  await browser.close()
}

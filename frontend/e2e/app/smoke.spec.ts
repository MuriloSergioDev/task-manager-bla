import { expect, test } from '@playwright/test'

import { SIGNED_OUT } from './demo-user.ts'
import { waitForDashboard, waitForDialog } from './fixtures.ts'

// The frontend talking to the real API: the paths a reviewer would try first.
// Backend behaviour itself is covered by backend/tests; these only prove the
// wiring (cookie session, query params, mutations + cache invalidation).

test.describe('dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
    await waitForDashboard(page)
  })

  test('loads the signed-in session and the task list', async ({ page }) => {
    // The email is hidden below `sm` by design; Log out is on every size.
    await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible()
    await expect(page.getByRole('region', { name: 'Task list' }).getByRole('listitem').first()).toBeVisible()
  })

  // Data-independent: whatever the database holds, the filter must reach the
  // API, and the list must show exactly what the API returned.
  test('status filter goes to the URL, the API and the list', async ({ page }) => {
    const filteredResponse = page.waitForResponse(
      (response) => response.url().includes('/api/v1/tasks?') && response.url().includes('status=IN_PROGRESS'),
    )
    await page.getByText('In progress', { exact: true }).first().click()

    const response = await filteredResponse
    expect(response.ok()).toBe(true)
    await expect(page).toHaveURL(/status=IN_PROGRESS/)

    const body = (await response.json()) as { items: { status: string }[] }
    expect(body.items.every((task) => task.status === 'IN_PROGRESS')).toBe(true)
    await expect(page.getByRole('region', { name: 'Task list' }).getByRole('listitem')).toHaveCount(body.items.length)
  })

  test('filters survive a reload and clear in one click', async ({ page }) => {
    await page.goto('/dashboard?status=COMPLETED&due_date_from=2020-01-01')
    await page.reload()
    await waitForDashboard(page)

    await expect(page.getByRole('radio', { name: 'Done' })).toBeChecked()
    await expect(page.getByLabel('Due from')).toHaveValue('2020-01-01')

    await page.getByRole('button', { name: 'Clear filters' }).first().click()
    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.getByRole('radio', { name: 'All' })).toBeChecked()
    await expect(page.getByLabel('Due from')).toHaveValue('')
  })

  test('creates a task and deletes it again', async ({ page }) => {
    const title = `E2E smoke ${Date.now()}`

    await page.getByRole('button', { name: 'New task' }).first().click()
    await page.getByLabel('Title').fill(title)
    await page.getByRole('button', { name: 'Create task' }).click()
    await expect(page.getByRole('dialog')).toBeHidden()
    // Newest first, so a new task is always on page 1.
    const row = page.getByRole('listitem').filter({ hasText: title })
    await expect(row).toBeVisible()

    await row.getByRole('button', { name: `Delete "${title}"` }).click()
    const dialog = await waitForDialog(page)
    await dialog.getByRole('button', { name: 'Delete task' }).click()
    await expect(dialog).toBeHidden()
    await expect(row).toBeHidden()
  })
})

test.describe('signed out', () => {
  test.use({ storageState: SIGNED_OUT })

  // Regression: the /auth/me session probe returned 401 and the API client's
  // global 401 handler bounced every signed-out visitor from /register to
  // /login. Only in-app navigation to /register worked.
  test('can open the registration page directly', async ({ page }) => {
    await page.goto('/register')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/\/register$/)
    await expect(page.getByRole('heading', { name: 'Create an account' })).toBeVisible()
  })

  test('is sent to sign in when opening the dashboard', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login$/)
  })
})

import { expect, test, type Page } from '@playwright/test'

import { SIGNED_OUT } from './demo-user.ts'
import { waitForDashboard, waitForDialog } from './fixtures.ts'

// @visual: pixel comparison for refactors that must not change the UI (e.g.
// the design-token migration). Not part of the default run -- see
// playwright.config.ts for the baseline/compare workflow.

// Native <select> text lands on varying sub-pixel offsets between runs;
// masking keeps each box's size and position in the comparison but drops
// the glyph noise.
const screenshot = (page: Page, name: string, fullPage = false) =>
  expect(page).toHaveScreenshot(`${name}.png`, { fullPage, mask: [page.locator('select')] })

test.describe('@visual signed out', () => {
  test.use({ storageState: SIGNED_OUT })

  test('login', async ({ page }) => {
    await page.goto('/login')
    await page.evaluate(() => document.fonts.ready)
    await screenshot(page, 'login', true)
  })

  test('login errors', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page.getByText('Email is required')).toBeVisible()
    await screenshot(page, 'login-errors')
  })
})

test.describe('@visual signed in', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
    await waitForDashboard(page)
    await page.evaluate(() => document.fonts.ready)
  })

  test('dashboard', async ({ page }) => {
    await screenshot(page, 'dashboard', true)
  })

  test('new task dialog', async ({ page }) => {
    await page.getByRole('button', { name: 'New task' }).first().click()
    await waitForDialog(page)
    await screenshot(page, 'new-task')
  })

  test('delete confirmation', async ({ page }) => {
    await page.getByRole('button', { name: /^Delete "/ }).first().click()
    await waitForDialog(page)
    await screenshot(page, 'delete')
  })

  test('filtered empty state', async ({ page }) => {
    await page.goto('/dashboard?due_date_from=2001-01-01&due_date_to=2001-01-02')
    await expect(page.getByText('Nothing matches these filters')).toBeVisible()
    await screenshot(page, 'empty-filtered')
  })
})

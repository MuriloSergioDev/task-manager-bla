import { AxeBuilder } from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'

import { SIGNED_OUT } from './demo-user.ts'
import { waitForDashboard, waitForDialog } from './fixtures.ts'

// axe (WCAG 2.x A/AA rules) on every screen and dialog of the real app.
// Storybook's a11y checks cover components in isolation; this covers them
// composed, with real data (e.g. landmarks, contrast on actual surfaces).

async function expectNoViolations(page: Page) {
  const { violations } = await new AxeBuilder({ page }).analyze()
  const summary = violations.map(
    (violation) => `${violation.id} (${violation.impact}): ${violation.nodes.map((node) => node.target).join(', ')}`,
  )
  expect(summary).toEqual([])
}

test.describe('signed out', () => {
  test.use({ storageState: SIGNED_OUT })

  test('login', async ({ page }) => {
    await page.goto('/login')
    await expectNoViolations(page)
  })

  test('login with validation errors', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page.getByText('Email is required')).toBeVisible()
    await expectNoViolations(page)
  })

  test('register', async ({ page }) => {
    await page.goto('/register')
    await expectNoViolations(page)
  })
})

test.describe('signed in', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
    await waitForDashboard(page)
  })

  test('dashboard', async ({ page }) => {
    await expectNoViolations(page)
  })

  test('new task dialog', async ({ page }) => {
    await page.getByRole('button', { name: 'New task' }).first().click()
    await waitForDialog(page)
    await expectNoViolations(page)
  })

  test('delete confirmation', async ({ page }) => {
    await page.getByRole('button', { name: /^Delete "/ }).first().click()
    await waitForDialog(page)
    await expectNoViolations(page)
  })

  test('filtered empty state', async ({ page }) => {
    await page.goto('/dashboard?due_date_from=2001-01-01&due_date_to=2001-01-02')
    await expect(page.getByText('Nothing matches these filters')).toBeVisible()
    await expectNoViolations(page)
  })
})

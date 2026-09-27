import { expect, type Page } from '@playwright/test'

/** Waits until the dialog is visible and its fade-in has finished: axe and
 *  screenshots taken mid-animation see partially transparent text. */
export async function waitForDialog(page: Page) {
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  await dialog.evaluate((element) =>
    Promise.all(element.ownerDocument.getAnimations().map((animation) => animation.finished)),
  )
  return dialog
}

/** The dashboard is ready once rows have rendered and the users query has
 *  resolved (assignee selects stay disabled until then). */
export async function waitForDashboard(page: Page) {
  await page.getByRole('heading', { name: 'Tasks', level: 1 }).waitFor()
  await page.waitForLoadState('networkidle')
  await page.waitForFunction(() => {
    const selects = Array.from(document.querySelectorAll('select'))
    return selects.every((select) => !select.disabled)
  })
}

import { AxeBuilder } from '@axe-core/playwright'
import { expect, test } from '@playwright/test'
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

// One test per story, generated from the built Storybook's index, so a new
// story is covered automatically. Read from disk (not the server) because
// tests must be declared synchronously.

interface IndexEntry {
  id: string
  title: string
  name: string
  type: 'story' | 'docs'
}

const indexPath = resolve(process.cwd(), 'storybook-static/index.json')
if (!existsSync(indexPath)) {
  throw new Error('storybook-static/ not found: run `npm run build-storybook` first.')
}
const index = JSON.parse(readFileSync(indexPath, 'utf8')) as { entries: Record<string, IndexEntry> }
const stories = Object.values(index.entries).filter((entry) => entry.type === 'story')

for (const story of stories) {
  test(`${story.title} / ${story.name}`, async ({ page }) => {
    const errors: string[] = []
    page.on('console', (message) => {
      if (message.type() === 'error') errors.push(message.text())
    })
    page.on('pageerror', (error) => errors.push(error.message))

    await page.goto(`/iframe.html?id=${story.id}&viewMode=story`)
    await page.locator('#storybook-root > *').first().waitFor()
    await page.waitForLoadState('networkidle')

    const { violations } = await new AxeBuilder({ page }).include('#storybook-root').analyze()
    const summary = violations.map(
      (violation) => `${violation.id} (${violation.impact}): ${violation.nodes.map((node) => node.target).join(', ')}`,
    )
    expect(summary, 'axe violations').toEqual([])
    expect(errors, 'console errors').toEqual([])
  })
}

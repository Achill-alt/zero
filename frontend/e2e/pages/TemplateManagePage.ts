/**
 * Page Object Model for the Template Management page.
 */
import type { Page, Locator } from '@playwright/test'

export class TemplateManagePage {
  readonly page: Page
  readonly heading: Locator
  readonly table: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.locator('h2')
    this.table = page.locator('.el-table, table')
  }

  async goto() {
    await this.page.goto('/templates')
    await this.page.waitForLoadState('networkidle')
  }
}

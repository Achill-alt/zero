/**
 * Page Object Model for the Expiring Panel page.
 */
import type { Page, Locator } from '@playwright/test'

export class ExpiringPanelPage {
  readonly page: Page
  readonly heading: Locator
  readonly statCards: Locator
  readonly table: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.locator('h2')
    this.statCards = page.locator('.stat-card, [class*="stat"]')
    this.table = page.locator('.el-table, table')
  }

  async goto() {
    await this.page.goto('/expiring')
    await this.page.waitForLoadState('networkidle')
  }
}

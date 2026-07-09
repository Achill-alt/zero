/**
 * Page Object Model for the Audit Logs page.
 */
import type { Page, Locator } from '@playwright/test'

export class AuditLogsPage {
  readonly page: Page
  readonly heading: Locator
  readonly table: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.locator('h2')
    this.table = page.locator('.el-table, table')
  }

  async goto() {
    await this.page.goto('/admin/audit-logs')
    await this.page.waitForLoadState('networkidle')
  }
}

/**
 * Page Object Model for the Approval Center page.
 */
import type { Page, Locator } from '@playwright/test'

export class ApprovalCenterPage {
  readonly page: Page
  readonly heading: Locator
  readonly pendingTable: Locator
  readonly approveButton: Locator
  readonly rejectButton: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.locator('h2')
    this.pendingTable = page.locator('.el-table, table')
    this.approveButton = page.locator('button:has-text("通过")').first()
    this.rejectButton = page.locator('button:has-text("驳回")').first()
  }

  async goto() {
    await this.page.goto('/approvals')
    await this.page.waitForLoadState('networkidle')
  }

  async getPendingCount(): Promise<number> {
    const rows = this.page.locator('.el-table__body tr, tbody tr')
    return await rows.count()
  }
}

/**
 * Page Object Model for the Notification List page.
 */
import type { Page, Locator } from '@playwright/test'

export class NotificationListPage {
  readonly page: Page
  readonly heading: Locator
  readonly notificationItems: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.locator('h2')
    this.notificationItems = page.locator('.el-card, .notification-item, li')
  }

  async goto() {
    await this.page.goto('/notifications')
    await this.page.waitForLoadState('networkidle')
  }
}

/**
 * Page Object Model for the Dashboard page.
 */
import type { Page, Locator } from '@playwright/test'

export class DashboardPage {
  readonly page: Page
  readonly heading: Locator
  readonly statCards: Locator
  readonly expiringSection: Locator
  readonly sidebar: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.locator('h2')
    this.statCards = page.locator('.stat-card, [class*="stat"]')
    this.expiringSection = page.locator('text=即将到期')
    this.sidebar = page.locator('.el-menu, aside')
  }

  async goto() {
    await this.page.goto('/dashboard')
    await this.page.waitForLoadState('networkidle')
  }

  async getPageTitle(): Promise<string> {
    return (await this.heading.textContent()) || ''
  }

  /** Navigate via sidebar menu item */
  async navigateTo(label: string) {
    await this.sidebar.locator(`text=${label}`).first().click()
    await this.page.waitForLoadState('networkidle')
  }
}

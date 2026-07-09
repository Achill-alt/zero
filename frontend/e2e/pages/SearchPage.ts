/**
 * Page Object Model for the Search page.
 */
import type { Page, Locator } from '@playwright/test'

export class SearchPage {
  readonly page: Page
  readonly heading: Locator
  readonly searchInput: Locator
  readonly searchButton: Locator
  readonly results: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.locator('h2')
    this.searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="search"]').first()
    this.searchButton = page.locator('button:has-text("搜索"), button:has-text("Search")').first()
    this.results = page.locator('.el-table__body tr, tbody tr, .search-result')
  }

  async goto() {
    await this.page.goto('/search')
    await this.page.waitForLoadState('networkidle')
  }

  async search(query: string) {
    if ((await this.searchInput.count()) > 0) {
      await this.searchInput.fill(query)
      if ((await this.searchButton.count()) > 0) {
        await this.searchButton.click()
      } else {
        await this.searchInput.press('Enter')
      }
      await this.page.waitForLoadState('networkidle')
    }
  }
}

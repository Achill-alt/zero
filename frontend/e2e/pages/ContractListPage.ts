/**
 * Page Object Model for the Contract List page.
 */
import type { Page, Locator } from '@playwright/test'

export class ContractListPage {
  readonly page: Page
  readonly heading: Locator
  readonly createButton: Locator
  readonly searchInput: Locator
  readonly table: Locator
  readonly tableRows: Locator
  readonly pagination: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.locator('h2')
    this.createButton = page.locator('a:has-text("新建合同"), button:has-text("新建合同")')
    this.searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="search"]')
    this.table = page.locator('.el-table, table')
    this.tableRows = page.locator('.el-table__body tr, tbody tr')
    this.pagination = page.locator('.el-pagination')
  }

  async goto() {
    await this.page.goto('/contracts')
    await this.page.waitForLoadState('networkidle')
  }

  async clickCreate() {
    await this.createButton.click()
    await this.page.waitForURL('**/contracts/create')
  }

  async clickContract(title: string) {
    await this.page.locator(`text=${title}`).first().click()
    await this.page.waitForURL('**/contracts/*')
  }

  async getFirstContractTitle(): Promise<string | null> {
    const firstRow = this.tableRows.first()
    if ((await firstRow.count()) === 0) return null
    return await firstRow.textContent()
  }

  async search(query: string) {
    if ((await this.searchInput.count()) > 0) {
      await this.searchInput.fill(query)
      await this.searchInput.press('Enter')
      await this.page.waitForLoadState('networkidle')
    }
  }
}

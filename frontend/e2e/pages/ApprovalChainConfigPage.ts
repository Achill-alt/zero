/**
 * Page Object Model for the Approval Chain Config page.
 */
import type { Page, Locator } from '@playwright/test'

export class ApprovalChainConfigPage {
  readonly page: Page
  readonly heading: Locator
  readonly createButton: Locator
  readonly chainCards: Locator
  readonly dialog: Locator
  readonly nameInput: Locator
  readonly saveButton: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.locator('h2')
    this.createButton = page.locator('button:has-text("新建审批链")')
    this.chainCards = page.locator('.el-card')
    this.dialog = page.locator('.el-dialog')
    this.nameInput = page.locator('.el-dialog .el-form-item:has-text("名称") input').first()
    this.saveButton = page.locator('.el-dialog button:has-text("保存")')
  }

  async goto() {
    await this.page.goto('/admin/approval-chains')
    await this.page.waitForLoadState('networkidle')
  }

  async clickCreate() {
    await this.createButton.click()
    await this.dialog.waitFor({ state: 'visible' })
  }

  async fillFormAndSave(name: string) {
    await this.nameInput.fill(name)
    await this.saveButton.click()
    await this.page.waitForLoadState('networkidle')
  }

  async getChainCount(): Promise<number> {
    return await this.chainCards.count()
  }
}

/**
 * Page Object Model for the Contract Detail page.
 */
import type { Page, Locator } from '@playwright/test'

export class ContractDetailPage {
  readonly page: Page
  readonly heading: Locator
  readonly statusTag: Locator
  readonly backButton: Locator
  readonly editButton: Locator
  readonly submitButton: Locator
  readonly approveButton: Locator
  readonly rejectButton: Locator
  readonly withdrawButton: Locator
  readonly voidButton: Locator
  readonly archiveButton: Locator
  readonly contentCard: Locator
  readonly attachmentCard: Locator
  readonly approvalHistoryCard: Locator
  readonly uploadArea: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.locator('h2')
    this.statusTag = page.locator('.el-tag').first()
    this.backButton = page.locator('button:has-text("返回")')
    this.editButton = page.locator('button:has-text("编辑")')
    this.submitButton = page.locator('button:has-text("提交审批")')
    this.approveButton = page.locator('button:has-text("通过")')
    this.rejectButton = page.locator('button:has-text("驳回")')
    this.withdrawButton = page.locator('button:has-text("撤回审批")')
    this.voidButton = page.locator('button:has-text("作废")')
    this.archiveButton = page.locator('button:has-text("归档")')
    this.contentCard = page.locator('.el-card:has-text("合同内容")')
    this.attachmentCard = page.locator('.el-card:has-text("附件")')
    this.approvalHistoryCard = page.locator('.el-card:has-text("审批历史")')
    this.uploadArea = page.locator('.el-upload')
  }

  async goto(contractId: number | string) {
    await this.page.goto(`/contracts/${contractId}`)
    await this.page.waitForLoadState('networkidle')
  }

  async getStatus(): Promise<string | null> {
    return await this.statusTag.textContent()
  }

  async clickSubmitApproval() {
    await this.submitButton.click()
    await this.page.waitForLoadState('networkidle')
  }

  async clickApprove(comment?: string) {
    await this.approveButton.click()
    // Handle the ElMessageBox prompt dialog
    const promptInput = this.page.locator('.el-message-box__input input, .el-message-box input[type="text"]')
    if ((await promptInput.count()) > 0 && comment) {
      await promptInput.fill(comment)
    }
    await this.page.locator('.el-message-box__btns button:has-text("通过"), .el-message-box button:has-text("确定")').first().click()
    await this.page.waitForLoadState('networkidle')
  }

  async clickReject(reason: string) {
    await this.rejectButton.click()
    const promptInput = this.page.locator('.el-message-box__input input, .el-message-box input[type="text"]')
    if ((await promptInput.count()) > 0) {
      await promptInput.fill(reason)
    }
    await this.page.locator('.el-message-box__btns button:has-text("驳回"), .el-message-box button:has-text("确定")').first().click()
    await this.page.waitForLoadState('networkidle')
  }

  async clickWithdraw() {
    await this.withdrawButton.click()
    await this.page.locator('.el-message-box button:has-text("确定")').first().click()
    await this.page.waitForLoadState('networkidle')
  }

  async clickVoid() {
    await this.voidButton.click()
    await this.page.locator('.el-message-box button:has-text("确定")').first().click()
    await this.page.waitForLoadState('networkidle')
  }

  async clickArchive() {
    await this.archiveButton.click()
    await this.page.waitForLoadState('networkidle')
  }

  async clickEdit() {
    await this.editButton.click()
    await this.page.waitForURL('**/edit')
  }
}

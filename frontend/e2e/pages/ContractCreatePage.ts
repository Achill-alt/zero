/**
 * Page Object Model for the Contract Create page.
 *
 * Form structure (from ContractCreate.vue):
 * - Title: input[placeholder="请输入合同标题"]
 * - Contract type: el-select with label "合同类型"
 * - Amount: el-input-number within "合同金额"
 * - Party A: input[placeholder="甲方名称"]
 * - Party B: input[placeholder="乙方名称"]
 * - Start date: el-date-picker within "开始日期"
 * - End date: el-date-picker within "结束日期"
 * - Content: textarea[placeholder="请输入合同内容..."]
 * - Save draft: button:has-text("保存草稿")
 * - Submit approval: button:has-text("提交审批")
 */
import type { Page, Locator } from '@playwright/test'

export class ContractCreatePage {
  readonly page: Page
  readonly heading: Locator
  readonly titleInput: Locator
  readonly typeSelect: Locator
  readonly amountInput: Locator
  readonly partyAInput: Locator
  readonly partyBInput: Locator
  readonly startDatePicker: Locator
  readonly endDatePicker: Locator
  readonly contentTextarea: Locator
  readonly saveDraftBtn: Locator
  readonly submitBtn: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.locator('h2')
    this.titleInput = page.getByPlaceholder('请输入合同标题')
    this.typeSelect = page.locator('.el-form-item:has-text("合同类型") .el-select').first()
    this.amountInput = page.locator('.el-form-item:has-text("合同金额") input').first()
    this.partyAInput = page.getByPlaceholder('甲方名称')
    this.partyBInput = page.getByPlaceholder('乙方名称')
    this.startDatePicker = page.locator('.el-form-item:has-text("开始日期") input').first()
    this.endDatePicker = page.locator('.el-form-item:has-text("结束日期") input').first()
    this.contentTextarea = page.getByPlaceholder('请输入合同内容...')
    this.saveDraftBtn = page.locator('button:has-text("保存草稿")')
    this.submitBtn = page.locator('button:has-text("提交审批")')
  }

  async goto() {
    await this.page.goto('/contracts/create')
    await this.page.waitForLoadState('networkidle')
  }

  /**
   * Select an option from an el-select dropdown.
   */
  private async selectOption(formItemText: string, optionText: string) {
    // Click the select to open dropdown
    const selectInput = this.page.locator(`.el-form-item:has-text("${formItemText}") .el-select input`).first()
    await selectInput.click()
    await this.page.waitForTimeout(500)
    // Click the option by visible text
    const option = this.page.locator('.el-select-dropdown__item').filter({ hasText: optionText }).first()
    await option.waitFor({ state: 'visible', timeout: 5000 })
    await option.click()
    await this.page.waitForTimeout(300)
  }

  /**
   * Pick a date in the el-date-picker.
   */
  private async pickDate(formItemText: string, dateStr: string) {
    const input = this.page.locator(`.el-form-item:has-text("${formItemText}") input`).first()
    await input.click()
    await input.fill(dateStr)
    // Click outside to close date picker
    await this.page.locator('h2').first().click()
    await this.page.waitForTimeout(300)
  }

  async fillForm(data: {
    title: string
    contract_type?: string
    amount?: number
    party_a?: string
    party_b?: string
    start_date?: string
    end_date?: string
    content?: string
  }) {
    // Title (required)
    await this.titleInput.fill(data.title)

    // Contract type (required) - use select dropdown
    if (data.contract_type) {
      await this.selectOption('合同类型', data.contract_type)
    }

    // Amount
    if (data.amount != null) {
      await this.amountInput.fill(String(data.amount))
    }

    // Parties
    if (data.party_a) {
      await this.partyAInput.fill(data.party_a)
    }
    if (data.party_b) {
      await this.partyBInput.fill(data.party_b)
    }

    // Dates (required)
    if (data.start_date) {
      await this.pickDate('开始日期', data.start_date)
    }
    if (data.end_date) {
      await this.pickDate('结束日期', data.end_date)
    }

    // Content
    if (data.content) {
      await this.contentTextarea.fill(data.content)
    }
  }

  /** Click "保存草稿" (save as draft) */
  async saveDraft() {
    await this.saveDraftBtn.click()
    await this.page.waitForURL(/.*\/contracts\/\d+/, { timeout: 10_000 })
  }

  /** Click "提交审批" (submit for approval) */
  async submitForApproval() {
    await this.submitBtn.click()
    await this.page.waitForURL(/.*\/contracts\/\d+/, { timeout: 10_000 })
  }
}

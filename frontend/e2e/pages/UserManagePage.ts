/**
 * Page Object Model for the User Management page.
 */
import type { Page, Locator } from '@playwright/test'

export class UserManagePage {
  readonly page: Page
  readonly heading: Locator
  readonly addUserButton: Locator
  readonly table: Locator
  readonly dialog: Locator
  readonly usernameInput: Locator
  readonly passwordInput: Locator
  readonly roleSelect: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.locator('h2')
    this.addUserButton = page.locator('button:has-text("新增用户")')
    this.table = page.locator('.el-table, table')
    this.dialog = page.locator('.el-dialog')
    this.usernameInput = page.locator('.el-dialog .el-form-item:has-text("用户名") input').first()
    this.passwordInput = page.locator('.el-dialog .el-form-item:has-text("密码") input').first()
    this.roleSelect = page.locator('.el-dialog .el-form-item:has-text("角色") .el-select').first()
  }

  async goto() {
    await this.page.goto('/admin/users')
    await this.page.waitForLoadState('networkidle')
  }

  async clickAddUser() {
    await this.addUserButton.click()
    await this.dialog.waitFor({ state: 'visible' })
  }

  async fillNewUserForm(data: { username: string; password: string; role?: string }) {
    await this.usernameInput.fill(data.username)
    await this.passwordInput.fill(data.password)
  }

  async submitNewUser() {
    await this.dialog.locator('button:has-text("创建")').click()
    await this.page.waitForLoadState('networkidle')
  }
}

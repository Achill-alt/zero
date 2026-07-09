/**
 * Page Object Model for the Register page.
 */
import type { Page, Locator } from '@playwright/test'

export class RegisterPage {
  readonly page: Page
  readonly heading: Locator
  readonly usernameInput: Locator
  readonly passwordInput: Locator
  readonly roleSelect: Locator
  readonly registerButton: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.locator('h2')
    this.usernameInput = page.locator('input[placeholder*="用户名"], .el-form-item:has-text("用户名") input').first()
    this.passwordInput = page.locator('input[type="password"]').first()
    this.roleSelect = page.locator('.el-form-item:has-text("角色") .el-select').first()
    this.registerButton = page.locator('button:has-text("注册"), button:has-text("创建")').first()
  }

  async goto() {
    await this.page.goto('/admin/register')
    await this.page.waitForLoadState('networkidle')
  }
}

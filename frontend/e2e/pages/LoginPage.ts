/**
 * Page Object Model for the Login page.
 * Based on Login.vue structure:
 * - Username: input[placeholder="请输入用户名"]
 * - Password: input[placeholder="请输入密码"]
 * - Login button: .login-btn (text "登 录" with letter-spacing)
 * - Heading: "企业合同管理系统"
 */
import type { Page, Locator } from '@playwright/test'

export class LoginPage {
  readonly page: Page
  readonly usernameInput: Locator
  readonly passwordInput: Locator
  readonly loginButton: Locator
  readonly heading: Locator
  readonly loginCard: Locator

  constructor(page: Page) {
    this.page = page
    this.usernameInput = page.getByPlaceholder('请输入用户名')
    this.passwordInput = page.getByPlaceholder('请输入密码')
    this.loginButton = page.locator('.login-btn').or(page.locator('button:has-text("登 录")'))
    this.heading = page.locator('h1:has-text("企业合同管理系统")')
    this.loginCard = page.locator('.login-card')
  }

  async goto() {
    await this.page.goto('/login')
    await this.page.waitForLoadState('networkidle')
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username)
    await this.passwordInput.fill(password)
    await this.loginButton.click()
  }

  /** Wait for redirect after successful login */
  async waitForRedirect() {
    await this.page.waitForURL('**/dashboard', { timeout: 10_000 })
  }
}

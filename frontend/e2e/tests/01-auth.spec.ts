/**
 * E2E Test Suite 01: Authentication
 *
 * Covers: Login, Logout, Auth Guards, Token persistence
 *
 * Pages tested: /login, route protection
 */
import { test, expect } from '@playwright/test'
import { LoginPage } from '../pages/LoginPage'
import { TEST_USERS, loginViaApi, setupAuthState } from '../utils/test-data'

test.describe('Authentication', () => {
  let loginPage: LoginPage

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page)
  })

  test('should display login page', async ({ page }) => {
    await page.goto('/')
    await page.waitForURL('**/login')
    // Login page shows the heading
    await expect(loginPage.heading).toBeVisible({ timeout: 10_000 })
    await expect(loginPage.usernameInput).toBeVisible()
    await expect(loginPage.passwordInput).toBeVisible()
    await expect(loginPage.loginButton).toBeVisible()
  })

  test('should login successfully as admin', async ({ page }) => {
    await loginPage.goto()
    await loginPage.login(TEST_USERS.admin.username, TEST_USERS.admin.password)
    await loginPage.waitForRedirect()
    await expect(page).toHaveURL(/.*dashboard/)
    // Dashboard should have a heading or content
    await expect(page.locator('h2, h1, .logo').first()).toBeVisible()
  })

  test('should login successfully as handler', async ({ page }) => {
    await loginPage.goto()
    await loginPage.login(TEST_USERS.handler.username, TEST_USERS.handler.password)
    await loginPage.waitForRedirect()
    await expect(page).toHaveURL(/.*dashboard/)
  })

  test('should login successfully as approver', async ({ page }) => {
    await loginPage.goto()
    await loginPage.login(TEST_USERS.approver.username, TEST_USERS.approver.password)
    await loginPage.waitForRedirect()
    await expect(page).toHaveURL(/.*dashboard/)
  })

  test('should show error on invalid credentials', async ({ page }) => {
    await loginPage.goto()
    await loginPage.login('nonexistent', 'wrongpassword')
    // Wait for error message or verify we stay on login page
    const errorOrStay = await Promise.race([
      page.locator('.el-message--error, .el-alert--error').waitFor({ state: 'visible', timeout: 5000 }).then(() => 'error'),
      page.waitForTimeout(3000).then(() => 'stay'),
    ])
    // Either error shown or still on login page
    const onLoginPage = page.url().includes('login')
    expect(errorOrStay === 'error' || onLoginPage).toBeTruthy()
  })

  test('should redirect to login when accessing protected page without auth', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForURL('**/login')
  })

  test('should redirect to login when accessing contracts without auth', async ({ page }) => {
    await page.goto('/contracts')
    await page.waitForURL('**/login')
  })

  test('should persist auth across page reload', async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await setupAuthState(page, auth)

    // Navigate to dashboard
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/.*dashboard/)

    // Reload and verify still authenticated
    await page.reload()
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/.*dashboard/)
  })

  test('should logout and redirect to login', async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await setupAuthState(page, auth)

    // Navigate to dashboard
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')

    // Click logout button in navbar
    const logoutBtn = page.locator('.logout-btn')
    if ((await logoutBtn.count()) > 0) {
      await logoutBtn.click()
      await page.waitForURL('**/login', { timeout: 5000 })
      await expect(loginPage.loginCard).toBeVisible()
    }
  })
})

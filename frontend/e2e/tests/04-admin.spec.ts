/**
 * E2E Test Suite 04: Admin Pages
 *
 * Covers: User Management, Approval Chain Config, Audit Logs, Register
 *
 * Pages tested: /admin/users, /admin/approval-chains, /admin/audit-logs, /admin/register
 */
import { test, expect } from '@playwright/test'
import { UserManagePage } from '../pages/UserManagePage'
import { ApprovalChainConfigPage } from '../pages/ApprovalChainConfigPage'
import { AuditLogsPage } from '../pages/AuditLogsPage'
import { RegisterPage } from '../pages/RegisterPage'
import { TEST_USERS, loginViaApi, setupAuthState } from '../utils/test-data'

test.describe('Admin - User Management', () => {
  test.beforeEach(async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await setupAuthState(page, auth)
  })

  test('should load user management page', async ({ page }) => {
    const userPage = new UserManagePage(page)
    await userPage.goto()
    await page.waitForTimeout(1000)
    // Should show heading or user table content
    const hasHeading = (await page.locator('h2:has-text("用户管理")').count()) > 0
    const hasTable = (await page.locator('.el-table, table').count()) > 0
    expect(hasHeading || hasTable).toBeTruthy()
  })

  test('should show add user dialog', async ({ page }) => {
    const userPage = new UserManagePage(page)
    await userPage.goto()
    await userPage.clickAddUser()
    await expect(userPage.dialog).toBeVisible()
    await expect(userPage.dialog.locator('text=新增用户').first()).toBeVisible()
  })

  test('should create a new user', async ({ page }) => {
    const userPage = new UserManagePage(page)
    await userPage.goto()
    await userPage.clickAddUser()
    await userPage.usernameInput.fill(`e2e_newuser_${Date.now()}`)
    await userPage.passwordInput.fill('123456')
    await userPage.submitNewUser()
    // Should show success message
    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 5000 })
  })

  test('should toggle user active status', async ({ page }) => {
    const userPage = new UserManagePage(page)
    await userPage.goto()
    const toggle = page.locator('.el-switch').first()
    if ((await toggle.count()) > 0) {
      await toggle.click()
      await page.waitForTimeout(1000)
      const message = page.locator('.el-message').first()
      await expect(message).toBeVisible({ timeout: 3000 })
    }
  })
})

test.describe('Admin - Approval Chain Config', () => {
  test.beforeEach(async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await setupAuthState(page, auth)
  })

  test('should load approval chain config page', async ({ page }) => {
    const chainPage = new ApprovalChainConfigPage(page)
    await chainPage.goto()
    await page.waitForTimeout(1000)
    const hasHeading = (await page.locator('h2').count()) > 0
    const hasContent = (await page.locator('.el-card, .el-empty, button:has-text("新建审批链")').count()) > 0
    expect(hasHeading || hasContent).toBeTruthy()
  })

  test('should show create chain dialog', async ({ page }) => {
    const chainPage = new ApprovalChainConfigPage(page)
    await chainPage.goto()
    await chainPage.clickCreate()
    await expect(chainPage.dialog).toBeVisible()
  })

  test('should create a new approval chain', async ({ page }) => {
    const chainPage = new ApprovalChainConfigPage(page)
    await chainPage.goto()
    await chainPage.clickCreate()
    await chainPage.fillFormAndSave(`E2E Chain ${Date.now()}`)
    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 5000 })
  })
})

test.describe('Admin - Audit Logs', () => {
  test.beforeEach(async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await setupAuthState(page, auth)
  })

  test('should load audit logs page', async ({ page }) => {
    const logsPage = new AuditLogsPage(page)
    await logsPage.goto()
    await page.waitForTimeout(1000)
    // Audit logs page has h2 "审计日志" or el-table
    const hasHeading = (await page.locator('h2:has-text("审计日志")').count()) > 0
    const hasTable = (await page.locator('.el-table, table').count()) > 0
    expect(hasHeading || hasTable).toBeTruthy()
  })
})

test.describe('Admin - Register', () => {
  test.beforeEach(async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await setupAuthState(page, auth)
  })

  test('should load register page', async ({ page }) => {
    const regPage = new RegisterPage(page)
    await regPage.goto()
    await page.waitForTimeout(1000)
    // Register page has card-title "新增用户" (no h2)
    const hasTitle = (await page.locator('text=新增用户').count()) > 0
    const hasForm = (await page.locator('.el-form').count()) > 0
    expect(hasTitle || hasForm).toBeTruthy()
  })
})

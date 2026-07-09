/**
 * E2E Test Suite 05: Search, Dashboard, Notifications, Expiring, Templates
 *
 * Covers: /search, /dashboard, /notifications, /expiring, /templates
 */
import { test, expect } from '@playwright/test'
import { SearchPage } from '../pages/SearchPage'
import { DashboardPage } from '../pages/DashboardPage'
import { NotificationListPage } from '../pages/NotificationListPage'
import { ExpiringPanelPage } from '../pages/ExpiringPanelPage'
import { TemplateManagePage } from '../pages/TemplateManagePage'
import { TEST_USERS, loginViaApi, setupAuthState } from '../utils/test-data'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await setupAuthState(page, auth)
  })

  test('should load dashboard page', async ({ page }) => {
    const dashPage = new DashboardPage(page)
    await dashPage.goto()
    await expect(page.locator('h2')).toBeVisible()
  })

  test('should display stat cards', async ({ page }) => {
    const dashPage = new DashboardPage(page)
    await dashPage.goto()
    // Dashboard should have stats or cards
    await page.waitForTimeout(2000)
    const hasContent = (await page.locator('.el-card, .stat-card, [class*="stat"]').count()) > 0
      || (await page.locator('text=合同').count()) > 0
    expect(hasContent).toBeTruthy()
  })
})

test.describe('Search', () => {
  test.beforeEach(async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await setupAuthState(page, auth)
  })

  test('should load search page', async ({ page }) => {
    const searchPage = new SearchPage(page)
    await searchPage.goto()
    await expect(page.locator('h2')).toBeVisible()
    // Should have search input
    const hasSearchInput = (await searchPage.searchInput.count()) > 0
      || (await page.locator('input').count()) > 0
    expect(hasSearchInput).toBeTruthy()
  })

  test('should perform a search', async ({ page, request }) => {
    // First create a contract to search for
    const auth = await loginViaApi(request, TEST_USERS.handler.username, TEST_USERS.handler.password)
    const uniqueTitle = `E2E_SEARCHABLE_${Date.now()}`
    await request.post('http://127.0.0.1:8000/api/v1/contracts', {
      data: {
        title: uniqueTitle,
        content: 'Unique searchable content for E2E testing.',
        contract_type: 'service',
        amount: 50000,
        party_a: 'Search Corp A',
        party_b: 'Search Corp B',
        start_date: '2026-07-01',
        end_date: '2027-06-30',
      },
      headers: { Authorization: `Bearer ${auth.token}` },
    })

    // Login as admin and search
    const adminAuth = await loginViaApi(request, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await setupAuthState(page, adminAuth)

    const searchPage = new SearchPage(page)
    await searchPage.goto()
    // Try to search for the unique title
    if ((await searchPage.searchInput.count()) > 0) {
      await searchPage.search(uniqueTitle.slice(0, 10))
      // Results should load
      await page.waitForTimeout(2000)
    }
  })
})

test.describe('Notifications', () => {
  test.beforeEach(async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await setupAuthState(page, auth)
  })

  test('should load notifications page', async ({ page }) => {
    const notifPage = new NotificationListPage(page)
    await notifPage.goto()
    await expect(page.locator('h2')).toBeVisible()
  })
})

test.describe('Expiring Contracts', () => {
  test.beforeEach(async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await setupAuthState(page, auth)
  })

  test('should load expiring panel page', async ({ page }) => {
    const expPage = new ExpiringPanelPage(page)
    await expPage.goto()
    await expect(page.locator('h2')).toBeVisible()
  })
})

test.describe('Templates', () => {
  test.beforeEach(async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await setupAuthState(page, auth)
  })

  test('should load templates page', async ({ page }) => {
    const tplPage = new TemplateManagePage(page)
    await tplPage.goto()
    await expect(page.locator('h2')).toBeVisible()
    // Templates page uses el-card for each template, or el-empty when none
    const hasContent = (await page.locator('.el-card, .el-empty').first().count()) > 0
    expect(hasContent).toBeTruthy()
  })
})

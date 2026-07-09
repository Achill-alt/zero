/**
 * E2E Test Suite 02: Contract CRUD
 *
 * Covers: Create contract, list contracts, view detail, edit, void
 *
 * Pages tested: /contracts, /contracts/create, /contracts/:id, /contracts/:id/edit
 */
import { test, expect } from '@playwright/test'
import { LoginPage } from '../pages/LoginPage'
import { ContractListPage } from '../pages/ContractListPage'
import { ContractCreatePage } from '../pages/ContractCreatePage'
import { ContractDetailPage } from '../pages/ContractDetailPage'
import { TEST_USERS, loginViaApi, setupAuthState, generateContract } from '../utils/test-data'

test.describe('Contract CRUD', () => {
  test.beforeEach(async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.handler.username, TEST_USERS.handler.password)
    await setupAuthState(page, auth)
  })

  test('should navigate to contract list page', async ({ page }) => {
    const listPage = new ContractListPage(page)
    await listPage.goto()
    await expect(page.locator('h2')).toBeVisible()
    // Should have "合同" somewhere
    await expect(page.locator('text=合同').first()).toBeVisible()
  })

  test('should navigate to create contract page', async ({ page }) => {
    await page.goto('/contracts/create')
    await page.waitForLoadState('networkidle')
    // Should have form elements
    const formItem = page.locator('.el-form-item').first()
    await expect(formItem).toBeVisible({ timeout: 5000 })
  })

  test('should load contract create form', async ({ page }) => {
    const createPage = new ContractCreatePage(page)
    await createPage.goto()
    await page.waitForTimeout(500)
    // Verify form elements exist
    await expect(createPage.titleInput).toBeVisible()
    // Rich text editor (TipTap) instead of textarea
    await expect(page.locator('.rich-text-editor').first()).toBeVisible()
    // Should have save draft button
    await expect(createPage.saveDraftBtn).toBeVisible()
  })

  test('should create a new draft contract', async ({ page, request }) => {
    // Create contract via API (more reliable than UI for el-select dropdowns)
    const auth = await loginViaApi(request, TEST_USERS.handler.username, TEST_USERS.handler.password)
    const contractData = generateContract({
      title: `E2E UI Draft ${Date.now()}`,
      contract_type: 'purchase',
    })
    const createResp = await request.post('http://127.0.0.1:8000/api/v1/contracts', {
      data: contractData,
      headers: { Authorization: `Bearer ${auth.token}` },
    })
    const json = await createResp.json()
    expect(json.data.id).toBeDefined()

    // Verify in UI
    await setupAuthState(page, auth)
    const detailPage = new ContractDetailPage(page)
    await detailPage.goto(json.data.id)

    // Should show the title and draft status
    await expect(page.locator(`text=${contractData.title}`).first()).toBeVisible()
    await expect(page.locator('.el-tag:has-text("草稿")').first()).toBeVisible()
  })

  test('should show created contract in list', async ({ page, request }) => {
    // Create via API first to ensure existence
    const auth = await loginViaApi(request, TEST_USERS.handler.username, TEST_USERS.handler.password)
    const contractData = generateContract()
    const createResp = await request.post('http://127.0.0.1:8000/api/v1/contracts', {
      data: contractData,
      headers: { Authorization: `Bearer ${auth.token}` },
    })
    expect(createResp.ok()).toBeTruthy()

    // Navigate to list and verify
    const listPage = new ContractListPage(page)
    await listPage.goto()
    await expect(page.locator(`text=${contractData.title}`).first()).toBeVisible({ timeout: 5000 })
  })

  test('should view contract detail', async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.handler.username, TEST_USERS.handler.password)
    const contractData = generateContract({ title: 'E2E Detail View Test' })
    const createResp = await request.post('http://127.0.0.1:8000/api/v1/contracts', {
      data: contractData,
      headers: { Authorization: `Bearer ${auth.token}` },
    })
    const json = await createResp.json()
    const cid = json.data.id

    const detailPage = new ContractDetailPage(page)
    await detailPage.goto(cid)
    await expect(page.locator(`text=${contractData.title}`).first()).toBeVisible()
    // Should show contract type
    await expect(page.locator('text=采购').first()).toBeVisible()
  })

  test('should show edit button for draft contracts', async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.handler.username, TEST_USERS.handler.password)
    const contractData = generateContract({ title: 'E2E Edit Test' })
    const createResp = await request.post('http://127.0.0.1:8000/api/v1/contracts', {
      data: contractData,
      headers: { Authorization: `Bearer ${auth.token}` },
    })
    const json = await createResp.json()
    const cid = json.data.id

    const detailPage = new ContractDetailPage(page)
    await detailPage.goto(cid)
    await expect(detailPage.editButton).toBeVisible()
  })

  test('should void a draft contract', async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.handler.username, TEST_USERS.handler.password)
    const contractData = generateContract({ title: 'E2E Void Test' })
    const createResp = await request.post('http://127.0.0.1:8000/api/v1/contracts', {
      data: contractData,
      headers: { Authorization: `Bearer ${auth.token}` },
    })
    const json = await createResp.json()
    const cid = json.data.id

    const detailPage = new ContractDetailPage(page)
    await detailPage.goto(cid)
    await expect(detailPage.voidButton).toBeVisible()
    await detailPage.clickVoid()
    // After void, status should change
    await expect(page.locator('.el-tag:has-text("作废")').first()).toBeVisible({ timeout: 5000 })
  })
})

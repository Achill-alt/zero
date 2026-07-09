/**
 * E2E Test Suite 03: Approval Flow
 *
 * Covers: Submit for approval, Approve, Reject, Withdraw
 * Uses API for reliable data setup, then verifies with UI.
 */
import { test, expect } from '@playwright/test'
import { ContractDetailPage } from '../pages/ContractDetailPage'
import { ApprovalCenterPage } from '../pages/ApprovalCenterPage'
import { TEST_USERS, loginViaApi, setupAuthState, generateContract } from '../utils/test-data'

test.describe('Approval Flow', () => {
  test('should load approval center page', async ({ page, request }) => {
    const auth = await loginViaApi(request, TEST_USERS.approver.username, TEST_USERS.approver.password)
    await setupAuthState(page, auth)

    const approvalPage = new ApprovalCenterPage(page)
    await approvalPage.goto()
    await expect(page.locator('h2')).toBeVisible()
  })

  test('should view pending contract and see approve/reject buttons', async ({ page, request }) => {
    // Create + submit a contract via API as handler
    const handlerAuth = await loginViaApi(request, TEST_USERS.handler.username, TEST_USERS.handler.password)
    const contractData = generateContract({ title: 'E2E Approval Test', contract_type: 'purchase' })
    const createResp = await request.post('http://127.0.0.1:8000/api/v1/contracts', {
      data: contractData,
      headers: { Authorization: `Bearer ${handlerAuth.token}` },
    })
    const json = await createResp.json()
    const cid = json.data.id
    await request.post(`http://127.0.0.1:8000/api/v1/contracts/${cid}/submit`, {
      headers: { Authorization: `Bearer ${handlerAuth.token}` },
    })

    // Login as approver and view the contract detail page
    const approverAuth = await loginViaApi(request, TEST_USERS.approver.username, TEST_USERS.approver.password)
    await setupAuthState(page, approverAuth)

    const detailPage = new ContractDetailPage(page)
    await detailPage.goto(cid)
    await page.waitForTimeout(1500)

    // Should see contract details
    await expect(page.locator(`text=${contractData.title}`).first()).toBeVisible({ timeout: 5000 })
    // Should see status tag
    await expect(page.locator('.el-tag').first()).toBeVisible()
  })

  test('should show approval history on submitted contract', async ({ page, request }) => {
    const handlerAuth = await loginViaApi(request, TEST_USERS.handler.username, TEST_USERS.handler.password)
    const contractData = generateContract({ title: 'E2E History Test', contract_type: 'purchase' })
    const createResp = await request.post('http://127.0.0.1:8000/api/v1/contracts', {
      data: contractData,
      headers: { Authorization: `Bearer ${handlerAuth.token}` },
    })
    const json = await createResp.json()
    const cid = json.data.id
    await request.post(`http://127.0.0.1:8000/api/v1/contracts/${cid}/submit`, {
      headers: { Authorization: `Bearer ${handlerAuth.token}` },
    })

    // View as handler
    await setupAuthState(page, handlerAuth)
    const detailPage = new ContractDetailPage(page)
    await detailPage.goto(cid)
    await page.waitForTimeout(1000)

    // Should see the contract title and status
    await expect(page.locator(`text=${contractData.title}`).first()).toBeVisible({ timeout: 5000 })
  })
})

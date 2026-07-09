/**
 * Test user credentials for E2E tests.
 */
export const TEST_USERS = {
  admin: {
    username: 'e2e_admin',
    password: 'admin123',
    role: 'admin' as const,
  },
  handler: {
    username: 'e2e_handler',
    password: '123456',
    role: 'handler' as const,
  },
  approver: {
    username: 'e2e_approver',
    password: '123456',
    role: 'approver' as const,
  },
} as const

/**
 * API base URL for direct API calls during tests.
 */
export const API_BASE = 'http://127.0.0.1:8000/api/v1'

/**
 * Login via API and return auth token + user data.
 */
export async function loginViaApi(
  request: any,
  username: string,
  password: string,
): Promise<{ token: string; user: Record<string, unknown> }> {
  const resp = await request.post(`${API_BASE}/auth/login`, {
    data: { username, password },
  })
  const json = await resp.json()
  return {
    token: json.data.access_token,
    user: json.data.user,
  }
}

/**
 * Generate unique contract data for tests.
 */
let contractCounter = 0
export function generateContract(overrides: Record<string, unknown> = {}) {
  contractCounter++
  const now = new Date()
  const end = new Date(now.getFullYear() + 1, now.getMonth(), now.getDate())
  return {
    title: `E2E Test Contract #${contractCounter}`,
    content: `<p>Automated E2E test contract #${contractCounter}</p>`,
    contract_type: 'purchase',
    amount: 100000 + contractCounter * 1000,
    party_a: 'E2E Company A',
    party_b: 'E2E Company B',
    start_date: now.toISOString().slice(0, 10),
    end_date: end.toISOString().slice(0, 10),
    ...overrides,
  }
}

/**
 * Helper to set up authenticated browser state via localStorage.
 */
export async function setupAuthState(
  page: any,
  user: { token: string; user: Record<string, unknown> },
) {
  await page.goto('/')
  await page.evaluate(
    ({ token, user }) => {
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
    },
    { token: user.token, user: user.user },
  )
  // Reload so the app picks up the token
  await page.reload()
  await page.waitForLoadState('networkidle')
}

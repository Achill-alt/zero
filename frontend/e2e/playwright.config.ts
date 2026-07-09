import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E configuration for Contract Management System.
 *
 * Servers (backend + frontend) must be started manually before running tests:
 *   # Terminal 1 - Backend
 *   cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
 *
 *   # Terminal 2 - Frontend
 *   cd frontend && npx vite --port 5173 --strictPort
 *
 * Usage:
 *   npm run test:e2e                     # run all tests
 *   npx playwright test --headed         # run with visible browser
 *   npx playwright test tests/01-auth    # run specific suite
 */
export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  timeout: 30_000,
  expect: { timeout: 10_000 },

  globalSetup: require.resolve('./utils/global-setup'),

  use: {
    baseURL: 'http://localhost:5173',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})

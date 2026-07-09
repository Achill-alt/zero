/**
 * Global setup: seed the E2E test database before all tests.
 * Runs once before any test starts.
 */
import { execSync } from 'child_process'
import path from 'path'

async function globalSetup() {
  const seedScript = path.resolve(__dirname, 'seed_db.py')
  const backendDir = path.resolve(__dirname, '..', '..', '..', 'backend')
  console.log(`[global-setup] Running: python "${seedScript}" "${backendDir}"`)

  try {
    execSync(`python "${seedScript}" "${backendDir}"`, {
      stdio: 'inherit',
      timeout: 30_000,
    })
    console.log('[global-setup] Database seeded successfully')
  } catch (error) {
    console.error('[global-setup] Failed to seed database:', error)
    throw error
  }
}

export default globalSetup

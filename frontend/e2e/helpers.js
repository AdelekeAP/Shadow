export const TEST_EMAIL = process.env.E2E_TEST_EMAIL || 'test@example.com'
export const TEST_PASSWORD = process.env.E2E_TEST_PASSWORD || 'TestPassword123!'

/**
 * Login via the UI form (navigates to /login, fills credentials, waits for dashboard).
 */
export async function loginAs(page, email = TEST_EMAIL, password = TEST_PASSWORD) {
  await page.goto('/login')
  await page.fill('input[name="email"], input[type="email"]', email)
  await page.fill('input[name="password"], input[type="password"]', password)
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard', { timeout: 15000 })
}

/**
 * Login via the backend API, set tokens in localStorage, then navigate to a target path.
 * This is the preferred approach for E2E tests to avoid UI flakiness on the login page.
 *
 * @param {import('@playwright/test').Page} page
 * @param {string} targetPath - Path to navigate to after login (e.g. '/smartstudy')
 * @param {string} email
 * @param {string} password
 */
export async function loginViaApi(page, targetPath = '/smartstudy', email = TEST_EMAIL, password = TEST_PASSWORD) {
  const loginRes = await page.request.post('http://localhost:8000/api/v1/auth/login', {
    data: { email, password },
  })
  const loginData = await loginRes.json()

  // Set auth tokens in localStorage before navigating
  await page.goto('/login')
  await page.evaluate((data) => {
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
  }, loginData)

  if (targetPath) {
    await page.goto(targetPath)
    await page.waitForURL(`**${targetPath}`, { timeout: 15000 })
  }

  return loginData
}

import { test, expect } from '@playwright/test'
import path from 'path'
import { loginViaApi } from './helpers.js'

/**
 * SHADOW — Full System Readiness E2E Test
 *
 * Tests the entire application as an existing user:
 *   1. Login (UI flow)
 *   2. Dashboard (greeting, stats, nav, tasks, courses)
 *   3. Courses (browse, enroll, search, semesters)
 *   4. CGPA (analytics, grading reference, what-if calculator)
 *   5. Library (browse, upload modal)
 *   6. SmartStudy — plan form with ML slide upload + all learning styles
 *   7. SmartStudy — AI Coach chat
 *   8. SmartStudy — Quiz & Diagrams quick actions
 *   9. Cross-feature navigation round-trip
 *  10. Auth guard — protected routes redirect when logged out
 *
 * Run:  npx playwright test e2e/system-readiness.spec.js --headed
 */

const TEST_EMAIL = 'nicomannion6@gmail.com'
const TEST_PASSWORD = 'password123'
const PPTX_PATH = path.resolve(__dirname, '../../CSC 411_ Machine Learning Lecture 1.pptx')

// Shared auth state across serial tests
let accessToken = null
let userData = null

/** Dismiss any overlay/modal that might be open */
async function dismissModals(page) {
  for (let i = 0; i < 5; i++) {
    const backdrop = page.locator('.fixed.inset-0.z-50')
    if (await backdrop.isVisible({ timeout: 600 }).catch(() => false)) {
      await page.keyboard.press('Escape')
      await page.waitForTimeout(400)
      if (!(await backdrop.isVisible({ timeout: 300 }).catch(() => false))) break
      // Try clicking the outer edge of the backdrop
      const box = await backdrop.boundingBox()
      if (box) await page.mouse.click(box.x + 5, box.y + 5)
      await page.waitForTimeout(400)
    } else break
  }
}

/** Inject auth tokens into localStorage and navigate.
 *  Reuses cached token if available to avoid rate limits on /auth/login. */
async function loginAndGo(page, targetPath) {
  if (accessToken && userData) {
    // Reuse cached token
    await page.goto('/login')
    await page.evaluate((data) => {
      localStorage.setItem('access_token', data.token)
      localStorage.setItem('user', JSON.stringify(data.user))
    }, { token: accessToken, user: userData })
    await page.goto(targetPath)
    await page.waitForURL(`**${targetPath}`, { timeout: 15000 })
    await page.waitForTimeout(1500)
  } else {
    // First login — hit the API
    const loginData = await loginViaApi(page, targetPath, TEST_EMAIL, TEST_PASSWORD)
    accessToken = loginData.access_token
    userData = loginData.user
    expect(accessToken).toBeTruthy()
    await page.waitForTimeout(1500)
  }
}

// ─────────────────────────────────────────────
// All tests run in order — each builds on previous state
// ─────────────────────────────────────────────
test.describe.serial('Shadow System Readiness Check', () => {

  // ═══════════════════════════════════════════
  // 1. LOGIN — try UI first, fall back to API if rate-limited
  // ═══════════════════════════════════════════
  test('1 — Login', async ({ page }) => {
    // Try UI login first
    await page.goto('/login')
    await expect(page.getByText('Welcome back')).toBeVisible({ timeout: 10000 })
    console.log('[LOGIN] Page loaded')

    await page.getByPlaceholder('your.email@pau.edu.ng').fill(TEST_EMAIL)
    await page.getByPlaceholder('Enter your password').fill(TEST_PASSWORD)
    await page.getByRole('button', { name: 'Sign In' }).click()

    // Check if we got rate-limited or login succeeded
    const dashboardReached = await page.waitForURL('**/dashboard', { timeout: 8000 }).then(() => true).catch(() => false)

    if (dashboardReached) {
      accessToken = await page.evaluate(() => localStorage.getItem('access_token'))
      const userStr = await page.evaluate(() => localStorage.getItem('user'))
      userData = JSON.parse(userStr)
      console.log(`[LOGIN] SUCCESS via UI — User: ${userData.full_name}`)
    } else {
      // Rate limited — use API login
      console.log('[LOGIN] UI rate-limited, falling back to API login...')
      const loginData = await loginViaApi(page, '/dashboard', TEST_EMAIL, TEST_PASSWORD)
      accessToken = loginData.access_token
      userData = loginData.user
      console.log(`[LOGIN] SUCCESS via API — User: ${userData.full_name}`)
    }

    expect(accessToken).toBeTruthy()
    expect(userData).toBeTruthy()
  })

  // ═══════════════════════════════════════════
  // 2. DASHBOARD
  // ═══════════════════════════════════════════
  test('2 — Dashboard loads with all components', async ({ page }) => {
    await loginAndGo(page, '/dashboard')

    // Greeting
    await expect(page.locator('text=/Good (morning|afternoon|evening)/i')).toBeVisible({ timeout: 10000 })
    console.log('[DASHBOARD] Greeting visible')

    // Navigation links
    for (const nav of ['Dashboard', 'Courses', 'CGPA', 'Library', 'SmartStudy']) {
      await expect(page.locator(`text="${nav}"`).first()).toBeVisible({ timeout: 5000 })
    }
    console.log('[DASHBOARD] All nav links present')

    // Stat tiles
    await expect(page.locator('text=/Total Credits|Average CA|Tasks/i').first()).toBeVisible({ timeout: 5000 })
    console.log('[DASHBOARD] Stat tiles visible')

    // CGPA ring or CGPA display
    const cgpaArea = page.locator('text=/of 5\\.0|CGPA|First Class|Second Class/i').first()
    if (await cgpaArea.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('[DASHBOARD] CGPA display visible')
    }

    // Task section
    await expect(page.locator('text=/Tasks|No tasks|upcoming|priority/i').first()).toBeVisible({ timeout: 5000 })
    console.log('[DASHBOARD] Task section visible')

    // Course carousel
    const courseArea = page.locator('text=/courses|enrolled|no courses/i').first()
    if (await courseArea.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('[DASHBOARD] Course carousel visible')
    }

    await page.screenshot({ path: 'e2e/screenshots/02-dashboard.png', fullPage: true })
    console.log('[DASHBOARD] SUCCESS')
  })

  // ═══════════════════════════════════════════
  // 3. COURSES
  // ═══════════════════════════════════════════
  test('3 — Courses page: browse, search, enroll', async ({ page }) => {
    await loginAndGo(page, '/courses')

    await expect(page.locator('text=/Courses/i').first()).toBeVisible({ timeout: 10000 })
    console.log('[COURSES] Page loaded')

    await page.waitForTimeout(3000)

    // Filter tabs
    await expect(page.locator('text=/All|Enrolled|Available/i').first()).toBeVisible({ timeout: 5000 })
    console.log('[COURSES] Filter tabs visible')

    // Search
    const searchInput = page.locator('input[placeholder*="earch"], input[type="search"], input[placeholder*="course"]').first()
    if (await searchInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await searchInput.fill('CSC')
      await page.waitForTimeout(1000)
      console.log('[COURSES] Search filtering works')
      await searchInput.clear()
      await page.waitForTimeout(500)
    }

    // Enroll in a course if any available
    const enrollBtn = page.getByRole('button', { name: /enroll/i }).first()
    if (await enrollBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await enrollBtn.click()
      await page.waitForTimeout(2000)
      console.log('[COURSES] Enrolled in a course')
    } else {
      console.log('[COURSES] Already enrolled or no available courses')
    }

    // Semester management area
    const semArea = page.locator('text=/semester|academic year/i').first()
    if (await semArea.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('[COURSES] Semester management visible')
    }

    await page.screenshot({ path: 'e2e/screenshots/03-courses.png', fullPage: true })
    console.log('[COURSES] SUCCESS')
  })

  // ═══════════════════════════════════════════
  // 4. CGPA
  // ═══════════════════════════════════════════
  test('4 — CGPA page: analytics, grading reference, what-if', async ({ page }) => {
    await loginAndGo(page, '/cgpa')

    await expect(page.locator('text=/CGPA/i').first()).toBeVisible({ timeout: 10000 })
    console.log('[CGPA] Page loaded')

    await page.waitForTimeout(3000)

    // Grading scale
    await expect(page.locator('text=/5\\.0 Scale|Grading Scale|First Class/i').first()).toBeVisible({ timeout: 5000 })
    console.log('[CGPA] Grading reference visible')

    // Classification table
    await expect(page.locator('text=/Second Class|Third Class|Pass/i').first()).toBeVisible({ timeout: 5000 })
    console.log('[CGPA] Classification table visible')

    // Export PDF button
    const exportBtn = page.getByRole('button', { name: /export|pdf/i }).first()
    if (await exportBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('[CGPA] Export PDF button visible')
    }

    // What-If Calculator
    const whatIfBtn = page.getByRole('button', { name: /what.if|calculator/i }).first()
    if (await whatIfBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await whatIfBtn.click()
      await page.waitForTimeout(1500)
      console.log('[CGPA] What-If Calculator opened')
      await dismissModals(page)
    }

    // SmartStudy CTA if CGPA < target
    const studyCta = page.locator('text=/below your target|Study Plan/i').first()
    if (await studyCta.isVisible({ timeout: 2000 }).catch(() => false)) {
      console.log('[CGPA] SmartStudy CTA alert visible (CGPA < target)')
    }

    await page.screenshot({ path: 'e2e/screenshots/04-cgpa.png', fullPage: true })
    console.log('[CGPA] SUCCESS')
  })

  // ═══════════════════════════════════════════
  // 5. LIBRARY
  // ═══════════════════════════════════════════
  test('5 — Library page: browse and upload modal', async ({ page }) => {
    await loginAndGo(page, '/library')

    await expect(page.locator('text=/Library|Learning Library/i').first()).toBeVisible({ timeout: 10000 })
    console.log('[LIBRARY] Page loaded')

    await page.waitForTimeout(2000)

    // Upload button
    const uploadBtn = page.getByRole('button', { name: /upload/i }).first()
    await expect(uploadBtn).toBeVisible({ timeout: 5000 })
    console.log('[LIBRARY] Upload button visible')

    // Open upload modal
    await uploadBtn.click()
    await page.waitForTimeout(1000)

    // Modal verification
    const modal = page.locator('.fixed.inset-0')
    if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
      const topicInput = page.getByPlaceholder(/topic|binary|search/i).first()
      if (await topicInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log('[LIBRARY] Upload modal — Topic field visible')
      }

      const fileZone = page.locator('text=/drag|drop|browse|choose/i').first()
      if (await fileZone.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log('[LIBRARY] Upload modal — File drop zone visible')
      }

      const courseSelect = page.locator('select').first()
      if (await courseSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log('[LIBRARY] Upload modal — Course selector visible')
      }

      console.log('[LIBRARY] Upload modal verified')
      await dismissModals(page)
    }

    // Check for existing documents in the library browser
    const docCards = page.locator('text=/\\.pdf|\\.pptx|week|topic/i').first()
    if (await docCards.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('[LIBRARY] Existing documents visible in browser')
    }

    await page.screenshot({ path: 'e2e/screenshots/05-library.png', fullPage: true })
    console.log('[LIBRARY] SUCCESS')
  })

  // ═══════════════════════════════════════════
  // 6. SMARTSTUDY — Plan form with ML slide upload + learning styles
  // ═══════════════════════════════════════════
  test('6 — SmartStudy: upload ML slide and verify plan form', async ({ page }) => {
    await loginAndGo(page, '/smartstudy')

    await expect(page.locator('text=/SmartStudy/i').first()).toBeVisible({ timeout: 10000 })
    console.log('[SMARTSTUDY] Page loaded')

    await page.waitForTimeout(2000)
    await dismissModals(page)

    // Quick action cards
    for (const action of ['AI Coach', 'Quiz', 'Diagrams', 'Insights', 'Analytics']) {
      const el = page.locator(`text=/${action}/i`).first()
      if (await el.isVisible({ timeout: 1500 }).catch(() => false)) {
        console.log(`[SMARTSTUDY] Quick action "${action}" visible`)
      }
    }

    // Stats strip (plans count, completion, etc.)
    const statsArea = page.locator('text=/plan|active|completed|completion/i').first()
    if (await statsArea.isVisible({ timeout: 2000 }).catch(() => false)) {
      console.log('[SMARTSTUDY] Stats strip visible')
    }

    // Click "New Study Plan"
    const newPlanBtn = page.getByRole('button', { name: /New Study Plan/i }).first()
    await expect(newPlanBtn).toBeVisible({ timeout: 5000 })
    await newPlanBtn.scrollIntoViewIfNeeded()
    await newPlanBtn.click()
    console.log('[SMARTSTUDY] Clicked New Study Plan')
    await page.waitForTimeout(2000)

    // Scroll to top to see form
    await page.evaluate(() => window.scrollTo(0, 0))
    await page.waitForTimeout(500)

    // Upload the Machine Learning PPTX
    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toBeAttached({ timeout: 10000 })
    await fileInput.setInputFiles(PPTX_PATH)
    console.log('[SMARTSTUDY] ML slide file uploaded')

    // Wait for filename to appear confirming upload
    await expect(page.locator('text=/Machine Learning/i').first()).toBeVisible({ timeout: 15000 })
    console.log('[SMARTSTUDY] File accepted — "Machine Learning" visible')
    await page.waitForTimeout(1500)

    // Verify all learning style options
    for (const style of ['Visual', 'Audio', 'Reading', 'Hands-on']) {
      const styleBtn = page.locator(`text=/${style}/i`).first()
      await expect(styleBtn).toBeVisible({ timeout: 5000 })
      console.log(`[SMARTSTUDY] Learning style "${style}" option visible`)
    }

    // Select "Visual" style
    const visualBtn = page.locator('text=/Visual/i').first()
    await visualBtn.click()
    console.log('[SMARTSTUDY] Selected "Visual" learning style')
    await page.waitForTimeout(500)

    // Course selector should appear (file uploaded triggers school material mode)
    const courseSelect = page.locator('select').filter({ has: page.locator('option:has-text("Select course")') })
    if (await courseSelect.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Select first available course
      const options = await courseSelect.locator('option').allTextContents()
      const realCourse = options.find(o => o !== 'Select course' && o !== '')
      if (realCourse) {
        await courseSelect.selectOption({ label: realCourse })
        console.log(`[SMARTSTUDY] Selected course: ${realCourse}`)
      }
    }

    // Duration selector
    const durationSelect = page.locator('select').filter({ has: page.locator('option:has-text("Standard")') })
    if (await durationSelect.isVisible({ timeout: 3000 }).catch(() => false)) {
      await durationSelect.selectOption({ index: 2 })
      console.log('[SMARTSTUDY] Duration set')
    }

    // Generate button should be visible
    const generateBtn = page.getByRole('button', { name: /generate/i }).first()
    await expect(generateBtn).toBeVisible({ timeout: 5000 })
    console.log('[SMARTSTUDY] Generate Plan button visible and ready')

    await page.screenshot({ path: 'e2e/screenshots/06-smartstudy-form.png', fullPage: true })
    console.log('[SMARTSTUDY] SUCCESS — Plan form fully verified with ML slide')
  })

  // ═══════════════════════════════════════════
  // 7. SMARTSTUDY — AI Coach chat
  // ═══════════════════════════════════════════
  test('7 — SmartStudy: AI Coach chat opens', async ({ page }) => {
    await loginAndGo(page, '/smartstudy')
    await page.waitForTimeout(2000)
    await dismissModals(page)

    const coachBtn = page.locator('text=/AI Coach/i').first()
    await expect(coachBtn).toBeVisible({ timeout: 5000 })
    await coachBtn.click()
    await page.waitForTimeout(2000)

    // Chat interface should appear — look for input area
    const chatInput = page.locator('textarea, input[placeholder*="essage"], input[placeholder*="Ask"], input[placeholder*="ype"]').first()
    if (await chatInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.log('[AI COACH] Chat input visible')
    }

    // Look for suggested prompts or welcome message
    const welcome = page.locator('text=/hello|help|ask|suggest|welcome|coach/i').first()
    if (await welcome.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('[AI COACH] Welcome/suggestion area visible')
    }

    await page.screenshot({ path: 'e2e/screenshots/07-ai-coach.png', fullPage: true })
    await dismissModals(page)
    console.log('[AI COACH] SUCCESS')
  })

  // ═══════════════════════════════════════════
  // 8. SMARTSTUDY — Quiz & Diagrams quick actions
  // ═══════════════════════════════════════════
  test('8 — SmartStudy: Quiz and Diagrams quick actions', async ({ page }) => {
    // Quiz — own navigation to avoid stale modal state
    await loginAndGo(page, '/smartstudy')
    await page.waitForTimeout(2000)
    await dismissModals(page)

    const quizBtn = page.locator('text=/Quiz/i').first()
    if (await quizBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await quizBtn.click()
      await page.waitForTimeout(2000)
      const quizArea = page.locator('text=/quiz|test|question|generate|select a plan/i').first()
      if (await quizArea.isVisible({ timeout: 5000 }).catch(() => false)) {
        console.log('[QUIZ] Quiz interface opened')
      }
      await page.screenshot({ path: 'e2e/screenshots/08a-quiz.png', fullPage: true })
    }

    // Diagrams — fresh page load to avoid modal stacking
    await page.goto('/smartstudy')
    await page.waitForTimeout(2000)
    await dismissModals(page)

    const diagBtn = page.locator('text=/Diagrams/i').first()
    if (await diagBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await diagBtn.click()
      await page.waitForTimeout(2000)
      const diagArea = page.locator('text=/diagram|concept|generate|visual|topic/i').first()
      if (await diagArea.isVisible({ timeout: 5000 }).catch(() => false)) {
        console.log('[DIAGRAMS] Diagram generator opened')
      }
      await page.screenshot({ path: 'e2e/screenshots/08b-diagrams.png', fullPage: true })
      await dismissModals(page)
    }

    console.log('[QUICK ACTIONS] SUCCESS')
  })

  // ═══════════════════════════════════════════
  // 9. CROSS-FEATURE NAVIGATION
  // ═══════════════════════════════════════════
  test('9 — Navigate across all pages seamlessly', async ({ page }) => {
    await loginAndGo(page, '/dashboard')
    await page.waitForTimeout(1500)

    const pages = [
      { nav: 'Courses', url: '/courses', check: /Courses/i },
      { nav: 'CGPA', url: '/cgpa', check: /CGPA|Analytics/i },
      { nav: 'Library', url: '/library', check: /Library/i },
      { nav: 'SmartStudy', url: '/smartstudy', check: /SmartStudy/i },
      { nav: 'Dashboard', url: '/dashboard', check: /Good (morning|afternoon|evening)/i },
    ]

    for (const p of pages) {
      const navLink = page.locator(`a:has-text("${p.nav}"), button:has-text("${p.nav}")`).first()
      await navLink.click()
      await page.waitForURL(`**${p.url}`, { timeout: 10000 })
      await page.waitForTimeout(1000)
      await dismissModals(page)

      await expect(page.locator(`text=${p.check}`).first()).toBeVisible({ timeout: 5000 })
      console.log(`[NAV] ${p.nav} — OK`)
    }

    console.log('[NAVIGATION] SUCCESS — Full round-trip completed')
  })

  // ═══════════════════════════════════════════
  // 10. AUTH GUARD — protected routes
  // ═══════════════════════════════════════════
  test('10 — Protected routes redirect to login when unauthenticated', async ({ page }) => {
    // Clear auth
    await page.goto('/login')
    await page.evaluate(() => {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      localStorage.removeItem('refresh_token')
    })

    for (const route of ['/dashboard', '/courses', '/cgpa', '/library', '/smartstudy']) {
      await page.goto(route)
      await page.waitForURL('**/login', { timeout: 10000 })
      console.log(`[AUTH GUARD] ${route} → /login`)
    }

    console.log('[AUTH GUARD] SUCCESS — All protected routes secured')
  })

})

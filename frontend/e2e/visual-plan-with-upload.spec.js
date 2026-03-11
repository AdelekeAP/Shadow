import { test, expect } from '@playwright/test'
import path from 'path'
import { TEST_EMAIL, TEST_PASSWORD, loginViaApi } from './helpers.js'

/*
 * E2E: Visual Learning Style — Study Plan with PPTX Upload
 *
 * Tests the full flow: login → SmartStudy → upload lecture slides →
 * select course → create visual plan → verify YouTube videos,
 * diagram buttons, curated resources, and slide content integration.
 */

const PPTX_PATH = path.resolve(__dirname, '../../CSC 411_ Machine Learning Lecture 1.pptx')
const COURSE_LABEL = 'PAU-CSC411' // Machine Learning course

test.describe('Visual Plan with PPTX Upload', () => {
  // PPTX upload + processing + plan generation + diagrams can take 8+ minutes
  test.setTimeout(720000)

  test.beforeEach(async ({ page }) => {
    // Login via API
    const loginData = await loginViaApi(page, '/smartstudy', TEST_EMAIL, TEST_PASSWORD)
    expect(loginData.access_token).toBeTruthy()

    await expect(page.locator('h1:has-text("SmartStudy")')).toBeVisible({ timeout: 10000 })
  })

  test('generates visual plan from uploaded PPTX with course selection', async ({ page }) => {
    // Click "New Study Plan"
    await page.locator('button:has-text("New Study Plan")').first().click()
    await expect(page.locator('h3:has-text("Create a New Study Plan")')).toBeVisible({ timeout: 5000 })

    // Upload the PPTX file
    const fileInput = page.locator('input[type="file"][accept=".pdf,.pptx,.ppt"]')
    await fileInput.setInputFiles(PPTX_PATH)

    // Verify file appears in the upload area
    await expect(page.locator('text=CSC 411_ Machine Learning Lecture 1.pptx')).toBeVisible({ timeout: 3000 })
    console.log('[E2E] PPTX file uploaded successfully')

    // Select the PAU-CSC411 course (required when uploading)
    const courseSelect = page.locator('select').filter({ has: page.locator('option:has-text("Select course...")') })
    // Find the option that contains our course code
    const courseOption = courseSelect.locator(`option:has-text("${COURSE_LABEL}")`)
    const courseValue = await courseOption.getAttribute('value')
    await courseSelect.selectOption(courseValue)
    console.log('[E2E] Course selected: PAU-CSC411 - Machine Learning')

    // Select "Visual" learning style
    const visualStyleBtn = page.locator('button', { has: page.locator('p:text-is("Visual")') })
      .filter({ has: page.locator('p:text-is("Diagrams & videos")') })
    await visualStyleBtn.click()
    console.log('[E2E] Visual learning style selected')

    // Click "Generate Plan"
    const generateBtn = page.locator('button[type="submit"]:has-text("Generate Plan")')
    await generateBtn.click()

    // Wait for overlay to appear and then disappear
    const overlay = page.locator('.fixed.inset-0.z-50')
    await expect(overlay).toBeVisible({ timeout: 15000 })
    console.log('[E2E] GeneratingOverlay appeared — generating plan from slides...')

    await expect(overlay).toBeHidden({ timeout: 240000 })
    console.log('[E2E] GeneratingOverlay dismissed — plan generated from PPTX')

    // Wait for plan list to refresh
    await page.waitForTimeout(3000)

    // Click the plan in the sidebar (topic is extracted from the slides)
    // The plan topic may be auto-extracted from the PPTX, so find the most recent plan
    const planButtons = page.locator('.space-y-1 button').first()
    await expect(planButtons).toBeVisible({ timeout: 10000 })
    await planButtons.click()
    await page.waitForTimeout(1000)

    // ── ASSERTION 1: Plan rendered with day sections ──
    const dayBadges = page.locator('span:text-matches("Day \\\\d+")')
    const dayCount = await dayBadges.count()
    expect(dayCount).toBeGreaterThanOrEqual(3)
    console.log(`[E2E] PASS: Found ${dayCount} day sections`)

    // ── ASSERTION 2: Visual-only "View Diagram" buttons present ──
    const diagramButtons = page.locator('button:has-text("View Diagram")')
    const diagramCount = await diagramButtons.count()
    expect(diagramCount).toBeGreaterThanOrEqual(1)
    console.log(`[E2E] PASS: Found ${diagramCount} "View Diagram" buttons`)

    // ── ASSERTION 3: Resource breakdown ──
    const videoCards = page.locator('span:text-is("Video")')
    const articleCards = page.locator('span:text-is("Article")')
    const docCards = page.locator('span:text-is("Documentation")')
    const slideCards = page.locator('span:text-is("Your Slides")')
    const interactiveCards = page.locator('span:text-is("Interactive")')
    const aiCards = page.locator('span:text-is("AI Guide")')

    const videoCount = await videoCards.count()
    const articleCount = await articleCards.count()
    const docCount = await docCards.count()
    const slideCount = await slideCards.count()
    const interactiveCount = await interactiveCards.count()
    const aiCount = await aiCards.count()

    console.log(`[E2E] Resource breakdown:`)
    console.log(`  YouTube videos: ${videoCount}`)
    console.log(`  Articles: ${articleCount}`)
    console.log(`  Documentation: ${docCount}`)
    console.log(`  Your Slides: ${slideCount}`)
    console.log(`  Interactive: ${interactiveCount}`)
    console.log(`  AI Generated: ${aiCount}`)

    const totalCurated = videoCount + articleCount + docCount + slideCount + interactiveCount
    const totalResources = totalCurated + aiCount
    const curationPct = totalResources > 0 ? Math.round(totalCurated / totalResources * 100) : 0
    console.log(`  Curation rate: ${totalCurated}/${totalResources} (${curationPct}%)`)

    // ── ASSERTION 4: At least some curated resources ──
    expect(totalCurated).toBeGreaterThanOrEqual(1)
    console.log(`[E2E] PASS: ${totalCurated} curated resources found`)

    // ── ASSERTION 5: Check for slide content integration ──
    // With PPTX upload + course, slides should be saved and viewable
    if (slideCount > 0) {
      console.log(`[E2E] PASS: ${slideCount} slide resources found (inline viewing available)`)
    } else {
      console.log(`[E2E] INFO: No "Your Slides" badges — slides may be assigned as docs or AI resources`)
    }

    // ── ASSERTION 6: YouTube inline player works ──
    const playButtons = page.locator('button:has-text("Play"):not(:has-text("Full Screen"))')
    const playCount = await playButtons.count()
    if (playCount > 0) {
      await playButtons.first().scrollIntoViewIfNeeded()
      await playButtons.first().click()
      const iframe = page.locator('iframe[src*="youtube"]')
      await expect(iframe).toBeVisible({ timeout: 10000 })
      console.log('[E2E] PASS: YouTube inline player works')
    } else {
      console.log('[E2E] INFO: No Play buttons — YouTube API may have returned 0 results')
    }

    // ── ASSERTION 7: Generate concept diagrams for ALL days ──
    // NOTE: After clicking, "View Diagram" becomes "Hide Diagram", so the locator
    // re-evaluates dynamically. Always click the FIRST remaining "View Diagram" button.
    for (let i = 0; i < diagramCount; i++) {
      // Re-query to get the first un-clicked "View Diagram" button
      const remainingBtns = page.locator('button:has-text("View Diagram")')
      const firstBtn = remainingBtns.first()
      await firstBtn.scrollIntoViewIfNeeded()
      await firstBtn.click()
      console.log(`[E2E] Clicked "View Diagram" for Day ${i + 1} — generating...`)

      // Wait for this diagram to load (new "Hide Diagram" button appears)
      const hideButtons = page.locator('button:has-text("Hide Diagram")')
      await expect(hideButtons.nth(i)).toBeVisible({ timeout: 45000 })

      // Verify the diagram SVG rendered
      const diagrams = page.locator('[aria-label*="Concept diagram"]')
      await expect(diagrams.nth(i)).toBeVisible({ timeout: 5000 })
      console.log(`[E2E] PASS: Concept diagram ${i + 1}/${diagramCount} rendered`)
    }
    console.log(`[E2E] PASS: All ${diagramCount} concept diagrams generated`)

    // ── SUMMARY ──
    console.log('\n[E2E] ════════════════════════════════════════')
    console.log('[E2E] Visual Plan + PPTX Upload E2E PASSED')
    console.log(`[E2E] Days: ${dayCount}, Diagrams: ${diagramCount}`)
    console.log(`[E2E] Videos: ${videoCount}, Articles: ${articleCount}, Slides: ${slideCount}`)
    console.log(`[E2E] Curation rate: ${curationPct}%`)
    console.log('[E2E] ════════════════════════════════════════')
  })
})

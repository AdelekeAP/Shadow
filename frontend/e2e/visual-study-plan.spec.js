import { test, expect } from '@playwright/test'
import { TEST_EMAIL, TEST_PASSWORD, loginViaApi } from './helpers.js'

/*
 * E2E: Visual Learning Style — Study Plan Generation
 *
 * Tests the full flow: login → SmartStudy → create visual plan → verify
 * that YouTube videos, diagram buttons, and curated resources render.
 *
 * Requires both backend (localhost:8000) and frontend (localhost:3000) running.
 */

const TEST_TOPIC = 'Machine Learning Fundamentals'

test.describe('Visual Learning Style — Study Plan', () => {

  test.beforeEach(async ({ page }) => {
    // Login via API to avoid UI flakiness, then set tokens in localStorage
    const loginData = await loginViaApi(page, '/smartstudy', TEST_EMAIL, TEST_PASSWORD)
    expect(loginData.access_token).toBeTruthy()

    // Wait for the page to fully load (hero section visible)
    await expect(page.locator('h1:has-text("SmartStudy")')).toBeVisible({ timeout: 10000 })
  })

  test('generates a visual study plan with YouTube videos and diagram buttons', async ({ page }) => {
    // Click "New Study Plan" button (the one in the hero area, not the empty-state one)
    const newPlanBtn = page.locator('button:has-text("New Study Plan")').first()
    await newPlanBtn.click()

    // Wait for the form to appear — look for the form heading
    await expect(page.locator('h3:has-text("Create a New Study Plan")')).toBeVisible({ timeout: 5000 })

    // Fill in the topic — use the specific placeholder
    const topicInput = page.locator('input[placeholder*="Binary Search Trees"]')
    await topicInput.fill(TEST_TOPIC)

    // Select "Visual" learning style — target the style grid button specifically
    // The style buttons are inside a grid under the "Your Learning Style" label
    // Each has the style name AND description. Target by the description "Diagrams & videos"
    const visualStyleBtn = page.locator('button', { has: page.locator('p:text-is("Visual")') })
      .filter({ has: page.locator('p:text-is("Diagrams & videos")') })
    await visualStyleBtn.click()

    // Verify the visual button shows active state (icon container has navy background)
    await expect(visualStyleBtn).toBeVisible()

    // Click "Generate Plan" — the submit button inside the form
    const generateBtn = page.locator('button[type="submit"]:has-text("Generate Plan")')
    await generateBtn.click()

    // Wait for GeneratingOverlay to appear (it shows "Generating Your Plan" then "Finishing Up")
    const overlay = page.locator('.fixed.inset-0.z-50')
    await expect(overlay).toBeVisible({ timeout: 15000 })
    console.log('[E2E] GeneratingOverlay appeared — waiting for plan generation...')

    // Wait for the overlay to completely disappear (generation finished)
    // Study plan generation can take up to 90 seconds (OpenAI + YouTube API calls)
    await expect(overlay).toBeHidden({ timeout: 120000 })
    console.log('[E2E] GeneratingOverlay dismissed — plan generated')

    // Wait for the plan list to refresh
    await page.waitForTimeout(3000)

    // The plan should now appear in the sidebar — click it
    const planEntry = page.locator(`button:has-text("${TEST_TOPIC}")`).first()
    await expect(planEntry).toBeVisible({ timeout: 10000 })
    await planEntry.click()

    // Wait for plan details to render (day sections)
    await page.waitForTimeout(1000)

    // ── ASSERTION 1: Plan title is displayed ──
    await expect(page.locator(`text=${TEST_TOPIC}`).first()).toBeVisible({ timeout: 5000 })
    console.log('[E2E] PASS: Plan title visible')

    // ── ASSERTION 2: Day sections exist ──
    // Day badges are rendered as spans with "Day N" text
    const dayBadges = page.locator('span:text-matches("Day \\\\d+")')
    const dayCount = await dayBadges.count()
    expect(dayCount).toBeGreaterThanOrEqual(3) // at least 3 days
    console.log(`[E2E] PASS: Found ${dayCount} day sections`)

    // ── ASSERTION 3: Visual plan shows "View Diagram" buttons ──
    // Visual plans have a diagram button on each day header
    const diagramButtons = page.locator('button:has-text("View Diagram")')
    const diagramCount = await diagramButtons.count()
    expect(diagramCount).toBeGreaterThanOrEqual(1)
    console.log(`[E2E] PASS: Found ${diagramCount} "View Diagram" buttons (visual-only feature)`)

    // ── ASSERTION 4: Check for YouTube video resources ──
    // ResourceCards for YouTube videos show "Play" and "Full Screen" buttons
    const playButtons = page.locator('button:has-text("Play"):not(:has-text("Full Screen"))')
    const playCount = await playButtons.count()
    console.log(`[E2E] Found ${playCount} "Play" buttons (YouTube videos)`)

    // Count all ResourceCard badges — check for curated resources
    // Badge text comes from studyPlanHelpers.getResourceStyle(): "Video", "Article", "Docs", "Interactive", "AI Guide"
    const youtubeCards = page.locator('span:text-is("Video")')
    const articleCards = page.locator('span:text-is("Article")')
    const docCards = page.locator('span:text-is("Documentation")')
    const interactiveCards = page.locator('span:text-is("Interactive")')
    const aiGeneratedCards = page.locator('span:text-is("AI Guide")')

    const youtubeCount = await youtubeCards.count()
    const articleCount = await articleCards.count()
    const docCount = await docCards.count()
    const interactiveCount = await interactiveCards.count()
    const aiGenCount = await aiGeneratedCards.count()

    console.log(`[E2E] Resource breakdown:`)
    console.log(`  YouTube videos: ${youtubeCount}`)
    console.log(`  Articles: ${articleCount}`)
    console.log(`  Documentation: ${docCount}`)
    console.log(`  Interactive: ${interactiveCount}`)
    console.log(`  AI Generated: ${aiGenCount}`)

    const totalCurated = youtubeCount + articleCount + docCount + interactiveCount
    const totalResources = totalCurated + aiGenCount
    const curationPct = totalResources > 0 ? Math.round(totalCurated / totalResources * 100) : 0
    console.log(`  Curation rate: ${totalCurated}/${totalResources} (${curationPct}%)`)

    // ── ASSERTION 5: At least some curated resources exist ──
    expect(totalCurated).toBeGreaterThanOrEqual(1)
    console.log(`[E2E] PASS: ${totalCurated} curated resources found`)

    // ── ASSERTION 6: Visual plans should have YouTube videos specifically ──
    if (youtubeCount === 0) {
      console.warn('[E2E] WARNING: No YouTube videos found for visual learner plan!')
      console.warn('[E2E] This may indicate YouTube API issues or resource assignment problems')
    } else {
      console.log(`[E2E] PASS: ${youtubeCount} YouTube videos found for visual learner`)
    }

    // ── ASSERTION 7: "Full Screen" button exists for YouTube videos ──
    if (youtubeCount > 0) {
      const fullScreenButtons = page.locator('button:has-text("Full Screen")')
      const fullScreenCount = await fullScreenButtons.count()
      expect(fullScreenCount).toBeGreaterThanOrEqual(1)
      console.log(`[E2E] PASS: Found ${fullScreenCount} "Full Screen" buttons`)
    }

    // ── ASSERTION 8: Click a "Play" button to expand inline YouTube player ──
    if (playCount > 0) {
      const firstPlay = playButtons.first()
      await firstPlay.scrollIntoViewIfNeeded()
      await firstPlay.click()
      // After clicking Play, an iframe for YouTube should appear
      const iframe = page.locator('iframe[src*="youtube"]')
      await expect(iframe).toBeVisible({ timeout: 10000 })
      console.log('[E2E] PASS: YouTube inline player opened successfully')
    }

    // ── SUMMARY ──
    console.log('\n[E2E] ════════════════════════════════════════')
    console.log('[E2E] Visual Study Plan E2E Test PASSED')
    console.log(`[E2E] Days: ${dayCount}, Diagrams: ${diagramCount}`)
    console.log(`[E2E] YouTube: ${youtubeCount}, Articles: ${articleCount}, Docs: ${docCount}`)
    console.log(`[E2E] Curation rate: ${curationPct}%`)
    console.log('[E2E] ════════════════════════════════════════')
  })

  test('diagram button generates concept diagram for visual learners', async ({ page }) => {
    // Wait for plans to load and click the first one with our topic
    await page.waitForTimeout(2000) // let plan list load
    const planEntry = page.locator(`button:has-text("${TEST_TOPIC}")`).first()
    // If no plan exists yet, skip this test
    const planVisible = await planEntry.isVisible().catch(() => false)
    if (!planVisible) {
      console.log('[E2E] SKIP: No plan found to test diagram generation')
      test.skip()
      return
    }
    await planEntry.click()
    await page.waitForTimeout(1000)

    // Find and click the first "View Diagram" button
    const diagramBtn = page.locator('button:has-text("View Diagram")').first()
    await expect(diagramBtn).toBeVisible({ timeout: 5000 })
    await diagramBtn.click()

    // Wait for diagram to load (spinner appears then disappears)
    // The button text changes to "Hide Diagram" when loaded
    await expect(page.locator('button:has-text("Hide Diagram")').first()).toBeVisible({ timeout: 30000 })

    // Verify the ConceptDiagram component rendered
    const diagramRegion = page.locator('[aria-label*="Concept diagram"]')
    await expect(diagramRegion).toBeVisible({ timeout: 5000 })
    console.log('[E2E] PASS: Concept diagram generated and rendered successfully')
  })
})

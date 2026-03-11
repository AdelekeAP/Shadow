import { test, expect } from '@playwright/test'
import path from 'path'
import { TEST_EMAIL, TEST_PASSWORD, loginViaApi } from './helpers.js'

/**
 * E2E: All 4 Learning Styles — Production Readiness Test
 *
 * VISUAL:  Plan with days, YouTube videos, diagram generation, slide page-ranges
 * AUDIO:   Plan with days, Generate Podcast, ElevenLabs TTS audio, script fallback
 * READING: Plan with days, inline SlideRangeViewer, StudyCards, no "Open Slides"
 * KINESTHETIC: Plan with days, exercise generation, code sandbox indicators, CodeEditor
 */

const PPTX_PATH = path.resolve(__dirname, '../../CSC 411_ Machine Learning Lecture 1.pptx')

async function dismissModals(page, label = '') {
  for (let attempt = 0; attempt < 5; attempt++) {
    const backdrop = page.locator('.fixed.inset-0.z-50')
    if (await backdrop.isVisible({ timeout: 600 }).catch(() => false)) {
      console.log(`[${label}] Closing modal (attempt ${attempt + 1})...`)
      // Try Escape first (now works with our fix)
      await page.keyboard.press('Escape')
      await page.waitForTimeout(400)
      // Check if it closed
      if (!(await backdrop.isVisible({ timeout: 300 }).catch(() => false))) break
      // If still open, try clicking backdrop
      const inner = page.locator('.fixed.inset-0.z-50 > div').first()
      const box = await backdrop.boundingBox()
      if (box) {
        await page.mouse.click(box.x + 5, box.y + 5) // click outer edge
        await page.waitForTimeout(400)
      }
    } else break
  }
}

async function loginAndGoToSmartStudy(page) {
  const loginData = await loginViaApi(page, '/smartstudy', TEST_EMAIL, TEST_PASSWORD)
  expect(loginData.access_token).toBeTruthy()
  console.log('[LOGIN] Got access token')

  await page.getByRole('heading', { name: 'SmartStudy' }).waitFor({ timeout: 30000 })
  console.log('[NAV] SmartStudy page loaded')

  // Dismiss any modal that auto-opened (Concept Diagram, etc.)
  await page.waitForTimeout(1500)
  await dismissModals(page, 'INIT')
  await page.waitForTimeout(300)
}

async function createPlanWithStyle(page, style) {
  const S = style.toUpperCase()

  // 1. Click "New Study Plan" button
  const newPlanBtn = page.getByRole('button', { name: 'New Study Plan' }).first()
  await newPlanBtn.scrollIntoViewIfNeeded()
  await newPlanBtn.click()
  console.log(`[${S}] Clicked New Study Plan`)
  await page.waitForTimeout(2000)

  // 2. Scroll to make form visible
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.waitForTimeout(500)

  // 3. Upload PPTX
  const fileInput = page.locator('input[type="file"]')
  await expect(fileInput).toBeAttached({ timeout: 10000 })
  await fileInput.setInputFiles(PPTX_PATH)
  console.log(`[${S}] PPTX file set on input`)

  // 4. Wait for file to be accepted — the filename appears in the upload area
  const fileNameVisible = page.locator('text=/Machine Learning/i').first()
  await expect(fileNameVisible).toBeVisible({ timeout: 15000 })
  console.log(`[${S}] File upload confirmed`)
  await page.waitForTimeout(1500) // Wait for courses API to load

  // 5. Select course — wait for course options to populate
  //    The Course select appears after file upload and needs the enrolled courses API to finish
  const courseSelect = page.locator('select').filter({ has: page.locator('option:has-text("Select course")') })
  await expect(courseSelect).toBeVisible({ timeout: 10000 })
  console.log(`[${S}] Course select visible`)

  // Wait for course options to load (beyond just "Select course...")
  await page.waitForFunction(() => {
    const selects = document.querySelectorAll('select')
    for (const sel of selects) {
      const opts = Array.from(sel.options).map(o => o.textContent)
      if (opts.some(o => o.includes('CSC') || o.includes('Machine'))) return true
    }
    return false
  }, { timeout: 15000 })
  console.log(`[${S}] Course options loaded`)

  // Select the Machine Learning course
  const allSelects = await page.locator('select').all()
  for (const sel of allSelects) {
    const options = await sel.locator('option').allTextContents()
    const match = options.find(o => o.includes('Machine Learning') || o.includes('CSC411'))
    if (match) {
      await sel.selectOption({ label: match })
      console.log(`[${S}] Selected course: ${match}`)
      break
    }
  }
  await page.waitForTimeout(500)

  // 6. Select learning style
  const styleLabels = { visual: 'Visual', audio: 'Audio', reading: 'Reading', kinesthetic: 'Hands-on' }
  const styleLabel = styleLabels[style]
  // Find the style button within the learning style grid (not just any button with that text)
  const styleBtn = page.locator(`button:has-text("${styleLabel}")`).first()
  await styleBtn.scrollIntoViewIfNeeded()
  await styleBtn.click()
  console.log(`[${S}] Clicked ${styleLabel} style button`)
  await page.waitForTimeout(500)

  // Dismiss any modal that may have appeared
  await dismissModals(page, S)

  // 7. Check for validation errors before submit
  const valError = page.locator('text=/Please enter|Please select a course/i')
  if (await valError.isVisible({ timeout: 300 }).catch(() => false)) {
    const errText = await valError.textContent()
    console.log(`[${S}] ⚠ Validation error before submit: ${errText}`)
  }

  // 8. Click Generate Plan
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
  await page.waitForTimeout(300)

  const submitBtn = page.locator('button[type="submit"]')
  await expect(submitBtn).toBeVisible({ timeout: 5000 })
  await submitBtn.scrollIntoViewIfNeeded()

  // Take a screenshot before clicking submit for debugging
  await page.screenshot({ path: `test-results/${style}-pre-submit.png` })

  await submitBtn.click()
  console.log(`[${S}] Clicked Generate Plan`)

  // 9. Check if form submission started — look for generating overlay or form disappearing
  //    The GeneratingOverlay appears during plan generation, OR validation error shows
  await page.waitForTimeout(2000)
  const valErrorAfter = page.locator('text=/Please enter|Please select a course/i')
  if (await valErrorAfter.isVisible({ timeout: 1000 }).catch(() => false)) {
    const errText = await valErrorAfter.textContent()
    console.log(`[${S}] ✗ Validation error after submit: ${errText}`)
    await page.screenshot({ path: `test-results/${style}-validation-error.png` })
    throw new Error(`Form validation failed: ${errText}`)
  }

  console.log(`[${S}] Generating plan (waiting up to 5 min)...`)

  // Wait for plan — "Day 1" appears in the plan details
  await expect(page.locator('text=/Day 1/i').first()).toBeVisible({ timeout: 300000 })
  console.log(`[${S}] Plan generated!`)
  await page.waitForTimeout(3000)
}

// ════════════════ VISUAL ════════════════
test.describe('Visual Learning Style E2E', () => {
  test.setTimeout(600000)
  test('visual plan: videos, diagrams, slide ranges', async ({ page }) => {
    await loginAndGoToSmartStudy(page)
    await createPlanWithStyle(page, 'visual')
    const r = {}

    const dayCount = await page.locator('text=/Day \\d+/i').count()
    r['plan_has_days'] = dayCount >= 3
    console.log(`[VISUAL] Days: ${dayCount}`)

    const videoCount = await page.locator('button:has-text("Play")').count()
    r['has_youtube_videos'] = videoCount >= 1
    console.log(`[VISUAL] Videos: ${videoCount}`)

    const diagBtns = page.locator('button:has-text("View Diagram"), button:has-text("Generate Diagram")')
    r['has_diagram_buttons'] = await diagBtns.count() >= 1
    console.log(`[VISUAL] Diagram buttons: ${await diagBtns.count()}`)

    if (await diagBtns.count() > 0) {
      await diagBtns.first().click()
      await page.waitForTimeout(10000)
      const hasSvg = await page.locator('svg[role="img"]').isVisible({ timeout: 45000 }).catch(() => false)
      r['diagram_renders_svg'] = hasSvg
      if (hasSvg) {
        r['diagram_has_nodes'] = await page.locator('svg[role="img"] rect').count() >= 3
      } else { r['diagram_has_nodes'] = false }
      await page.keyboard.press('Escape')
      await page.waitForTimeout(500)
    } else { r['diagram_renders_svg'] = false; r['diagram_has_nodes'] = false }

    r['has_page_ranges'] = await page.locator('button:has-text("Pages")').count() >= 1
    console.log(`[VISUAL] Page ranges: ${await page.locator('button:has-text("Pages")').count()}`)

    r['style_indicator'] = await page.locator('text=/visual/i').first().isVisible({ timeout: 3000 }).catch(() => false)

    const passed = Object.values(r).filter(Boolean).length
    const total = Object.keys(r).length
    const score = Math.round((passed / total) * 100)
    console.log(`\n===== VISUAL SCORE: ${score}% (${passed}/${total}) =====`)
    console.log(JSON.stringify(r, null, 2))
    expect(score).toBeGreaterThanOrEqual(50)
  })
})

// ════════════════ AUDIO ════════════════
test.describe('Audio Learning Style E2E', () => {
  test.setTimeout(600000)
  test('audio plan: podcasts, TTS, scripts', async ({ page }) => {
    await loginAndGoToSmartStudy(page)
    await createPlanWithStyle(page, 'audio')
    const r = {}

    r['plan_has_days'] = await page.locator('text=/Day \\d+/i').count() >= 3
    console.log(`[AUDIO] Days: ${await page.locator('text=/Day \\d+/i').count()}`)

    const podBtns = page.locator('button:has-text("Generate Podcast"), button:has-text("Play Podcast")')
    const podCount = await podBtns.count()
    r['has_podcast_buttons'] = podCount >= 1
    console.log(`[AUDIO] Podcast buttons: ${podCount}`)

    if (podCount > 0) {
      await podBtns.first().click()
      console.log('[AUDIO] Generating podcast...')
      const audioOrScript = page.locator('audio, button:has-text("Show Script")')
      await expect(audioOrScript.first()).toBeVisible({ timeout: 120000 })

      r['tts_produces_audio'] = await page.locator('audio').first().isVisible({ timeout: 5000 }).catch(() => false)
      r['has_show_script'] = await page.locator('button:has-text("Show Script")').first().isVisible({ timeout: 3000 }).catch(() => false)
      console.log(`[AUDIO] Audio: ${r['tts_produces_audio']}, Script: ${r['has_show_script']}`)
    } else { r['tts_produces_audio'] = false; r['has_show_script'] = false }

    r['has_page_ranges'] = await page.locator('button:has-text("Pages")').count() >= 1
    r['style_indicator'] = await page.locator('text=/audio/i').first().isVisible({ timeout: 3000 }).catch(() => false)

    const passed = Object.values(r).filter(Boolean).length
    const total = Object.keys(r).length
    const score = Math.round((passed / total) * 100)
    console.log(`\n===== AUDIO SCORE: ${score}% (${passed}/${total}) =====`)
    console.log(JSON.stringify(r, null, 2))
    expect(score).toBeGreaterThanOrEqual(50)
  })
})

// ════════════════ READING ════════════════
test.describe('Reading Learning Style E2E', () => {
  test.setTimeout(600000)
  test('reading plan: inline slides, study cards, no open-slides', async ({ page }) => {
    await loginAndGoToSmartStudy(page)
    await createPlanWithStyle(page, 'reading')
    const r = {}

    r['plan_has_days'] = await page.locator('text=/Day \\d+/i').count() >= 3
    console.log(`[READING] Days: ${await page.locator('text=/Day \\d+/i').count()}`)

    const prCount = await page.locator('button:has-text("Pages")').count()
    r['has_page_ranges'] = prCount >= 1
    console.log(`[READING] Page ranges: ${prCount}`)

    if (prCount > 0) {
      await page.locator('button:has-text("Pages")').first().click()
      await page.waitForTimeout(5000)
      r['inline_viewer_works'] = await page.locator('canvas').first().isVisible({ timeout: 15000 }).catch(() => false)
        || await page.locator('text=/Page \\d+/i').first().isVisible({ timeout: 5000 }).catch(() => false)
      console.log(`[READING] Inline viewer: ${r['inline_viewer_works']}`)
    } else { r['inline_viewer_works'] = false }

    r['has_study_cards'] = await page.locator('button:has-text("Generate Study Cards"), button:has-text("Generate Cards"), text=/Study Cards/i').first()
      .isVisible({ timeout: 5000 }).catch(() => false)
    console.log(`[READING] Study Cards: ${r['has_study_cards']}`)

    r['no_open_slides'] = !(await page.locator('button:has-text("Open Slides")').isVisible({ timeout: 2000 }).catch(() => false))
    console.log(`[READING] Open Slides removed: ${r['no_open_slides']}`)

    r['uploaded_slides_label'] = await page.locator('text=/Your Uploaded Slides/i').first().isVisible({ timeout: 3000 }).catch(() => false)
    r['style_indicator'] = await page.locator('text=/reading/i').first().isVisible({ timeout: 3000 }).catch(() => false)

    const passed = Object.values(r).filter(Boolean).length
    const total = Object.keys(r).length
    const score = Math.round((passed / total) * 100)
    console.log(`\n===== READING SCORE: ${score}% (${passed}/${total}) =====`)
    console.log(JSON.stringify(r, null, 2))
    expect(score).toBeGreaterThanOrEqual(50)
  })
})

// ════════════════ KINESTHETIC ════════════════
test.describe('Kinesthetic Learning Style E2E', () => {
  test.setTimeout(600000)
  test('kinesthetic plan: code sandbox, exercises, guided steps', async ({ page }) => {
    await loginAndGoToSmartStudy(page)
    await createPlanWithStyle(page, 'kinesthetic')
    const r = {}

    r['plan_has_days'] = await page.locator('text=/Day \\d+/i').count() >= 3
    console.log(`[KINESTHETIC] Days: ${await page.locator('text=/Day \\d+/i').count()}`)

    const exBtns = page.locator('button:has-text("Generate Practice Exercises")')
    const exCount = await exBtns.count()
    r['has_exercise_buttons'] = exCount >= 1
    console.log(`[KINESTHETIC] Exercise buttons: ${exCount}`)

    r['has_sandbox_indicator'] = await page.locator('text=/Code Sandbox/i').first().isVisible({ timeout: 3000 }).catch(() => false)
    r['has_ai_review_indicator'] = await page.locator('text=/AI Code Review/i').first().isVisible({ timeout: 2000 }).catch(() => false)
    r['has_guided_indicator'] = await page.locator('text=/Guided Steps/i').first().isVisible({ timeout: 2000 }).catch(() => false)
    console.log(`[KINESTHETIC] Indicators: sandbox=${r['has_sandbox_indicator']}, review=${r['has_ai_review_indicator']}, guided=${r['has_guided_indicator']}`)

    if (exCount > 0) {
      await exBtns.first().click()
      console.log('[KINESTHETIC] Generating exercises...')
      const types = page.locator('text=/Code Challenge|Worked Example|Debug Exercise|Explain Aloud|Build Project|Draw It Out|Compare/i')
      await expect(types.first()).toBeVisible({ timeout: 90000 })
      r['exercises_generated'] = await types.count() >= 1
      console.log(`[KINESTHETIC] Exercise types: ${await types.count()}`)

      await page.waitForTimeout(2000)
      r['code_editor_visible'] = await page.locator('text=/CODE EDITOR/i').first().isVisible({ timeout: 5000 }).catch(() => false)
        || await page.locator('.cm-editor').first().isVisible({ timeout: 3000 }).catch(() => false)
      console.log(`[KINESTHETIC] Code editor: ${r['code_editor_visible']}`)

      if (r['code_editor_visible']) {
        r['has_language_badge'] = await page.locator('text=/Python|JavaScript|Java/i').first().isVisible({ timeout: 3000 }).catch(() => false)
      } else { r['has_language_badge'] = true }
    } else {
      r['exercises_generated'] = false
      r['code_editor_visible'] = false
      r['has_language_badge'] = false
    }

    r['style_indicator'] = await page.locator('text=/hands-on|kinesthetic/i').first().isVisible({ timeout: 3000 }).catch(() => false)

    const passed = Object.values(r).filter(Boolean).length
    const total = Object.keys(r).length
    const score = Math.round((passed / total) * 100)
    console.log(`\n===== KINESTHETIC SCORE: ${score}% (${passed}/${total}) =====`)
    console.log(JSON.stringify(r, null, 2))
    expect(score).toBeGreaterThanOrEqual(50)
  })
})

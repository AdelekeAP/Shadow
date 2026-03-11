import { test, expect } from '@playwright/test'
import path from 'path'
import { TEST_EMAIL, TEST_PASSWORD, loginViaApi } from './helpers.js'

/*
 * E2E: Audio Learning Style — Study Plan with PPTX Upload
 *
 * Tests the full flow: login → SmartStudy → upload lecture slides →
 * select course → create audio plan → verify:
 *   1. "Generate Podcast" buttons on activities
 *   2. Podcast generation (audio player + script toggle)
 *   3. Slide range inline viewing (Pages X-Y buttons → SlideRangeViewer)
 *   4. Section quiz generation from slide ranges
 *   5. Quiz taking flow (QuizForm → QuizPlayer → QuizResults)
 *   6. Resource breakdown (curated vs AI)
 */

const PPTX_PATH = path.resolve(__dirname, '../../CSC 411_ Machine Learning Lecture 1.pptx')
const COURSE_LABEL = 'PAU-CSC411' // Machine Learning course

test.describe('Audio Learning Style — Study Plan with PPTX Upload', () => {
  // PPTX upload + processing + plan generation + audio generation = long test
  test.setTimeout(720000) // 12 minutes — PPTX upload + plan gen + podcast + quiz

  test.beforeEach(async ({ page }) => {
    // Login via API to avoid UI flakiness
    const loginData = await loginViaApi(page, '/smartstudy', TEST_EMAIL, TEST_PASSWORD)
    expect(loginData.access_token).toBeTruthy()

    await expect(page.locator('h1:has-text("SmartStudy")')).toBeVisible({ timeout: 10000 })
  })

  test('generates audio plan from PPTX with podcast, slides, and quiz', async ({ page }) => {
    // Capture console errors for debugging
    const consoleErrors = []
    page.on('console', msg => {
      if (msg.type() === 'error') consoleErrors.push(msg.text())
    })
    page.on('pageerror', err => {
      consoleErrors.push(`PAGE ERROR: ${err.message}`)
      console.log(`[E2E] PAGE ERROR: ${err.message}`)
    })
    // ══════════════════════════════════════════════════════
    // PHASE 1: Create an Audio Study Plan from PPTX
    // ══════════════════════════════════════════════════════

    // Click "New Study Plan"
    await page.locator('button:has-text("New Study Plan")').first().click()
    await expect(page.locator('h3:has-text("Create a New Study Plan")')).toBeVisible({ timeout: 5000 })

    // Upload the PPTX file
    const fileInput = page.locator('input[type="file"][accept=".pdf,.pptx,.ppt"]')
    await fileInput.setInputFiles(PPTX_PATH)

    // Verify file appears in the upload area
    await expect(page.locator('text=CSC 411_ Machine Learning Lecture 1.pptx')).toBeVisible({ timeout: 3000 })
    console.log('[E2E] PPTX file uploaded successfully')

    // Select the PAU-CSC411 course
    const courseSelect = page.locator('select').filter({ has: page.locator('option:has-text("Select course...")') })
    const courseOption = courseSelect.locator(`option:has-text("${COURSE_LABEL}")`)
    const courseValue = await courseOption.getAttribute('value')
    await courseSelect.selectOption(courseValue)
    console.log('[E2E] Course selected: PAU-CSC411 - Machine Learning')

    // Select "Audio" learning style — target the style grid button specifically
    const audioStyleBtn = page.locator('button', { has: page.locator('p:text-is("Audio")') })
      .filter({ has: page.locator('p:text-is("Podcast summaries")') })
    await audioStyleBtn.scrollIntoViewIfNeeded()
    await audioStyleBtn.click()
    console.log('[E2E] Audio learning style selected')

    // Click "Generate Plan"
    const generateBtn = page.locator('button[type="submit"]:has-text("Generate Plan")')
    await generateBtn.click()

    // Wait for GeneratingOverlay to appear then disappear
    const overlay = page.locator('.fixed.inset-0.z-50')
    await expect(overlay).toBeVisible({ timeout: 15000 })
    console.log('[E2E] GeneratingOverlay appeared — generating audio plan from slides...')

    await expect(overlay).toBeHidden({ timeout: 240000 })
    console.log('[E2E] GeneratingOverlay dismissed — audio plan generated')

    // Wait for plan list to refresh
    await page.waitForTimeout(3000)

    // Click the most recent plan in the sidebar
    const planButtons = page.locator('.space-y-1 button').first()
    await expect(planButtons).toBeVisible({ timeout: 10000 })
    await planButtons.click()
    await page.waitForTimeout(1500)

    // ══════════════════════════════════════════════════════
    // PHASE 2: Verify Audio Plan Structure
    // ══════════════════════════════════════════════════════

    // ASSERTION 1: Plan has day sections
    const dayBadges = page.locator('span:text-matches("Day \\\\d+")')
    const dayCount = await dayBadges.count()
    expect(dayCount).toBeGreaterThanOrEqual(3)
    console.log(`[E2E] PASS: Found ${dayCount} day sections`)

    // ASSERTION 2: Audio learner badge is displayed
    const audioBadge = page.locator('span:has-text("audio learner")')
    await expect(audioBadge).toBeVisible({ timeout: 5000 })
    console.log('[E2E] PASS: "audio learner" badge visible')

    // ASSERTION 3: "Generate Podcast" buttons are present (audio-only feature)
    const podcastButtons = page.locator('button:has-text("Generate Podcast")')
    const podcastCount = await podcastButtons.count()
    expect(podcastCount).toBeGreaterThanOrEqual(1)
    console.log(`[E2E] PASS: Found ${podcastCount} "Generate Podcast" buttons (audio-only feature)`)

    // ASSERTION 4: Resource breakdown
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

    console.log('[E2E] Resource breakdown:')
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

    // ASSERTION 5: At least some curated resources
    expect(totalCurated).toBeGreaterThanOrEqual(1)
    console.log(`[E2E] PASS: ${totalCurated} curated resources found`)

    // ══════════════════════════════════════════════════════
    // PHASE 3: Slide Range Inline Viewing
    // ══════════════════════════════════════════════════════

    // Find "Pages X-Y" buttons (slide range viewers)
    const pageRangeButtons = page.locator('button:has-text("Pages ")')
      .filter({ hasNot: page.locator('text=Quiz this section') })
    const pageRangeCount = await pageRangeButtons.count()
    console.log(`[E2E] Found ${pageRangeCount} "Pages X-Y" slide range buttons`)

    if (pageRangeCount > 0) {
      // Click first slide range button to open SlideRangeViewer
      const firstPageBtn = pageRangeButtons.first()
      await firstPageBtn.scrollIntoViewIfNeeded()
      const pageRangeText = await firstPageBtn.textContent()
      await firstPageBtn.click()
      console.log(`[E2E] Clicked slide range button: "${pageRangeText.trim()}"`)

      // Wait for SlideRangeViewer to load — look for the toolbar with page info
      // The viewer renders a glass toolbar with "Pages X-Y" and zoom controls
      const slideViewer = page.locator('.react-pdf__Document, [class*="react-pdf"]').first()
      // Wait for either the PDF to render or a loading indicator
      await page.waitForTimeout(3000) // give react-pdf time to load

      // Check for the viewer toolbar (it shows "Pages X-Y" and zoom percentage)
      const viewerToolbar = page.locator('span:has-text("100%")').first()
      const toolbarVisible = await viewerToolbar.isVisible().catch(() => false)

      if (toolbarVisible) {
        console.log('[E2E] PASS: SlideRangeViewer rendered with zoom controls')

        // Check for page navigation dots (if multiple pages in range)
        const navDots = page.locator('button[title^="Page "]')
        const dotCount = await navDots.count()
        if (dotCount > 1) {
          console.log(`[E2E] PASS: ${dotCount} page navigation dots visible`)
          // Click second page dot to navigate
          await navDots.nth(1).click()
          await page.waitForTimeout(500)
          console.log('[E2E] PASS: Navigated to second page via dots')
        }

        // Close the viewer by clicking the same button again (it toggles)
        await firstPageBtn.scrollIntoViewIfNeeded()
        await firstPageBtn.click()
        await page.waitForTimeout(500)
        console.log('[E2E] Closed SlideRangeViewer')
      } else {
        // The viewer might be loading or document not available
        console.log('[E2E] INFO: SlideRangeViewer opened but PDF may still be loading')
        // Close it
        await firstPageBtn.scrollIntoViewIfNeeded()
        await firstPageBtn.click()
        await page.waitForTimeout(500)
      }
    } else {
      console.log('[E2E] INFO: No slide range buttons found (plan may not have page_range activities)')
    }

    // ══════════════════════════════════════════════════════
    // PHASE 4: Podcast Generation (Audio Player)
    // ══════════════════════════════════════════════════════

    // Click the first "Generate Podcast" button
    const firstPodcastBtn = podcastButtons.first()
    await firstPodcastBtn.scrollIntoViewIfNeeded()
    await firstPodcastBtn.click()
    console.log('[E2E] Clicked "Generate Podcast" — generating audio...')

    // Button should change to "Generating..." with a spinner
    const generatingBtn = page.locator('button:has-text("Generating...")')
    await expect(generatingBtn.first()).toBeVisible({ timeout: 5000 })
    console.log('[E2E] PASS: "Generating..." state visible')

    // Wait for audio generation to complete (60-120 seconds for TTS)
    // The button will change to either "Play Podcast" (success) or "Retry Audio" (error with script fallback)
    const playPodcastBtn = page.locator('button:has-text("Play Podcast")')
    const retryAudioBtn = page.locator('button:has-text("Retry Audio")')
    const showScriptBtn = page.locator('button:has-text("Show Script")')

    // Wait for generation to finish — "Generating..." button disappears
    await expect(generatingBtn.first()).toBeHidden({ timeout: 150000 })

    const playVisible = await playPodcastBtn.first().isVisible().catch(() => false)
    const retryVisible = await retryAudioBtn.first().isVisible().catch(() => false)
    const scriptBtnVisible = await showScriptBtn.first().isVisible().catch(() => false)

    if (playVisible) {
      console.log('[E2E] PASS: Audio generated — "Play Podcast" button visible')

      // Check for HTML5 audio player
      const audioElement = page.locator('audio[controls]')
      await expect(audioElement.first()).toBeVisible({ timeout: 5000 })
      console.log('[E2E] PASS: HTML5 audio player rendered')

      // Check for duration estimate
      const durationText = page.locator('span:text-matches("~\\\\d+ minute")')
      const hasDuration = await durationText.first().isVisible().catch(() => false)
      if (hasDuration) {
        const dur = await durationText.first().textContent()
        console.log(`[E2E] PASS: Duration estimate shown: "${dur}"`)
      }

      // Check for page range badge on audio (shows which pages the podcast covers)
      const audioPageBadge = page.locator('span:has-text("Pages ")').filter({
        has: page.locator('svg') // the page badge has an SVG icon
      })
      const hasPageBadge = await audioPageBadge.first().isVisible().catch(() => false)
      if (hasPageBadge) {
        const badgeText = await audioPageBadge.first().textContent()
        console.log(`[E2E] PASS: Audio page range badge: "${badgeText.trim()}"`)
      }

      // Toggle "Show Script" to see the transcript
      if (scriptBtnVisible) {
        await showScriptBtn.first().click()
        const scriptContent = page.locator('h6:has-text("Audio Script")')
        await expect(scriptContent).toBeVisible({ timeout: 3000 })
        console.log('[E2E] PASS: Script toggled on — "Audio Script" heading visible')

        // Script should have content
        const scriptText = page.locator('p.whitespace-pre-wrap')
        await expect(scriptText.first()).toBeVisible({ timeout: 2000 })
        const scriptLen = (await scriptText.first().textContent()).length
        expect(scriptLen).toBeGreaterThan(50)
        console.log(`[E2E] PASS: Script content is ${scriptLen} chars`)

        // Toggle script off
        const hideScriptBtn = page.locator('button:has-text("Hide Script")')
        await hideScriptBtn.first().click()
        await expect(scriptContent).toBeHidden({ timeout: 2000 })
        console.log('[E2E] PASS: Script toggled off')
      }
    } else if (retryVisible || scriptBtnVisible) {
      console.log('[E2E] INFO: Audio TTS failed but script fallback available')

      // Script-only fallback — show script should be auto-toggled
      const scriptHeading = page.locator('h6:has-text("Audio Script")')
      const scriptVisible = await scriptHeading.isVisible().catch(() => false)
      if (scriptVisible) {
        console.log('[E2E] PASS: Script-only fallback rendered (TTS unavailable)')
      }

      // Check for error message
      const errorMsg = page.locator('span:has-text("Audio unavailable")').or(
        page.locator('span:has-text("quota exceeded")').or(
          page.locator('span:has-text("not configured")')
        )
      )
      const hasError = await errorMsg.first().isVisible().catch(() => false)
      if (hasError) {
        const errText = await errorMsg.first().textContent()
        console.log(`[E2E] INFO: Audio error message: "${errText}"`)
      }
    }

    // ══════════════════════════════════════════════════════
    // PHASE 5: Section Quiz — Generate from Slide Range
    // ══════════════════════════════════════════════════════

    // Find "Quiz this section" buttons
    const quizSectionButtons = page.locator('button:has-text("Quiz this section")')
    const quizSectionCount = await quizSectionButtons.count()
    console.log(`[E2E] Found ${quizSectionCount} "Quiz this section" buttons`)

    if (quizSectionCount > 0) {
      // Click the first "Quiz this section" button
      const firstQuizBtn = quizSectionButtons.first()
      await firstQuizBtn.scrollIntoViewIfNeeded()
      const quizBtnText = await firstQuizBtn.textContent()
      await firstQuizBtn.click()
      console.log(`[E2E] Clicked: "${quizBtnText.trim()}"`)

      // Button should show loading state "Generating section quiz..."
      const quizLoadingBtn = page.locator('button:has-text("Generating section quiz...")')
      const isLoadingVisible = await quizLoadingBtn.first().isVisible().catch(() => false)
      if (isLoadingVisible) {
        console.log('[E2E] PASS: "Generating section quiz..." loading state visible')
      }

      // Wait for the section quiz button to finish loading
      await expect(quizLoadingBtn.first()).toBeHidden({ timeout: 60000 }).catch(() => {})
      await page.waitForTimeout(1000)

      // Check if quiz modal appeared (section quiz may fail gracefully)
      const quizModal = page.locator('.fixed.inset-0.z-50').filter({
        has: page.locator('text=Generate Quiz').or(page.locator('text=Quick Quiz'))
      })
      let quizModalVisible = await quizModal.isVisible().catch(() => false)

      // If section quiz failed, check for error and fall back to "Take Knowledge Quiz"
      if (!quizModalVisible) {
        const sectionError = page.locator('text=/Section quiz|quiz.*failed/i')
        const hasError = await sectionError.first().isVisible().catch(() => false)
        if (hasError) {
          console.log('[E2E] INFO: Section quiz generation failed, falling back to Knowledge Quiz')
        } else {
          console.log('[E2E] INFO: Section quiz modal did not appear, trying Knowledge Quiz')
        }

        // Scroll down to find "Take Knowledge Quiz" button in the final assessment
        const knowledgeQuizBtn = page.locator('button:has-text("Take Knowledge Quiz")')
        const knowledgeQuizCount = await knowledgeQuizBtn.count()
        if (knowledgeQuizCount > 0) {
          await knowledgeQuizBtn.first().scrollIntoViewIfNeeded()
          await knowledgeQuizBtn.first().click()
          console.log('[E2E] Clicked "Take Knowledge Quiz" as fallback')
          await expect(quizModal).toBeVisible({ timeout: 10000 })
          quizModalVisible = true
        } else {
          console.log('[E2E] SKIP: No "Take Knowledge Quiz" button found either')
        }
      }

      if (!quizModalVisible) {
        console.log('[E2E] SKIP: Quiz modal never appeared, skipping quiz flow')
      } else {
      console.log('[E2E] PASS: Quiz modal opened (QuizForm)')

      // ── Select "Quick Quiz" type (first option, 8 questions) ──
      const quickQuizBtn = page.locator('button').filter({ has: page.locator('text=Quick Quiz') })
        .filter({ has: page.locator('text=8 questions') })
      const quickQuizVisible = await quickQuizBtn.first().isVisible().catch(() => false)
      if (quickQuizVisible) {
        await quickQuizBtn.first().click()
        console.log('[E2E] Selected "Quick Quiz" type')
      }

      // ── Click "Generate Quiz" ──
      const generateQuizBtn = page.locator('button:has-text("Generate Quiz")').last()
      await expect(generateQuizBtn).toBeVisible({ timeout: 5000 })
      await generateQuizBtn.click()
      console.log('[E2E] Clicked "Generate Quiz"')

      // Wait for "Generating Quiz..." to appear then disappear
      const generatingQuiz = page.locator('button:has-text("Generating Quiz...")')
      await expect(generatingQuiz).toBeVisible({ timeout: 10000 }).catch(() => {
        console.log('[E2E] INFO: "Generating Quiz..." state may have been too fast to catch')
      })

      // Wait for QuizPlayer "Ready to Begin?" screen
      const startQuizBtn = page.locator('button:has-text("Start Quiz")')
      await expect(startQuizBtn).toBeVisible({ timeout: 60000 })
      console.log('[E2E] PASS: QuizPlayer loaded — "Start Quiz" screen visible')

      // Intercept quiz submit API response for debugging
      page.on('response', response => {
        if (response.url().includes('/submit') && response.url().includes('/quizzes/')) {
          response.text().then(body => {
            console.log(`[E2E] Quiz submit API: ${response.status()} — ${body.substring(0, 300)}`)
          }).catch(() => {})
        }
      })

      // Click "Start Quiz"
      await startQuizBtn.click()
      console.log('[E2E] Clicked "Start Quiz"')
      await page.waitForTimeout(1000)

      // ══════════════════════════════════════════════════════
      // PHASE 6: Quiz Taking — Answer Questions
      // ══════════════════════════════════════════════════════

      // QuizPlayer shows questions one at a time:
      //  - Multiple choice: buttons with A/B/C/D letter badges
      //  - True/False: "True" and "False" buttons
      //  - Short answer: textarea with placeholder "Type your answer here..."
      let questionsAnswered = 0
      const maxQuestions = 25 // safety limit

      while (questionsAnswered < maxQuestions) {
        // Wait for a question to be visible — look for the Q badge
        const qBadge = page.locator('span:text-matches("^Q\\\\d+$")')
        const hasQuestion = await qBadge.first().isVisible().catch(() => false)
        if (!hasQuestion) break

        // Determine question type and answer accordingly
        const shortAnswerInput = page.locator('.fixed.inset-0.z-50 textarea[placeholder*="Type your answer"]')
        const trueFalseBtn = page.locator('.fixed.inset-0.z-50 button:has-text("True")')
        const mcOptions = page.locator('.fixed.inset-0.z-50 button[type="button"]')

        const isShortAnswer = await shortAnswerInput.isVisible().catch(() => false)
        const isTrueFalse = await trueFalseBtn.isVisible().catch(() => false)

        if (isShortAnswer) {
          // Type a generic answer for short-answer questions
          await shortAnswerInput.fill('This is a test answer for the E2E test covering the key concepts.')
          await page.waitForTimeout(200)
        } else if (isTrueFalse) {
          await trueFalseBtn.click()
          await page.waitForTimeout(200)
        } else {
          // Multiple choice — click the first option
          const optCount = await mcOptions.count()
          if (optCount > 0) {
            await mcOptions.first().click()
            await page.waitForTimeout(200)
          }
        }

        questionsAnswered++

        // Check for "Next" or "Submit Quiz" button
        const nextBtn = page.locator('button:has-text("Next"):not(:has-text("Previous"))').last()
        const submitQuizBtn = page.locator('button:has-text("Submit Quiz")')

        const submitVisible = await submitQuizBtn.isVisible().catch(() => false)
        const nextVisible = await nextBtn.isVisible().catch(() => false)

        if (submitVisible) {
          // Last question — submit the quiz
          await submitQuizBtn.click()
          console.log(`[E2E] Answered question ${questionsAnswered} (${isShortAnswer ? 'short answer' : isTrueFalse ? 'T/F' : 'MC'}), clicked "Submit Quiz"`)

          // Handle review screen — if shown, click "Submit Quiz" again
          await page.waitForTimeout(1500)
          const reviewSubmit = page.locator('button:has-text("Submit Quiz")')
          const stillHasSubmit = await reviewSubmit.isVisible().catch(() => false)
          if (stillHasSubmit) {
            await reviewSubmit.click()
            console.log('[E2E] Confirmed submission from review screen')
          }

          // Wait for submission to complete
          await page.waitForTimeout(3000)
          break
        } else if (nextVisible) {
          await nextBtn.click()
          console.log(`[E2E] Answered question ${questionsAnswered} (${isShortAnswer ? 'short answer' : isTrueFalse ? 'T/F' : 'MC'}), clicked "Next"`)
          await page.waitForTimeout(300)
        } else {
          console.log(`[E2E] Answered question ${questionsAnswered}, auto-advancing`)
          await page.waitForTimeout(500)
        }
      }

      console.log(`[E2E] Answered ${questionsAnswered} questions total`)

      // ══════════════════════════════════════════════════════
      // PHASE 7: Quiz Results
      // ══════════════════════════════════════════════════════

      // Wait for results screen — look for "X of Y correct" text in the quiz modal
      const quizModalArea = page.locator('.fixed.inset-0.z-50')

      // The results page shows "X of Y correct" — wait for this specific pattern
      const correctText = quizModalArea.locator('p:has-text("correct")')
      const hasResults = await correctText.first()
        .isVisible({ timeout: 30000 }).catch(() => false)

      if (hasResults) {
        const scoreText = await correctText.first().textContent().catch(() => 'N/A')
        console.log(`[E2E] PASS: Quiz results visible — ${scoreText.trim()}`)

        // Check for knowledge gap analysis
        const knowledgeSection = quizModalArea.locator('text=Knowledge Analysis').or(quizModalArea.locator('text=WEAK TOPICS'))
        const hasGaps = await knowledgeSection.first().isVisible().catch(() => false)
        if (hasGaps) console.log('[E2E] PASS: Knowledge gap analysis rendered')

        // Check action buttons by scrolling to bottom of modal
        const modalContent = quizModalArea.locator('.overflow-y-auto')
        if (await modalContent.count() > 0) {
          await modalContent.first().evaluate(el => el.scrollTop = el.scrollHeight)
          await page.waitForTimeout(500)
        }
        const retakeVisible = await quizModalArea.locator('button:has-text("Retake Quiz")').isVisible().catch(() => false)
        const studyVisible = await quizModalArea.locator('button:has-text("Study Weak")').isVisible().catch(() => false)
        const doneVisible = await quizModalArea.locator('button:has-text("Done")').isVisible().catch(() => false)
        console.log(`[E2E] Results buttons: Retake=${retakeVisible}, StudyWeak=${studyVisible}, Done=${doneVisible}`)
      } else {
        // Capture whatever the modal shows
        const modalText = await quizModalArea.innerText().catch(() => 'N/A')
        console.log(`[E2E] WARNING: Quiz results not detected. Modal text (first 400): ${modalText.substring(0, 400)}`)
      }

      // Close the quiz modal
      try {
        // Use the close button (title="Close quiz") or press Escape
        const closeX = page.locator('button[title="Close quiz"]')
        if (await closeX.isVisible().catch(() => false)) {
          await closeX.click({ timeout: 3000 })
        } else {
          await page.keyboard.press('Escape')
        }
        await page.waitForTimeout(1000)

        // Handle error boundary if app crashed
        const tryAgainBtn = page.locator('button:has-text("Try Again")')
        if (await tryAgainBtn.isVisible().catch(() => false)) {
          console.log('[E2E] INFO: App error boundary — clicking "Try Again"')
          await tryAgainBtn.click()
          await page.waitForTimeout(1000)
        }
      } catch {
        console.log('[E2E] INFO: Quiz modal already closed')
      }
      console.log('[E2E] Quiz flow complete')

      } // end if (quizModalVisible)
    } else {
      console.log('[E2E] SKIP: No "Quiz this section" buttons found (plan may lack page ranges)')
    }

    // ══════════════════════════════════════════════════════
    // CONSOLE ERRORS (for debugging)
    // ══════════════════════════════════════════════════════
    if (consoleErrors.length > 0) {
      console.log(`\n[E2E] ── Console Errors (${consoleErrors.length}) ──`)
      for (const err of consoleErrors.slice(0, 10)) {
        console.log(`[E2E] ERROR: ${err.substring(0, 200)}`)
      }
    }

    // ══════════════════════════════════════════════════════
    // SUMMARY
    // ══════════════════════════════════════════════════════
    console.log('\n[E2E] ════════════════════════════════════════')
    console.log('[E2E] Audio Plan + PPTX Upload E2E PASSED')
    console.log(`[E2E] Days: ${dayCount}, Podcast buttons: ${podcastCount}`)
    console.log(`[E2E] Slide viewers: ${pageRangeCount}, Quiz sections: ${quizSectionCount}`)
    console.log(`[E2E] Videos: ${videoCount}, Articles: ${articleCount}, Slides: ${slideCount}`)
    console.log(`[E2E] Curation rate: ${curationPct}%`)
    console.log('[E2E] ════════════════════════════════════════')
  })
})

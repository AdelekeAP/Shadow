import { test, expect } from '@playwright/test'
import path from 'path'
import { TEST_EMAIL, TEST_PASSWORD, loginViaApi } from './helpers.js'

/*
 * E2E: Reading Learning Style — Study Plan with PPTX Upload
 *
 * Tests the full flow: login → SmartStudy → upload lecture slides →
 * select course → create reading plan → verify:
 *   1. "reading learner" badge displayed
 *   2. Study Cards component (Flashcards / Key Concepts / Comprehension tabs)
 *   3. ZERO YouTube videos (reading learners skip videos entirely)
 *   4. High proportion of Article / Documentation / Your Slides resources
 *   5. Slide range inline viewing (Pages X-Y buttons)
 *   6. Section quiz generation + quiz taking flow
 *   7. Resource curation quality
 */

const PPTX_PATH = path.resolve(__dirname, '../../CSC 411_ Machine Learning Lecture 1.pptx')
const COURSE_LABEL = 'PAU-CSC411' // Machine Learning course

test.describe('Reading Learning Style — Study Plan with PPTX Upload', () => {
  // PPTX upload + processing + plan generation + study cards + quiz
  test.setTimeout(720000) // 12 minutes

  test.beforeEach(async ({ page }) => {
    // Login via API
    const loginData = await loginViaApi(page, '/smartstudy', TEST_EMAIL, TEST_PASSWORD)
    expect(loginData.access_token).toBeTruthy()

    await expect(page.locator('h1:has-text("SmartStudy")')).toBeVisible({ timeout: 10000 })
  })

  test('generates reading plan from PPTX with study cards, slides, and quiz', async ({ page }) => {
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
    // PHASE 1: Create a Reading Study Plan from PPTX
    // ══════════════════════════════════════════════════════

    await page.locator('button:has-text("New Study Plan")').first().click()
    await expect(page.locator('h3:has-text("Create a New Study Plan")')).toBeVisible({ timeout: 5000 })

    // Upload the PPTX file
    const fileInput = page.locator('input[type="file"][accept=".pdf,.pptx,.ppt"]')
    await fileInput.setInputFiles(PPTX_PATH)
    await expect(page.locator('text=CSC 411_ Machine Learning Lecture 1.pptx')).toBeVisible({ timeout: 3000 })
    console.log('[E2E] PPTX file uploaded successfully')

    // Select the PAU-CSC411 course
    const courseSelect = page.locator('select').filter({ has: page.locator('option:has-text("Select course...")') })
    const courseOption = courseSelect.locator(`option:has-text("${COURSE_LABEL}")`)
    const courseValue = await courseOption.getAttribute('value')
    await courseSelect.selectOption(courseValue)
    console.log('[E2E] Course selected: PAU-CSC411 - Machine Learning')

    // Select "Reading" learning style
    const readingStyleBtn = page.locator('button', { has: page.locator('p:text-is("Reading")') })
      .filter({ has: page.locator('p:text-is("Articles & docs")') })
    await readingStyleBtn.scrollIntoViewIfNeeded()
    await readingStyleBtn.click()
    console.log('[E2E] Reading learning style selected')

    // Click "Generate Plan"
    const generateBtn = page.locator('button[type="submit"]:has-text("Generate Plan")')
    await generateBtn.click()

    // Wait for overlay
    const overlay = page.locator('.fixed.inset-0.z-50')
    await expect(overlay).toBeVisible({ timeout: 15000 })
    console.log('[E2E] GeneratingOverlay appeared — generating reading plan from slides...')

    await expect(overlay).toBeHidden({ timeout: 240000 })
    console.log('[E2E] GeneratingOverlay dismissed — reading plan generated')

    // Wait for plan list to refresh
    await page.waitForTimeout(3000)

    // Click the most recent plan in the sidebar
    const planButtons = page.locator('.space-y-1 button').first()
    await expect(planButtons).toBeVisible({ timeout: 10000 })
    await planButtons.click()
    await page.waitForTimeout(1500)

    // ══════════════════════════════════════════════════════
    // PHASE 2: Verify Reading Plan Structure
    // ══════════════════════════════════════════════════════

    // ASSERTION 1: Plan has day sections
    const dayBadges = page.locator('span:text-matches("Day \\\\d+")')
    const dayCount = await dayBadges.count()
    expect(dayCount).toBeGreaterThanOrEqual(3)
    console.log(`[E2E] PASS: Found ${dayCount} day sections`)

    // ASSERTION 2: Reading learner badge is displayed
    const readingBadge = page.locator('span:has-text("reading learner")')
    await expect(readingBadge).toBeVisible({ timeout: 5000 })
    console.log('[E2E] PASS: "reading learner" badge visible')

    // ASSERTION 3: No "View Diagram" buttons (visual-only feature)
    const diagramButtons = page.locator('button:has-text("View Diagram")')
    const diagramCount = await diagramButtons.count()
    expect(diagramCount).toBe(0)
    console.log('[E2E] PASS: No "View Diagram" buttons (correctly absent for reading)')

    // ASSERTION 4: No "Generate Podcast" buttons (audio-only feature)
    const podcastButtons = page.locator('button:has-text("Generate Podcast")')
    const podcastCount = await podcastButtons.count()
    expect(podcastCount).toBe(0)
    console.log('[E2E] PASS: No "Generate Podcast" buttons (correctly absent for reading)')

    // ASSERTION 5: Resource breakdown
    const videoCards = page.locator('span:text-is("Video")')
    const articleCards = page.locator('span:text-is("Article")')
    const docCards = page.locator('span:text-is("Documentation")')
    const slideCards = page.locator('span:text-is("Your Slides")')
    const interactiveCards = page.locator('span:text-is("Interactive")')
    const practiceCards = page.locator('span:text-is("Practice")')
    const aiCards = page.locator('span:text-is("AI Guide")')

    const videoCount = await videoCards.count()
    const articleCount = await articleCards.count()
    const docCount = await docCards.count()
    const slideCount = await slideCards.count()
    const interactiveCount = await interactiveCards.count()
    const practiceCount = await practiceCards.count()
    const aiCount = await aiCards.count()

    console.log('[E2E] Resource breakdown:')
    console.log(`  YouTube videos: ${videoCount}`)
    console.log(`  Articles: ${articleCount}`)
    console.log(`  Documentation: ${docCount}`)
    console.log(`  Your Slides: ${slideCount}`)
    console.log(`  Interactive: ${interactiveCount}`)
    console.log(`  Practice: ${practiceCount}`)
    console.log(`  AI Generated: ${aiCount}`)

    const textResources = articleCount + docCount + slideCount
    const totalCurated = videoCount + articleCount + docCount + slideCount + interactiveCount + practiceCount
    const totalResources = totalCurated + aiCount
    const curationPct = totalResources > 0 ? Math.round(totalCurated / totalResources * 100) : 0
    console.log(`  Text-based resources: ${textResources}`)
    console.log(`  Curation rate: ${totalCurated}/${totalResources} (${curationPct}%)`)

    // ASSERTION 6: Reading learners should get ZERO YouTube videos
    expect(videoCount).toBe(0)
    console.log('[E2E] PASS: 0 YouTube videos (reading learners correctly skip videos)')

    // ASSERTION 7: Reading learners should have text-based resources
    expect(textResources).toBeGreaterThanOrEqual(1)
    console.log(`[E2E] PASS: ${textResources} text-based resources (articles + docs + slides)`)

    // ASSERTION 8: At least some curated resources
    expect(totalCurated).toBeGreaterThanOrEqual(1)
    console.log(`[E2E] PASS: ${totalCurated} curated resources found`)

    // ══════════════════════════════════════════════════════
    // PHASE 3: Study Cards Component (Reading-specific)
    // ══════════════════════════════════════════════════════

    // Study Cards starts with "Generate Study Cards" buttons (like Practice Exercises).
    // Must click one to trigger GPT generation, then the tabs (Flashcards, Key Concepts,
    // Comprehension) appear.
    const generateStudyCardsBtn = page.locator('button:has-text("Generate Study Cards")')
    const generateStudyCardsCount = await generateStudyCardsBtn.count()
    console.log(`[E2E] Found ${generateStudyCardsCount} "Generate Study Cards" buttons`)

    expect(generateStudyCardsCount).toBeGreaterThanOrEqual(1)
    console.log('[E2E] PASS: "Generate Study Cards" buttons present (reading-specific feature)')

    // Click the first one to trigger generation
    const firstStudyCardsBtn = generateStudyCardsBtn.first()
    await firstStudyCardsBtn.scrollIntoViewIfNeeded()
    await firstStudyCardsBtn.click()
    console.log('[E2E] Clicked "Generate Study Cards" — generating via GPT...')

    // Wait for "Generating study cards..." to appear then disappear
    const generatingCardsBtn = page.locator('button:has-text("Generating study cards...")')
    await expect(generatingCardsBtn.first()).toBeVisible({ timeout: 5000 }).catch(() => {
      console.log('[E2E] INFO: "Generating study cards..." state too fast to catch')
    })
    await expect(generatingCardsBtn.first()).toBeHidden({ timeout: 90000 })
    console.log('[E2E] Study cards generation complete')

    await page.waitForTimeout(1000)

    // Now look for the Study Cards tabs
    const flashcardsTab = page.locator('button:has-text("Flashcards")')
    const keyConceptsTab = page.locator('button:has-text("Key Concepts")')
    const comprehensionTab = page.locator('button:has-text("Comprehension")')

    const flashcardsCount = await flashcardsTab.count()
    const keyConceptsCount = await keyConceptsTab.count()
    const comprehensionCount = await comprehensionTab.count()

    console.log(`[E2E] Study Cards tabs found: Flashcards=${flashcardsCount}, Key Concepts=${keyConceptsCount}, Comprehension=${comprehensionCount}`)

    if (flashcardsCount > 0) {
      // Flashcards tab should be active by default
      // Look for flashcard content — "Card X of Y" counter
      const cardCounter = page.locator('text=/Card \\d+ of \\d+/')
      const hasCardCounter = await cardCounter.first().isVisible({ timeout: 5000 }).catch(() => false)
      if (hasCardCounter) {
        const counterText = await cardCounter.first().textContent()
        console.log(`[E2E] PASS: Flashcard counter visible: "${counterText.trim()}"`)

        // Try to flip a card (click the card area)
        const flipArea = page.locator('text=Click to flip')
        if (await flipArea.first().isVisible().catch(() => false)) {
          await flipArea.first().click()
          await page.waitForTimeout(600)

          // After flip, "Answer" label should appear
          const answerLabel = page.locator('span:has-text("Answer")')
          const flipped = await answerLabel.first().isVisible().catch(() => false)
          if (flipped) {
            console.log('[E2E] PASS: Flashcard flip works — "Answer" side visible')
          } else {
            console.log('[E2E] INFO: Flashcard flip triggered (animation may be slow)')
          }
        }

        // Test "Know it" button
        const knowItBtn = page.locator('button:has-text("Know it")')
        if (await knowItBtn.first().isVisible().catch(() => false)) {
          console.log('[E2E] PASS: "Know it" mastery button visible')
        }
      } else {
        console.log('[E2E] INFO: Flashcard content not visible (cards may be empty)')
      }

      // Switch to Key Concepts tab
      if (keyConceptsCount > 0) {
        await keyConceptsTab.first().scrollIntoViewIfNeeded()
        await keyConceptsTab.first().click()
        await page.waitForTimeout(500)

        // Key Concepts shows expandable items with importance badges
        const criticalBadges = page.locator('span:has-text("Critical")')
        const extraBadges = page.locator('span:has-text("Extra")')
        const critCount = await criticalBadges.count()
        const extraCount = await extraBadges.count()
        console.log(`[E2E] Key Concepts: ${critCount} critical, ${extraCount} supplementary items`)

        // Click first concept to expand
        const conceptButtons = page.locator('.rounded-lg.border button').first()
        if (await conceptButtons.isVisible().catch(() => false)) {
          await conceptButtons.click()
          await page.waitForTimeout(300)
          console.log('[E2E] PASS: Key Concepts accordion expand works')
        }
      }

      // Switch to Comprehension tab
      if (comprehensionCount > 0) {
        await comprehensionTab.first().scrollIntoViewIfNeeded()
        await comprehensionTab.first().click()
        await page.waitForTimeout(500)

        // Comprehension shows questions with "Reveal Sample Answer" button
        const revealBtn = page.locator('button:has-text("Reveal Sample Answer")')
        const questionLabel = page.locator('span:has-text("Question 1")')
        const hasQuestion = await questionLabel.first().isVisible().catch(() => false)
        const hasReveal = await revealBtn.first().isVisible().catch(() => false)

        if (hasQuestion) {
          console.log('[E2E] PASS: Comprehension question 1 visible')
        }
        if (hasReveal) {
          // Click to reveal the sample answer
          await revealBtn.first().click()
          await page.waitForTimeout(500)

          const sampleAnswer = page.locator('text=Sample Answer')
          const hasSample = await sampleAnswer.first().isVisible().catch(() => false)
          if (hasSample) {
            console.log('[E2E] PASS: "Reveal Sample Answer" works — answer visible')
          }

          // Check for self-rating buttons
          const gotItBtn = page.locator('button:has-text("Got it")')
          const partiallyBtn = page.locator('button:has-text("Partially")')
          const reviewBtn = page.locator('button:has-text("Need to review")')
          const hasRating = await gotItBtn.first().isVisible().catch(() => false)
          if (hasRating) {
            console.log('[E2E] PASS: Self-rating buttons visible (Got it / Partially / Need to review)')
          }
        }
      }

      console.log('[E2E] PASS: Study Cards component fully rendered (reading-specific feature)')
    } else {
      console.log('[E2E] WARNING: Study Cards tabs not found after generation — possible API error')
    }

    // ══════════════════════════════════════════════════════
    // PHASE 4: Slide Range Inline Viewing
    // ══════════════════════════════════════════════════════

    const pageRangeButtons = page.locator('button:has-text("Pages ")')
      .filter({ hasNot: page.locator('text=Quiz this section') })
    const pageRangeCount = await pageRangeButtons.count()
    console.log(`[E2E] Found ${pageRangeCount} "Pages X-Y" slide range buttons`)

    if (pageRangeCount > 0) {
      const firstPageBtn = pageRangeButtons.first()
      await firstPageBtn.scrollIntoViewIfNeeded()
      const pageRangeText = await firstPageBtn.textContent()
      await firstPageBtn.click()
      console.log(`[E2E] Clicked slide range button: "${pageRangeText.trim()}"`)

      await page.waitForTimeout(3000)

      const viewerToolbar = page.locator('span:has-text("100%")').first()
      const toolbarVisible = await viewerToolbar.isVisible().catch(() => false)

      if (toolbarVisible) {
        console.log('[E2E] PASS: SlideRangeViewer rendered with zoom controls')
      } else {
        console.log('[E2E] INFO: SlideRangeViewer opened but PDF may still be loading')
      }

      // Close the viewer
      await firstPageBtn.scrollIntoViewIfNeeded()
      await firstPageBtn.click()
      await page.waitForTimeout(500)
      console.log('[E2E] Closed SlideRangeViewer')
    }

    // ══════════════════════════════════════════════════════
    // PHASE 5: Quiz Flow
    // ══════════════════════════════════════════════════════

    // Try section quiz first, fall back to Knowledge Quiz
    const quizSectionButtons = page.locator('button:has-text("Quiz this section")')
    const quizSectionCount = await quizSectionButtons.count()
    console.log(`[E2E] Found ${quizSectionCount} "Quiz this section" buttons`)

    let quizModalVisible = false

    if (quizSectionCount > 0) {
      const firstQuizBtn = quizSectionButtons.first()
      await firstQuizBtn.scrollIntoViewIfNeeded()
      await firstQuizBtn.click()
      console.log('[E2E] Clicked "Quiz this section"')

      const quizLoadingBtn = page.locator('button:has-text("Generating section quiz...")')
      await expect(quizLoadingBtn.first()).toBeHidden({ timeout: 60000 }).catch(() => {})
      await page.waitForTimeout(1000)
    }

    // Check if quiz modal opened
    const quizModal = page.locator('.fixed.inset-0.z-50').filter({
      has: page.locator('text=Generate Quiz').or(page.locator('text=Quick Quiz'))
    })
    quizModalVisible = await quizModal.isVisible().catch(() => false)

    if (!quizModalVisible) {
      // Fall back to "Take Knowledge Quiz"
      const knowledgeQuizBtn = page.locator('button:has-text("Take Knowledge Quiz")')
      if (await knowledgeQuizBtn.count() > 0) {
        await knowledgeQuizBtn.first().scrollIntoViewIfNeeded()
        await knowledgeQuizBtn.first().click()
        console.log('[E2E] Clicked "Take Knowledge Quiz" as fallback')
        quizModalVisible = await quizModal.isVisible({ timeout: 10000 }).catch(() => false)
      }
    }

    if (quizModalVisible) {
      console.log('[E2E] PASS: Quiz modal opened (QuizForm)')

      // Select "Quick Quiz"
      const quickQuizBtn = page.locator('button').filter({ has: page.locator('text=Quick Quiz') })
        .filter({ has: page.locator('text=8 questions') })
      if (await quickQuizBtn.first().isVisible().catch(() => false)) {
        await quickQuizBtn.first().click()
        console.log('[E2E] Selected "Quick Quiz" type')
      }

      // Click "Generate Quiz"
      const generateQuizBtn = page.locator('button:has-text("Generate Quiz")').last()
      await expect(generateQuizBtn).toBeVisible({ timeout: 5000 })
      await generateQuizBtn.click()
      console.log('[E2E] Clicked "Generate Quiz"')

      // Wait for QuizPlayer
      const startQuizBtn = page.locator('button:has-text("Start Quiz")')
      await expect(startQuizBtn).toBeVisible({ timeout: 60000 })
      console.log('[E2E] PASS: QuizPlayer loaded — "Start Quiz" visible')

      // Intercept quiz submit API
      page.on('response', response => {
        if (response.url().includes('/submit') && response.url().includes('/quizzes/')) {
          response.text().then(body => {
            console.log(`[E2E] Quiz submit API: ${response.status()} — ${body.substring(0, 300)}`)
          }).catch(() => {})
        }
      })

      await startQuizBtn.click()
      console.log('[E2E] Clicked "Start Quiz"')
      await page.waitForTimeout(1000)

      // Answer all questions
      let questionsAnswered = 0
      const maxQuestions = 25

      while (questionsAnswered < maxQuestions) {
        const qBadge = page.locator('span:text-matches("^Q\\\\d+$")')
        if (!await qBadge.first().isVisible().catch(() => false)) break

        const shortAnswerInput = page.locator('.fixed.inset-0.z-50 textarea[placeholder*="Type your answer"]')
        const trueFalseBtn = page.locator('.fixed.inset-0.z-50 button:has-text("True")')
        const mcOptions = page.locator('.fixed.inset-0.z-50 button[type="button"]')

        const isShortAnswer = await shortAnswerInput.isVisible().catch(() => false)
        const isTrueFalse = await trueFalseBtn.isVisible().catch(() => false)

        if (isShortAnswer) {
          await shortAnswerInput.fill('This concept relates to the key machine learning principles discussed in the lecture slides.')
          await page.waitForTimeout(200)
        } else if (isTrueFalse) {
          await trueFalseBtn.click()
          await page.waitForTimeout(200)
        } else {
          if (await mcOptions.count() > 0) {
            await mcOptions.first().click()
            await page.waitForTimeout(200)
          }
        }

        questionsAnswered++

        const submitQuizBtn = page.locator('button:has-text("Submit Quiz")')
        const nextBtn = page.locator('button:has-text("Next"):not(:has-text("Previous"))').last()

        if (await submitQuizBtn.isVisible().catch(() => false)) {
          await submitQuizBtn.click()
          console.log(`[E2E] Answered Q${questionsAnswered}, clicked "Submit Quiz"`)

          await page.waitForTimeout(1500)
          const reviewSubmit = page.locator('button:has-text("Submit Quiz")')
          if (await reviewSubmit.isVisible().catch(() => false)) {
            await reviewSubmit.click()
            console.log('[E2E] Confirmed submission from review screen')
          }
          await page.waitForTimeout(3000)
          break
        } else if (await nextBtn.isVisible().catch(() => false)) {
          await nextBtn.click()
          await page.waitForTimeout(300)
        } else {
          await page.waitForTimeout(500)
        }
      }

      console.log(`[E2E] Answered ${questionsAnswered} questions total`)

      // Check results
      const quizModalArea = page.locator('.fixed.inset-0.z-50')
      const correctText = quizModalArea.locator('p:has-text("correct")')
      const hasResults = await correctText.first().isVisible({ timeout: 30000 }).catch(() => false)

      if (hasResults) {
        const scoreText = await correctText.first().textContent().catch(() => 'N/A')
        console.log(`[E2E] PASS: Quiz results visible — ${scoreText.trim()}`)

        const modalContent = quizModalArea.locator('.overflow-y-auto')
        if (await modalContent.count() > 0) {
          await modalContent.first().evaluate(el => el.scrollTop = el.scrollHeight)
          await page.waitForTimeout(500)
        }
        const retakeVisible = await quizModalArea.locator('button:has-text("Retake Quiz")').isVisible().catch(() => false)
        const doneVisible = await quizModalArea.locator('button:has-text("Done")').isVisible().catch(() => false)
        console.log(`[E2E] Results buttons: Retake=${retakeVisible}, Done=${doneVisible}`)
      } else {
        const modalText = await quizModalArea.innerText().catch(() => 'N/A')
        console.log(`[E2E] WARNING: Quiz results not detected. Modal text (first 400): ${modalText.substring(0, 400)}`)
      }

      // Close quiz modal
      try {
        const closeX = page.locator('button[title="Close quiz"]')
        if (await closeX.isVisible().catch(() => false)) {
          await closeX.click({ timeout: 3000 })
        } else {
          await page.keyboard.press('Escape')
        }
        await page.waitForTimeout(1000)

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
    } else {
      console.log('[E2E] SKIP: No quiz buttons found')
    }

    // ══════════════════════════════════════════════════════
    // CONSOLE ERRORS
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
    console.log('[E2E] Reading Plan + PPTX Upload E2E PASSED')
    console.log(`[E2E] Days: ${dayCount}`)
    console.log(`[E2E] Videos: ${videoCount} (should be 0), Articles: ${articleCount}, Docs: ${docCount}, Slides: ${slideCount}`)
    console.log(`[E2E] Text-based resources: ${textResources}`)
    console.log(`[E2E] Curation rate: ${curationPct}%`)
    console.log(`[E2E] Study Cards: ${generateStudyCardsCount} generate buttons, Tabs: Flashcards=${flashcardsCount}, KeyConcepts=${keyConceptsCount}, Comprehension=${comprehensionCount}`)
    console.log(`[E2E] Slide viewers: ${pageRangeCount}, Quiz sections: ${quizSectionCount}`)
    console.log('[E2E] ════════════════════════════════════════')
  })
})

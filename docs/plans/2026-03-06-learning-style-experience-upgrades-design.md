# Learning Style Experience Upgrades — Design Document

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Give reading and kinesthetic learners dedicated, AI-enhanced experiences on par with visual (diagrams) and audio (podcasts).

**Architecture:** Two new features built as single-GPT-call services with dedicated frontend components, following the exact pattern of ConceptDiagram/AudioPlayer/PracticeExercise.

**Tech Stack:** FastAPI, GPT via call_with_retry, React (Vite), Tailwind CSS

---

## Feature A: Reading Learners — "StudyCards"

### Backend Service: `StudyCardsService`

**File:** `backend/app/services/study_cards_service.py`

Single GPT call generates structured JSON with three sections:

```json
{
  "flashcards": [
    { "front": "What is a Binary Search Tree?",
      "back": "A tree where left children < parent < right children",
      "category": "definition" }
  ],
  "key_concepts": [
    { "concept": "BST Property",
      "explanation": "For every node, all values in left subtree are smaller...",
      "importance": "critical" }
  ],
  "comprehension_questions": [
    { "question": "Why is BST search O(log n) on average?",
      "hint": "Think about how many nodes you skip at each step",
      "sample_answer": "Each comparison eliminates half the remaining nodes..." }
  ]
}
```

- Uses `call_with_retry` with `PLAN_MODELS`
- Includes `_slide_content` from plan_data when available
- Generates 8-12 flashcards, 4-6 key concepts, 3-5 comprehension questions
- Flashcard categories: `definition`, `concept`, `formula`, `example`
- Key concept importance levels: `critical`, `important`, `supplementary`
- Fallback on GPT failure: 3 generic review flashcards
- Singleton pattern via `get_study_cards_service()`

### API Endpoint

```
POST /api/v1/smartstudy/study-plans/{plan_id}/resources/{resource_id}/study-cards
Rate limit: 5/minute; 30/hour
Auth: Bearer token (get_current_user)
Returns: { flashcards, key_concepts, comprehension_questions, plan_id, resource_id }
```

### Frontend Component: `StudyCards.jsx`

Three-tab component designed with /frontend-design skill:

**Tab 1 — Flashcards:**
- Stack of cards with 3D flip animation (click to reveal back)
- Arrow navigation between cards
- Category badges with distinct colors per category
- Progress: "Card 3 of 10"
- "Know it" / "Review again" sorting (review-again cards cycle back)

**Tab 2 — Key Concepts:**
- Importance-based hierarchy (critical = prominent, supplementary = muted)
- Expandable: title always visible, explanation on click
- Clean typographic layout

**Tab 3 — Comprehension Check:**
- One question at a time
- Text input for student's answer
- "Reveal Answer" shows sample answer for self-comparison
- Self-rating: "Got it" / "Partially" / "Need to review"
- Progress bar across all questions

### Rendering Logic

In `StudyPlanDetails.jsx`:
```javascript
const isReadingPlan = planData.learning_style_used === 'reading'
const showStudyCards = isReadingPlan || ['reading', 'review'].includes(activity.activity_type)
```

### Form Hint

In `StudyPlanForm.jsx`, when reading style selected:
- Emerald-themed hint: "Reading mode! Each activity includes flashcards, key concept summaries, and comprehension questions."

---

## Feature B: Kinesthetic Learners — Guided Solver Upgrade

### Backend: Step Validation Endpoint

**File:** `backend/app/routes/smartstudy/study_plans.py` (new endpoint)

```
POST /api/v1/smartstudy/study-plans/{plan_id}/resources/{resource_id}/exercises/validate-step
Body: { "exercise_title": "...", "step_text": "...", "student_answer": "...", "topic": "..." }
Rate limit: 10/minute; 60/hour
Returns: { "correct": bool, "feedback": "...", "hint": "..." }
```

- Lightweight GPT call using `CHAT_MODELS` (faster/cheaper)
- System prompt: encouraging tutor, validates attempt, returns structured JSON
- ~200 token response
- On GPT failure: `{ "correct": null, "feedback": "Couldn't validate — mark this step yourself", "hint": null }`

### Frontend: Upgrade `PracticeExercise.jsx`

**Changes to existing component:**

1. Each step gets a text input field + "Check" button
2. Step states expand: `idle` → `submitted` → `correct` / `needs_retry`
3. Animated feedback: green slide-in for correct, amber for hint
4. Toggle between "guided mode" (input fields) and "checklist mode" (checkboxes) per exercise
5. After all exercises complete: "Test Yourself" prompt linking to quiz feature with topic pre-filled

### Quiz Connection

After all exercises validated correct:
```
"Nice work! Ready to test your knowledge?"
[Take Quiz on {topic}] → navigates to quiz with topic pre-filled
```

---

## Files Summary

### New Files
| File | Purpose |
|------|---------|
| `backend/app/services/study_cards_service.py` | StudyCards GPT generation service |
| `frontend/src/components/studyplan/StudyCards.jsx` | 3-tab reading toolkit (frontend-design) |
| `backend/tests/test_services/test_study_cards_and_guided.py` | Tests for both features |

### Modified Files
| File | Change |
|------|--------|
| `backend/app/routes/smartstudy/study_plans.py` | `/study-cards` + `/exercises/validate-step` endpoints |
| `frontend/src/components/studyplan/PracticeExercise.jsx` | Input fields, GPT validation, guided/checklist toggle, quiz prompt |
| `frontend/src/components/studyplan/StudyPlanDetails.jsx` | `isReadingPlan`, `showStudyCards`, render `<StudyCards />` |
| `frontend/src/services/api.js` | `generateStudyCards()` + `validateExerciseStep()` functions |
| `frontend/src/components/studyplan/StudyPlanForm.jsx` | Reading learner hint |
| `backend/app/services/study_plan_generator.py` | Enhanced reading learner GPT prompt |

## Error Handling

- StudyCards GPT failure → 3 generic fallback flashcards
- validate-step GPT failure → `correct: null`, falls back to checklist mode
- Network errors → toast message, retry-enabled buttons

## Rate Limits

| Endpoint | Limit | Reasoning |
|----------|-------|-----------|
| `/study-cards` | 5/min; 30/hr | GPT generation cost |
| `/exercises/validate-step` | 10/min; 60/hr | Frequent per-step calls, but lightweight |

## Test Plan (~12 tests)

- StudyCards: generation success, with/without slides, invalid JSON fallback, field validation
- StudyCards endpoint: success, auth, 404
- validate-step: correct answer, incorrect with hint, GPT failure, auth

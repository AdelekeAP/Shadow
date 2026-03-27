# Learning Style Experience Upgrades — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Give reading learners a StudyCards toolkit (flashcards + key concepts + comprehension Q&A) and upgrade kinesthetic learners with a guided step solver + quiz connection.

**Architecture:** Two features following existing service+component+endpoint patterns (AudioSummaryService/AudioPlayer, PracticeExerciseService/PracticeExercise). StudyCards is a new service+component; Guided Solver upgrades the existing PracticeExercise component and adds a validation endpoint.

**Tech Stack:** FastAPI, GPT via `call_with_retry`, React (Vite), Tailwind CSS

---

## Task 1: Create StudyCardsService backend

**Files:**
- Create: `backend/app/services/study_cards_service.py`

**Step 1: Create the service file**

```python
"""
Study Cards Service
Generates flashcards, key concepts, and comprehension questions for reading learners.
Uses shared OpenAI infrastructure (call_with_retry) for content generation.
"""
import json
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class StudyCardsService:
    """Generates structured study cards for reading learners."""

    def generate(
        self,
        topic: str,
        activity_title: str,
        activity_description: str,
        slide_content: str = "",
    ) -> Dict[str, Any]:
        """
        Use GPT to generate flashcards, key concepts, and comprehension questions.

        Returns a dict with flashcards, key_concepts, and comprehension_questions arrays.
        """
        from app.services.openai_client import call_with_retry, PLAN_MODELS

        if slide_content:
            source_block = f"""
**Source Material from Slides**:
{slide_content[:3000]}

Create study cards that directly cover the concepts from these slides. Every flashcard and concept should map to actual slide content."""
        else:
            source_block = """
Use your deep knowledge of this topic to create comprehensive study materials from the ground up."""

        prompt = f"""Generate a complete study card set for a university student studying this topic.

**Topic**: {topic}
**Activity**: {activity_title}
**Details**: {activity_description}
{source_block}

Return ONLY valid JSON with exactly this structure:
{{
  "flashcards": [
    {{
      "front": "Question or term (concise, 1-2 sentences max)",
      "back": "Answer or definition (clear, 2-3 sentences max)",
      "category": "definition|concept|formula|example"
    }}
  ],
  "key_concepts": [
    {{
      "concept": "Concept name (2-5 words)",
      "explanation": "Clear explanation (2-4 sentences)",
      "importance": "critical|important|supplementary"
    }}
  ],
  "comprehension_questions": [
    {{
      "question": "A thought-provoking question testing understanding",
      "hint": "A helpful nudge without giving away the answer",
      "sample_answer": "A model answer (3-5 sentences)"
    }}
  ]
}}

Guidelines:
- Generate 8-12 flashcards covering all key terms, definitions, formulas, and examples
- Generate 4-6 key concepts with 2-3 marked "critical", rest as "important" or "supplementary"
- Generate 3-5 comprehension questions that test deep understanding, not just recall
- Flashcard categories: "definition" for terms, "concept" for ideas, "formula" for equations/rules, "example" for worked examples
- Order flashcards from foundational to advanced
- Comprehension questions should require synthesis, not just repeating facts
- Keep language clear and university-level appropriate"""

        response = call_with_retry(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert educational content creator specializing in "
                        "study materials for university students. You create flashcards, "
                        "concept summaries, and comprehension questions. "
                        "Return only valid JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            models=PLAN_MODELS,
            temperature=0.7,
            max_tokens=3000,
            timeout=45.0,
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse study cards JSON: {raw[:200]}")
            return self._fallback(topic)

        if not isinstance(data, dict):
            logger.warning("GPT returned non-dict study cards, using fallback")
            return self._fallback(topic)

        # Validate and sanitize each section
        result = {
            "flashcards": self._validate_flashcards(data.get("flashcards", []), topic),
            "key_concepts": self._validate_concepts(data.get("key_concepts", [])),
            "comprehension_questions": self._validate_questions(data.get("comprehension_questions", [])),
        }

        # Ensure we have at least some content
        if not result["flashcards"]:
            return self._fallback(topic)

        total = len(result["flashcards"]) + len(result["key_concepts"]) + len(result["comprehension_questions"])
        logger.info(f"Generated {total} study card items for '{topic}'")
        return result

    def _validate_flashcards(self, cards: Any, topic: str) -> List[Dict]:
        if not isinstance(cards, list):
            return []
        valid_categories = {"definition", "concept", "formula", "example"}
        validated = []
        for card in cards:
            if not isinstance(card, dict) or "front" not in card:
                continue
            validated.append({
                "front": str(card.get("front", "")),
                "back": str(card.get("back", "")),
                "category": card.get("category", "concept") if card.get("category") in valid_categories else "concept",
            })
        return validated[:15]  # Cap at 15

    def _validate_concepts(self, concepts: Any) -> List[Dict]:
        if not isinstance(concepts, list):
            return []
        valid_importance = {"critical", "important", "supplementary"}
        validated = []
        for concept in concepts:
            if not isinstance(concept, dict) or "concept" not in concept:
                continue
            validated.append({
                "concept": str(concept.get("concept", "")),
                "explanation": str(concept.get("explanation", "")),
                "importance": concept.get("importance", "important") if concept.get("importance") in valid_importance else "important",
            })
        return validated[:8]  # Cap at 8

    def _validate_questions(self, questions: Any) -> List[Dict]:
        if not isinstance(questions, list):
            return []
        validated = []
        for q in questions:
            if not isinstance(q, dict) or "question" not in q:
                continue
            validated.append({
                "question": str(q.get("question", "")),
                "hint": str(q.get("hint", "")),
                "sample_answer": str(q.get("sample_answer", "")),
            })
        return validated[:6]  # Cap at 6

    def _fallback(self, topic: str) -> Dict[str, Any]:
        """Return minimal fallback study cards when GPT fails."""
        return {
            "flashcards": [
                {"front": f"What is {topic}?", "back": f"Review your materials to define {topic} in your own words.", "category": "definition"},
                {"front": f"Why is {topic} important?", "back": f"Consider how {topic} connects to other concepts you've studied.", "category": "concept"},
                {"front": f"Give an example of {topic}", "back": f"Think of a real-world application of {topic}.", "category": "example"},
            ],
            "key_concepts": [
                {"concept": topic, "explanation": f"Review the core definition and principles of {topic}.", "importance": "critical"},
            ],
            "comprehension_questions": [
                {"question": f"Explain {topic} in your own words without looking at notes.", "hint": "Start with the basic definition, then expand.", "sample_answer": f"This requires reviewing your materials on {topic}."},
            ],
        }


# Singleton
_study_cards_service: Optional[StudyCardsService] = None


def get_study_cards_service() -> StudyCardsService:
    """Get or create StudyCardsService singleton."""
    global _study_cards_service
    if _study_cards_service is None:
        _study_cards_service = StudyCardsService()
    return _study_cards_service
```

**Step 2: Verify import works**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && source venv/bin/activate && python -c "from app.services.study_cards_service import get_study_cards_service; print('OK')"`
Expected: `OK`

---

## Task 2: Add study-cards and validate-step endpoints

**Files:**
- Modify: `backend/app/routes/smartstudy/study_plans.py`

**Step 1: Add the study-cards endpoint**

After the practice exercises endpoint block (after line ~981), add:

```python
# ============================================================================
# Study Cards Endpoints (Reading Learners)
# ============================================================================

@router.post(
    "/study-plans/{plan_id}/resources/{resource_id}/study-cards",
    operation_id="generate_study_cards",
    summary="Generate flashcards, key concepts, and comprehension questions",
)
@limiter.limit("5/minute;30/hour")
async def generate_study_cards(
    request: Request,
    plan_id: UUID,
    resource_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate study cards for reading learners.
    Returns flashcards, key concepts, and comprehension questions.
    """
    try:
        plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study plan not found"
            )

        resource = db.query(StudyPlanResource).filter(
            StudyPlanResource.id == resource_id,
            StudyPlanResource.study_plan_id == plan_id
        ).first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        from app.services.study_cards_service import get_study_cards_service
        cards_service = get_study_cards_service()

        # Extract slide content stored during plan generation
        slide_content = ""
        if plan.plan_data and isinstance(plan.plan_data, dict):
            slide_content = plan.plan_data.get("_slide_content", "")

        result = cards_service.generate(
            topic=plan.topic,
            activity_title=resource.resource_title or "Study Activity",
            activity_description=resource.resource_description or "",
            slide_content=slide_content,
        )

        return {
            **result,
            "plan_id": str(plan_id),
            "resource_id": str(resource_id),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating study cards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

**Step 2: Add the validate-step endpoint**

Below the study-cards endpoint, add:

```python
# ============================================================================
# Exercise Step Validation (Kinesthetic Guided Solver)
# ============================================================================

@router.post(
    "/study-plans/{plan_id}/resources/{resource_id}/exercises/validate-step",
    operation_id="validate_exercise_step",
    summary="Validate a student's answer for an exercise step",
)
@limiter.limit("10/minute;60/hour")
async def validate_exercise_step(
    request: Request,
    plan_id: UUID,
    resource_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate a student's answer for a specific exercise step.
    Uses lightweight GPT call for quick feedback.
    """
    try:
        body = await request.json()
        exercise_title = body.get("exercise_title", "")
        step_text = body.get("step_text", "")
        student_answer = body.get("student_answer", "")
        topic = body.get("topic", "")

        if not student_answer.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="student_answer is required"
            )

        # Verify plan ownership
        plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study plan not found"
            )

        # Lightweight GPT validation
        from app.services.openai_client import call_with_retry, CHAT_MODELS

        prompt = f"""A student is working on a practice exercise and submitted their answer for a step. Evaluate it.

**Topic**: {topic or plan.topic}
**Exercise**: {exercise_title}
**Step instruction**: {step_text}
**Student's answer**: {student_answer[:1000]}

Return ONLY valid JSON:
{{
  "correct": true or false,
  "feedback": "1-2 sentence encouraging feedback",
  "hint": "If incorrect, a helpful hint without giving the answer. If correct, null."
}}

Be encouraging. If the answer shows understanding even if imperfect, lean toward correct.
For open-ended steps (like 'open your editor'), always mark as correct."""

        try:
            response = call_with_retry(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a friendly, encouraging tutor. Validate student work and provide constructive feedback. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                models=CHAT_MODELS,
                temperature=0.3,
                max_tokens=200,
                timeout=15.0,
            )

            raw = response.choices[0].message.content.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

            result = json.loads(raw)
            return {
                "correct": bool(result.get("correct", False)),
                "feedback": str(result.get("feedback", "")),
                "hint": result.get("hint"),
            }

        except Exception as gpt_err:
            logger.warning(f"GPT validation failed: {gpt_err}")
            return {
                "correct": None,
                "feedback": "Couldn't validate automatically — mark this step yourself.",
                "hint": None,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating step: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

**Step 3: Add `import json` at the top of study_plans.py if not already present**

Check: `import json` should be in the imports at the top of the file. If not, add it.

**Step 4: Verify endpoints register**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && source venv/bin/activate && python -c "from app.main import app; routes = [r.path for r in app.routes]; print('study-cards' in str(routes), 'validate-step' in str(routes))"`
Expected: `True True`

---

## Task 3: Add API functions and enhance reading GPT prompt

**Files:**
- Modify: `frontend/src/services/api.js`
- Modify: `backend/app/services/study_plan_generator.py` (line 221)

**Step 1: Add `generateStudyCards` and `validateExerciseStep` to api.js**

After the `generatePracticeExercises` function (~line 865), add:

```javascript
export const generateStudyCards = async (planId, resourceId) => {
  const response = await api.post(
    `/api/v1/smartstudy/study-plans/${planId}/resources/${resourceId}/study-cards`
  )
  return response.data
}

export const validateExerciseStep = async (planId, resourceId, data) => {
  const response = await api.post(
    `/api/v1/smartstudy/study-plans/${planId}/resources/${resourceId}/exercises/validate-step`,
    data
  )
  return response.data
}
```

**Step 2: Enhance reading learner GPT prompt**

In `backend/app/services/study_plan_generator.py`, replace line 221:

```
  - Reading learners: more articles, documentation, and written guides
```

With:

```
  - Reading learners: PRIORITIZE text-based, deep-reading activities — articles, documentation, written guides, and review activities. Every day should have at least one "reading" or "review" activity. Include activities that encourage note-taking, summarization, and comprehension checks. Use detailed descriptions that give reading learners enough context to engage deeply with the material.
```

---

## Task 4: Build StudyCards frontend component

**Files:**
- Create: `frontend/src/components/studyplan/StudyCards.jsx`

**Step 1: Create the component**

This component will be built using the /frontend-design skill for a visually distinctive experience. The component must:

- Import `generateStudyCards` from `../../services/api`
- Accept props: `{ planId, resource, topic }`
- Have a "Generate Study Cards" button (emerald theme, matching the reading style)
- After generation, show 3 tabs: Flashcards, Key Concepts, Comprehension
- **Flashcards tab**: Cards with 3D CSS flip animation on click, category badges (definition=emerald, concept=blue, formula=amber, example=violet), arrow navigation, "Card N of M" counter, "Know it" / "Review again" buttons that sort cards
- **Key Concepts tab**: Importance hierarchy — critical gets prominent styling (left accent bar + bold), important is standard, supplementary is muted/smaller. Expandable: click to show explanation.
- **Comprehension tab**: One question at a time, textarea for student answer, "Reveal Answer" button, self-rating buttons ("Got it" / "Partially" / "Need to review"), progress dots at bottom
- Follow Shadow's design system: navy-900 for headings, surface-400 for body text, emerald for reading-learner accent color, rounded-lg borders, text-[12px]/text-[11px] sizes
- Loading state: spinner + "Generating study cards..."
- Error state: retry button

**This task MUST invoke the /frontend-design skill** for the StudyCards.jsx component to ensure it's visually distinctive and not generic.

---

## Task 5: Upgrade PracticeExercise with guided solver

**Files:**
- Modify: `frontend/src/components/studyplan/PracticeExercise.jsx`

**Step 1: Add the new imports and state**

Add to the imports at top:
```javascript
import { generatePracticeExercises, validateExerciseStep } from '../../services/api'
```

Replace the existing import of just `generatePracticeExercises`.

Add new state variables inside the component function:
```javascript
const [guidedMode, setGuidedMode] = useState(true) // true = input fields, false = checkboxes
const [stepAnswers, setStepAnswers] = useState({})   // { "exerciseIdx-stepIdx": "answer text" }
const [stepResults, setStepResults] = useState({})    // { "exerciseIdx-stepIdx": { correct, feedback, hint } }
const [validating, setValidating] = useState(null)    // "exerciseIdx-stepIdx" currently validating
```

**Step 2: Add the validate handler**

```javascript
const handleValidateStep = async (exerciseIdx, stepIdx, step, exerciseTitle) => {
  const key = `${exerciseIdx}-${stepIdx}`
  const answer = stepAnswers[key]
  if (!answer?.trim()) return

  setValidating(key)
  try {
    const result = await validateExerciseStep(planId, resource.id, {
      exercise_title: exerciseTitle,
      step_text: step,
      student_answer: answer,
      topic: topic,
    })

    setStepResults(prev => ({ ...prev, [key]: result }))

    // Auto-mark as completed if correct
    if (result.correct) {
      setCompletedSteps(prev => ({ ...prev, [key]: true }))
    }
  } catch (err) {
    console.error('Step validation failed:', err)
    setStepResults(prev => ({
      ...prev,
      [key]: { correct: null, feedback: 'Validation unavailable — mark this step yourself.', hint: null }
    }))
  } finally {
    setValidating(null)
  }
}
```

**Step 3: Replace the step rendering**

In the expanded exercise details section, replace the step buttons (the `exercise.steps.map` block) with guided mode support:

Each step in guided mode shows:
1. The step instruction text
2. A textarea input for the answer
3. A "Check" button (disabled while validating)
4. Result feedback below (green for correct, amber for needs retry with hint)

In checklist mode: keep the existing checkbox behavior.

Add a small toggle button in the exercise header area: "Guided" / "Checklist" mode switcher.

**Step 4: Add "Test Yourself" quiz prompt**

After the exercises list, when `allDone` is true, add:

```jsx
{allDone && (
  <div className="px-3 py-3 bg-emerald-50/40 border-t border-emerald-200/40">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <CheckCircleIcon className="w-4 h-4 text-emerald-500" />
        <span className="text-[12px] font-semibold text-emerald-700">
          All exercises complete! Ready to test yourself?
        </span>
      </div>
      <a
        href={`/smartstudy?quiz=${encodeURIComponent(topic)}`}
        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-[11px] font-semibold transition-all"
      >
        Take Quiz
      </a>
    </div>
  </div>
)}
```

---

## Task 6: Integrate StudyCards into StudyPlanDetails + Form hint

**Files:**
- Modify: `frontend/src/components/studyplan/StudyPlanDetails.jsx`
- Modify: `frontend/src/components/studyplan/StudyPlanForm.jsx`

**Step 1: Add import in StudyPlanDetails.jsx**

Add to the imports at the top (after the PracticeExercise import):
```javascript
import StudyCards from './StudyCards'
```

**Step 2: Add isReadingPlan constant**

After the existing `isKinestheticPlan` line (~line 52), it should already have `isReadingPlan` or add:
```javascript
const isReadingPlan = planData.learning_style_used === 'reading'
```

**Step 3: Add showStudyCards logic in the activity rendering**

In the activity rendering section (around line 410), after the `showExercises` const, add:
```javascript
const showStudyCards = isReadingPlan || ['reading', 'review'].includes(activity.activity_type)
```

**Step 4: Render StudyCards component**

After the PracticeExercise conditional render, add:
```jsx
{showStudyCards && (
  <StudyCards
    planId={plan.id}
    resource={matchingResource}
    topic={plan.topic}
  />
)}
```

**Step 5: Add reading learner hint in StudyPlanForm.jsx**

After the kinesthetic learner hint block (~line 448), add:
```jsx
{learningStyle === 'reading' && (
  <div className="flex items-center gap-2 text-[12px] text-emerald-600 bg-emerald-50/50 rounded-lg px-3 py-2 border border-emerald-200/60">
    <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
    </svg>
    Reading mode! Each activity includes flashcards, key concept summaries, and comprehension questions.
  </div>
)}
```

---

## Task 7: Write tests

**Files:**
- Create: `backend/tests/test_services/test_study_cards_and_guided.py`

**Step 1: Create the test file with all tests**

```python
"""
Tests for StudyCardsService, the study-cards endpoint, and the validate-step endpoint.

Covers:
  - GPT-based study card generation (flashcards, key concepts, comprehension)
  - Fallback on GPT failure / unparseable JSON
  - Field validation and sanitization
  - POST /study-cards endpoint auth, ownership, 404, and success paths
  - POST /exercises/validate-step correct, incorrect, GPT failure, auth
"""
import json
import uuid
import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from app.services.study_cards_service import (
    StudyCardsService,
    get_study_cards_service,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_openai_response(content: str) -> MagicMock:
    """Create a mock OpenAI ChatCompletion response."""
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content
    resp.model = "gpt-5.4"
    return resp


VALID_STUDY_CARDS_JSON = json.dumps({
    "flashcards": [
        {"front": "What is a stack?", "back": "LIFO data structure", "category": "definition"},
        {"front": "Push operation", "back": "Adds element to top", "category": "concept"},
    ],
    "key_concepts": [
        {"concept": "LIFO Principle", "explanation": "Last in, first out ordering.", "importance": "critical"},
        {"concept": "Stack Overflow", "explanation": "When stack exceeds capacity.", "importance": "important"},
    ],
    "comprehension_questions": [
        {"question": "Why use a stack for undo operations?", "hint": "Think about ordering.", "sample_answer": "Because undo reverses the most recent action first."},
    ],
})


# ===================================================================
# TestStudyCardsService  (unit tests)
# ===================================================================

class TestStudyCardsService:

    @pytest.fixture(autouse=True)
    def service(self):
        self.svc = StudyCardsService()

    # 1. Success path
    @patch("app.services.openai_client.call_with_retry")
    def test_generate_success(self, mock_retry):
        """Valid JSON from GPT -> dict with all three sections."""
        mock_retry.return_value = _mock_openai_response(VALID_STUDY_CARDS_JSON)

        result = self.svc.generate(
            topic="Data Structures",
            activity_title="Learn Stacks",
            activity_description="Understand LIFO",
        )

        assert "flashcards" in result
        assert "key_concepts" in result
        assert "comprehension_questions" in result
        assert len(result["flashcards"]) == 2
        assert len(result["key_concepts"]) == 2
        assert len(result["comprehension_questions"]) == 1
        assert result["flashcards"][0]["category"] == "definition"
        assert result["key_concepts"][0]["importance"] == "critical"

    # 2. Slide content in prompt
    @patch("app.services.openai_client.call_with_retry")
    def test_generate_with_slide_content(self, mock_retry):
        """When slide_content is provided, prompt includes it."""
        mock_retry.return_value = _mock_openai_response(VALID_STUDY_CARDS_JSON)

        self.svc.generate(
            topic="BST",
            activity_title="BST Intro",
            activity_description="Learn BST",
            slide_content="Slide 1: Binary tree definition",
        )

        call_args = mock_retry.call_args
        messages = call_args.kwargs.get("messages", call_args.args[0] if call_args.args else [])
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "Source Material from Slides" in user_msg["content"]

    # 3. No slide content
    @patch("app.services.openai_client.call_with_retry")
    def test_generate_without_slides(self, mock_retry):
        """Without slide_content, uses 'deep knowledge' path."""
        mock_retry.return_value = _mock_openai_response(VALID_STUDY_CARDS_JSON)

        self.svc.generate(
            topic="Sorting",
            activity_title="QuickSort",
            activity_description="Divide and conquer",
        )

        call_args = mock_retry.call_args
        messages = call_args.kwargs.get("messages", call_args.args[0] if call_args.args else [])
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "deep knowledge" in user_msg["content"]

    # 4. Invalid JSON -> fallback
    @patch("app.services.openai_client.call_with_retry")
    def test_generate_invalid_json_fallback(self, mock_retry):
        """GPT returns garbage -> fallback study cards."""
        mock_retry.return_value = _mock_openai_response("Not JSON at all!")

        result = self.svc.generate(
            topic="Recursion",
            activity_title="Learn Recursion",
            activity_description="Base case",
        )

        assert len(result["flashcards"]) == 3  # fallback has 3
        assert "Recursion" in result["flashcards"][0]["front"]

    # 5. Non-dict -> fallback
    @patch("app.services.openai_client.call_with_retry")
    def test_generate_non_dict_fallback(self, mock_retry):
        """GPT returns a list instead of dict -> fallback."""
        mock_retry.return_value = _mock_openai_response(json.dumps([1, 2, 3]))

        result = self.svc.generate(
            topic="Graphs",
            activity_title="BFS",
            activity_description="Breadth-first",
        )

        assert "flashcards" in result
        assert len(result["flashcards"]) == 3  # fallback

    # 6. Invalid category -> defaults to "concept"
    @patch("app.services.openai_client.call_with_retry")
    def test_validate_flashcard_invalid_category(self, mock_retry):
        """Flashcard with invalid category gets defaulted to 'concept'."""
        bad_cards = json.dumps({
            "flashcards": [
                {"front": "Q1", "back": "A1", "category": "invalid_cat"},
            ],
            "key_concepts": [],
            "comprehension_questions": [],
        })
        mock_retry.return_value = _mock_openai_response(bad_cards)

        result = self.svc.generate(topic="Test", activity_title="T", activity_description="D")

        assert result["flashcards"][0]["category"] == "concept"

    # 7. Direct fallback test
    def test_fallback_content(self):
        """_fallback returns 3 flashcards, 1 concept, 1 question with topic in them."""
        result = self.svc._fallback("Machine Learning")

        assert len(result["flashcards"]) == 3
        assert len(result["key_concepts"]) == 1
        assert len(result["comprehension_questions"]) == 1
        assert "Machine Learning" in result["flashcards"][0]["front"]
        assert result["key_concepts"][0]["importance"] == "critical"


# ===================================================================
# TestStudyCardsEndpoint  (integration tests)
# ===================================================================

class TestStudyCardsEndpoint:

    @pytest.fixture
    def integration_client(self):
        from tests.conftest import _engine, _TestingSessionLocal, _override_get_db
        from app.database import Base, get_db
        from app.main import app as fastapi_app
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=_engine)
        session = _TestingSessionLocal()

        fastapi_app.dependency_overrides[get_db] = _override_get_db
        from fastapi.testclient import TestClient
        with TestClient(fastapi_app) as c:
            yield {"client": c, "db": session}

        session.close()
        fastapi_app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=_engine)

    def _create_test_data(self, session):
        from app.models.user import User
        from app.models.smartstudy import StudyPlan, StudyPlanResource
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        user = User(
            id=uuid.uuid4(),
            email=f"reading_{uuid.uuid4().hex[:6]}@pau.edu.ng",
            password_hash=pwd_context.hash("TestPass123!"),
            full_name="Reading Test User",
            university_id=f"PAU/2022/{uuid.uuid4().hex[:3]}",
            entry_level="400L",
            target_cgpa=4.5,
            current_cgpa=3.5,
        )
        session.add(user)
        session.flush()

        plan = StudyPlan(
            id=uuid.uuid4(),
            user_id=user.id,
            topic="Data Structures",
            plan_data={
                "title": "Master Data Structures",
                "days": [{"day_number": 1, "activities": [{"difficulty": "medium"}]}],
                "_slide_content": "Slide content about stacks",
            },
            duration_days=7,
            start_date=date.today(),
            is_active=True,
            completion_percentage=0,
            completed_days=[],
        )
        session.add(plan)
        session.flush()

        resource = StudyPlanResource(
            id=uuid.uuid4(),
            study_plan_id=plan.id,
            resource_type="article",
            resource_title="Stacks Article",
            resource_description="Introduction to stacks",
            day_number=1,
            order_in_day=0,
            clicked=False,
            completed=False,
        )
        session.add(resource)
        session.commit()

        return {"user": user, "plan": plan, "resource": resource}

    def _auth_header(self, user):
        from app.utils.auth import create_access_token
        token = create_access_token(data={"sub": user.email, "user_id": str(user.id)})
        return {"Authorization": f"Bearer {token}"}

    # 8. Study cards endpoint success
    @patch("app.services.openai_client.call_with_retry")
    def test_study_cards_endpoint_success(self, mock_retry, integration_client):
        mock_retry.return_value = _mock_openai_response(VALID_STUDY_CARDS_JSON)

        import app.services.study_cards_service as sc_mod
        sc_mod._study_cards_service = None

        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{data['plan'].id}/resources/{data['resource'].id}/study-cards",
            headers=headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert "flashcards" in body
        assert "key_concepts" in body
        assert "comprehension_questions" in body
        assert body["plan_id"] == str(data["plan"].id)

        sc_mod._study_cards_service = None

    # 9. Unauthenticated
    def test_study_cards_unauthenticated(self, integration_client):
        c = integration_client["client"]
        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{uuid.uuid4()}/resources/{uuid.uuid4()}/study-cards"
        )
        assert resp.status_code == 401

    # 10. Plan not found
    def test_study_cards_plan_not_found(self, integration_client):
        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{uuid.uuid4()}/resources/{uuid.uuid4()}/study-cards",
            headers=headers,
        )
        assert resp.status_code == 404


# ===================================================================
# TestValidateStep  (unit + integration tests)
# ===================================================================

class TestValidateStep:

    @pytest.fixture
    def integration_client(self):
        from tests.conftest import _engine, _TestingSessionLocal, _override_get_db
        from app.database import Base, get_db
        from app.main import app as fastapi_app
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=_engine)
        session = _TestingSessionLocal()

        fastapi_app.dependency_overrides[get_db] = _override_get_db
        from fastapi.testclient import TestClient
        with TestClient(fastapi_app) as c:
            yield {"client": c, "db": session}

        session.close()
        fastapi_app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=_engine)

    def _create_test_data(self, session):
        from app.models.user import User
        from app.models.smartstudy import StudyPlan, StudyPlanResource
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        user = User(
            id=uuid.uuid4(),
            email=f"guided_{uuid.uuid4().hex[:6]}@pau.edu.ng",
            password_hash=pwd_context.hash("TestPass123!"),
            full_name="Guided Solver User",
            university_id=f"PAU/2022/{uuid.uuid4().hex[:3]}",
            entry_level="400L",
            target_cgpa=4.5,
            current_cgpa=3.5,
        )
        session.add(user)
        session.flush()

        plan = StudyPlan(
            id=uuid.uuid4(),
            user_id=user.id,
            topic="Algorithms",
            plan_data={"title": "Algo Plan", "days": [{"day_number": 1, "activities": []}]},
            duration_days=7,
            start_date=date.today(),
            is_active=True,
            completion_percentage=0,
            completed_days=[],
        )
        session.add(plan)
        session.flush()

        resource = StudyPlanResource(
            id=uuid.uuid4(),
            study_plan_id=plan.id,
            resource_type="practice",
            resource_title="Binary Search Practice",
            day_number=1,
            order_in_day=0,
            clicked=False,
            completed=False,
        )
        session.add(resource)
        session.commit()

        return {"user": user, "plan": plan, "resource": resource}

    def _auth_header(self, user):
        from app.utils.auth import create_access_token
        token = create_access_token(data={"sub": user.email, "user_id": str(user.id)})
        return {"Authorization": f"Bearer {token}"}

    # 11. Correct answer
    @patch("app.services.openai_client.call_with_retry")
    def test_validate_step_correct(self, mock_retry, integration_client):
        mock_retry.return_value = _mock_openai_response(json.dumps({
            "correct": True,
            "feedback": "Great work! Your implementation is correct.",
            "hint": None,
        }))

        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{data['plan'].id}/resources/{data['resource'].id}/exercises/validate-step",
            headers=headers,
            json={
                "exercise_title": "Implement Binary Search",
                "step_text": "Write a function that takes a sorted array",
                "student_answer": "def binary_search(arr, target): ...",
                "topic": "Binary Search",
            },
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["correct"] is True
        assert "feedback" in body

    # 12. Incorrect answer with hint
    @patch("app.services.openai_client.call_with_retry")
    def test_validate_step_incorrect(self, mock_retry, integration_client):
        mock_retry.return_value = _mock_openai_response(json.dumps({
            "correct": False,
            "feedback": "Not quite — you're using linear search instead.",
            "hint": "Try dividing the array in half each time.",
        }))

        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{data['plan'].id}/resources/{data['resource'].id}/exercises/validate-step",
            headers=headers,
            json={
                "exercise_title": "Implement Binary Search",
                "step_text": "Implement the comparison logic",
                "student_answer": "for i in range(len(arr)): if arr[i] == target: return i",
                "topic": "Binary Search",
            },
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["correct"] is False
        assert body["hint"] is not None

    # 13. GPT failure -> graceful fallback
    @patch("app.services.openai_client.call_with_retry")
    def test_validate_step_gpt_failure(self, mock_retry, integration_client):
        mock_retry.side_effect = Exception("OpenAI timeout")

        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{data['plan'].id}/resources/{data['resource'].id}/exercises/validate-step",
            headers=headers,
            json={
                "exercise_title": "Test",
                "step_text": "Do something",
                "student_answer": "my answer",
                "topic": "Test",
            },
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["correct"] is None
        assert "mark this step yourself" in body["feedback"].lower()

    # 14. Unauthenticated
    def test_validate_step_unauthenticated(self, integration_client):
        c = integration_client["client"]
        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{uuid.uuid4()}/resources/{uuid.uuid4()}/exercises/validate-step",
            json={"student_answer": "test"},
        )
        assert resp.status_code == 401
```

**Step 2: Run the new tests**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && source venv/bin/activate && TESTING=true pytest tests/test_services/test_study_cards_and_guided.py -v`
Expected: 14 tests PASS

**Step 3: Run full test suite**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && TESTING=true pytest tests/ -x -q`
Expected: ~1006 tests pass (992 existing + 14 new), 0 failures

**Step 4: Verify frontend builds**

Run: `cd /Users/useruser/Documents/shadow-final-year/frontend && npx vite build 2>&1 | tail -5`
Expected: Clean build, no errors

---

## Verification Checklist

1. `TESTING=true pytest tests/test_services/test_study_cards_and_guided.py -v` — 14 new tests pass
2. `TESTING=true pytest tests/ -x -q` — all ~1006 tests pass
3. `cd frontend && npx vite build` — clean build
4. Reading learner form hint appears when "Reading" style selected
5. Study cards generate button visible for reading learners
6. Kinesthetic exercises show input fields in guided mode
7. Validate-step endpoint returns correct/incorrect with feedback

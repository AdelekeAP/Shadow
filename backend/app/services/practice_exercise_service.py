"""
Practice Exercise Service
Generates hands-on practice exercises for kinesthetic learners using GPT.
Uses shared OpenAI infrastructure (call_with_retry) for exercise generation.
"""
import asyncio
import json
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class PracticeExerciseService:
    """Generates structured practice exercises for kinesthetic learners."""

    async def generate_exercises(
        self,
        topic: str,
        activity_title: str,
        activity_description: str,
        slide_content: str = "",
        difficulty: str = "medium",
    ) -> List[Dict]:
        """
        Use GPT to generate hands-on practice exercises for a study activity.

        Returns a list of exercise dicts with title, instructions, steps,
        difficulty, estimated_minutes, and exercise_type.
        """
        from app.services.openai_client import call_with_retry, PLAN_MODELS

        if slide_content:
            source_block = f"""
**ACTUAL SLIDE/LECTURE CONTENT (this is what the student is studying)**:
---
{slide_content[:6000]}
---

CRITICAL RULES:
- Every exercise MUST be based on specific concepts, examples, or problems from the slide content above
- Do NOT invent topics, examples, or problems that are not in the slides
- Reference specific terms, formulas, definitions, or examples from the slides
- If the slides discuss "regression analysis", exercises must be about regression analysis — NOT about unrelated topics like payroll or environment setup
- If the slides contain code examples, exercises should extend or modify those examples
- Do NOT generate generic "set up your environment" or "install tools" exercises unless the slides are specifically about installation"""
        else:
            source_block = f"""
No slides were uploaded. Create exercises based on standard university curriculum for {topic}.
Focus on core concepts and practical application — not setup or tooling."""

        prompt = f"""Generate 3–5 hands-on practice exercises for a university student.

**Topic**: {topic}
**Activity**: {activity_title}
**Activity Description**: {activity_description}
**Target Difficulty**: {difficulty}
{source_block}

Return ONLY valid JSON — an array of exercise objects. Each object must have:
- "title": short exercise name that references a SPECIFIC concept from the material (5-10 words)
- "instructions": clear 1-2 sentence description grounded in the actual material
- "steps": array of 3-6 concrete step-by-step instructions
- "difficulty": "easy", "medium", or "hard"
- "estimated_minutes": integer (5-30)
- "exercise_type": one of "code_challenge", "worked_example", "diagram_drawing", "explain_aloud", "build_project", "debug_exercise", "compare_contrast"
- "language": for code_challenge/debug_exercise, the programming language to use (e.g., "python", "javascript", "java", "cpp", "c", "sql", "r"). Detect from the topic/slides — do NOT default to JavaScript. For non-code exercises, use null.
- "starter_code": for code_challenge/debug_exercise ONLY, provide starter code the student should begin with. For debug_exercise, include the BUGGY code. For code_challenge, provide a skeleton. Use null for non-code exercises.
- "success_criteria": how the student knows they completed it correctly

Guidelines:
- Exercises MUST test the actual concepts in the slides — not generic or tangentially related topics
- Exercises should be ACTIVE — coding, building, drawing, explaining, debugging
- Progress from easier to harder
- For mathematical topics: include worked examples using formulas/methods FROM the slides
- For programming topics: exercises should use the same language/framework as the slides
- For conceptual topics: test understanding of the specific theories and models in the slides
- NEVER generate exercises about: setting up environments, installing software, class rules, or course administration

CODE CHALLENGE REQUIREMENT — VERY IMPORTANT:
- If the topic involves ANY programming, data science, machine learning, algorithms, or quantitative methods, you MUST include at least 2 exercises with exercise_type "code_challenge"
- Code challenges should ask students to WRITE actual code: implement an algorithm, compute a formula, process data, train a model, etc.
- For machine learning topics: code challenges in Python (scikit-learn, numpy, pandas) — e.g., "Implement linear regression from scratch", "Train a decision tree classifier", "Compute gradient descent step by step"
- For algorithm topics: code challenges that implement the algorithm
- Code challenges are completed in an in-app code editor — students write and submit real code
- Also include at least 1 "debug_exercise" if the topic involves code — give broken code and ask students to find and fix the bug"""

        response = await asyncio.to_thread(
            call_with_retry,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert educational content creator specializing in "
                        "hands-on, active learning exercises for university students. "
                        "When slide content is provided, exercises MUST be grounded in "
                        "that specific material — never invent unrelated topics. "
                        "Return only valid JSON arrays."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            models=PLAN_MODELS,
            temperature=0.7,
            max_tokens=2000,
            timeout=30.0,
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
            exercises = json.loads(raw)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse exercises JSON: {raw[:200]}")
            return self._fallback_exercises(topic, activity_title, difficulty)

        if not isinstance(exercises, list):
            logger.warning("GPT returned non-list exercises, using fallback")
            return self._fallback_exercises(topic, activity_title, difficulty)

        # Validate and sanitize each exercise
        validated = []
        for ex in exercises:
            if not isinstance(ex, dict) or "title" not in ex:
                continue
            exercise_type = str(ex.get("exercise_type", "worked_example"))
            # Only pass language/starter_code for code exercises
            is_code_exercise = exercise_type in ("code_challenge", "debug_exercise")
            exercise_data = {
                "title": str(ex.get("title", "Practice Exercise")),
                "instructions": str(ex.get("instructions", "")),
                "steps": ex.get("steps", []) if isinstance(ex.get("steps"), list) else [],
                "difficulty": ex.get("difficulty", difficulty) if ex.get("difficulty") in ("easy", "medium", "hard") else difficulty,
                "estimated_minutes": min(max(int(ex.get("estimated_minutes", 15)), 5), 60),
                "exercise_type": exercise_type,
                "success_criteria": str(ex.get("success_criteria", "")),
            }
            if is_code_exercise:
                lang = ex.get("language")
                exercise_data["language"] = str(lang).lower() if lang else None
                starter = ex.get("starter_code")
                exercise_data["starter_code"] = str(starter) if starter else None
            validated.append(exercise_data)

        if not validated:
            return self._fallback_exercises(topic, activity_title, difficulty)

        logger.info(f"Generated {len(validated)} practice exercises for '{topic}'")
        return validated

    def _fallback_exercises(self, topic: str, activity_title: str, difficulty: str) -> List[Dict]:
        """Return minimal fallback exercises when GPT generation fails."""
        return [
            {
                "title": f"Explain {topic} in Your Own Words",
                "instructions": "Without looking at any notes, explain the core concepts aloud or in writing.",
                "steps": [
                    "Close all reference material",
                    "Set a 5-minute timer",
                    f"Explain {topic} as if teaching a classmate",
                    "Note any gaps in your understanding",
                    "Review the material to fill those gaps",
                ],
                "difficulty": "easy",
                "estimated_minutes": 10,
                "exercise_type": "explain_aloud",
                "success_criteria": "You can explain the core concepts without hesitation",
                "is_fallback": True,
            },
            {
                "title": f"Apply {topic} to a Real Problem",
                "instructions": f"Take the concepts from '{activity_title}' and solve a concrete problem.",
                "steps": [
                    f"Identify a real-world scenario where {topic} applies",
                    "Break down the problem into steps",
                    "Work through the solution manually",
                    "Verify your answer",
                ],
                "difficulty": difficulty,
                "estimated_minutes": 20,
                "exercise_type": "worked_example",
                "success_criteria": "You solved a real problem using the concepts correctly",
                "is_fallback": True,
            },
        ]


# Singleton
_practice_exercise_service: Optional[PracticeExerciseService] = None


def get_practice_exercise_service() -> PracticeExerciseService:
    """Get or create PracticeExerciseService singleton."""
    global _practice_exercise_service
    if _practice_exercise_service is None:
        _practice_exercise_service = PracticeExerciseService()
    return _practice_exercise_service

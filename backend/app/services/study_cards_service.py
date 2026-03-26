"""
Study Cards Service
Generates flashcards, key concepts, and comprehension questions for reading learners.
Uses shared OpenAI infrastructure (call_with_retry) for content generation.
"""
import asyncio
import json
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class StudyCardsService:
    """Generates structured study cards for reading learners."""

    async def generate(
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
**ACTUAL SLIDE/LECTURE CONTENT (this is what the student is studying)**:
---
{slide_content[:6000]}
---

CRITICAL RULES:
- Every flashcard, concept, and question MUST come from the slide content above
- Use the EXACT terminology, definitions, and formulas from the slides
- Do NOT add concepts that are not in the slides
- Reference specific slide examples, diagrams, or case studies mentioned in the content
- If slides define a term, the flashcard should use that exact definition"""
        else:
            source_block = f"""
No slides were uploaded. Create study materials based on standard university curriculum for {topic}.
Focus on the most important concepts a student would need to know."""

        prompt = f"""Generate a complete study card set for a university student.

**Topic**: {topic}
**Activity**: {activity_title}
**Activity Description**: {activity_description}
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

        response = await asyncio.to_thread(
            call_with_retry,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert educational content creator specializing in "
                        "study materials for university students. You create flashcards, "
                        "concept summaries, and comprehension questions. "
                        "When slide content is provided, ALL materials MUST come directly "
                        "from that content — never add concepts not in the slides. "
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
            "is_fallback": True,
        }


# Singleton
_study_cards_service: Optional[StudyCardsService] = None


def get_study_cards_service() -> StudyCardsService:
    """Get or create StudyCardsService singleton."""
    global _study_cards_service
    if _study_cards_service is None:
        _study_cards_service = StudyCardsService()
    return _study_cards_service

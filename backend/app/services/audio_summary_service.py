"""
Audio Summary Service
Generates podcast-style audio summaries using GPT (script) + hybrid TTS (ElevenLabs premium + OpenAI nova fallback).
Uses shared OpenAI infrastructure (call_with_retry) for script generation.

TTS Strategy:
  - ElevenLabs (Rachel voice): Used for primary/first audio activity per day — premium quality
  - OpenAI TTS (nova voice, tts-1-hd): Used for all other audio + automatic fallback when ElevenLabs fails
"""
import asyncio
import os
import logging
from typing import Optional
from dotenv import load_dotenv

import httpx

load_dotenv()

logger = logging.getLogger(__name__)

# Audio cache directory
AUDIO_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "audio_cache"
)

# ElevenLabs defaults
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"
# "Rachel" — clear, warm, educational tone
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

# Maximum script length to stay under ElevenLabs 5000 char limit
MAX_SCRIPT_CHARS = 4500

# OpenAI TTS defaults
OPENAI_TTS_MODEL = "tts-1-hd"
OPENAI_TTS_VOICE = "nova"  # Most natural-sounding OpenAI voice


class AudioSummaryService:
    """Generates audio summaries for study plan activities with hybrid TTS."""

    def __init__(self):
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self._openai_client = None

        if self.elevenlabs_api_key:
            logger.info("ElevenLabs TTS initialized (premium provider)")
        else:
            logger.warning("ELEVENLABS_API_KEY not set — ElevenLabs unavailable")

        # Check OpenAI availability for fallback TTS
        try:
            from app.services.openai_client import get_openai_client
            if get_openai_client() is not None:
                logger.info("OpenAI TTS (nova) initialized as secondary provider")
        except Exception:
            logger.warning("OpenAI client not available for TTS fallback")

        # Ensure cache directory exists
        os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)

    @property
    def is_available(self) -> bool:
        """Audio is available if we have at least one TTS provider + OpenAI for scripts."""
        from app.services.openai_client import get_openai_client
        has_script_gen = get_openai_client() is not None
        has_any_tts = self.elevenlabs_api_key is not None or has_script_gen
        return has_script_gen and has_any_tts

    async def generate_script(self, topic: str, activity_title: str, activity_description: str, slide_content: str = "") -> str:
        """
        Use GPT to write a conversational podcast-style script (500-800 words).
        Uses shared call_with_retry infrastructure for model fallback and retries.
        """
        from app.services.openai_client import call_with_retry, PLAN_MODELS

        # Build prompt — include slide content when available for richer scripts
        if slide_content:
            prompt = f"""Write a conversational, podcast-style audio summary about the following study topic and activity.
The summary should be engaging and educational, as if a knowledgeable friend is explaining the concepts to a student.

**Topic**: {topic}
**Activity**: {activity_title}
**Activity Description**: {activity_description}

**ACTUAL SLIDE/LECTURE CONTENT**:
---
{slide_content[:6000]}
---

CRITICAL: Base the script on the ACTUAL slide content above. Explain the specific concepts, definitions, formulas, and examples from the slides. Do NOT discuss unrelated topics or generic introductions that aren't in the material.

Guidelines:
- Write 500-800 words in a natural, spoken style
- Start with a brief hook/intro
- Cover the key concepts from the slides clearly and comprehensively
- Use examples and analogies where helpful
- End with a quick recap of the main takeaways
- Do NOT include speaker labels, timestamps, or stage directions
- Write as continuous flowing text that reads well aloud

Output only the script text, nothing else."""
        else:
            prompt = f"""Write a conversational, podcast-style audio lecture about the following study topic and activity.
The script should be a thorough educational explanation — as if a knowledgeable professor is giving a mini-lecture to help a student truly understand the material.

**Topic**: {topic}
**Activity**: {activity_title}
**Details**: {activity_description}

Guidelines:
- Write 500-800 words in a natural, spoken style
- Start with a brief hook that frames why this topic matters
- Explain the core concepts, definitions, and principles in depth
- Use concrete examples, analogies, and real-world applications
- Address common misconceptions or tricky parts students struggle with
- End with a clear recap of the 3-5 most important takeaways
- Do NOT include speaker labels, timestamps, or stage directions
- Write as continuous flowing text that reads well aloud

Output only the script text, nothing else."""

        response = await asyncio.to_thread(
            call_with_retry,
            messages=[
                {
                    "role": "system",
                    "content": "You are an educational content creator who writes engaging audio scripts for university students."
                },
                {"role": "user", "content": prompt}
            ],
            models=PLAN_MODELS,
            temperature=0.7,
            max_tokens=1500,
            timeout=30.0,
        )

        script = response.choices[0].message.content.strip()

        # Truncate to stay under ElevenLabs 5000 char limit
        if len(script) > MAX_SCRIPT_CHARS:
            script = script[:MAX_SCRIPT_CHARS].rsplit('.', 1)[0] + '.'
            logger.info(f"Truncated audio script to {len(script)} characters (limit: {MAX_SCRIPT_CHARS})")

        logger.info(f"Generated audio script: {len(script)} characters, ~{len(script.split())} words")
        return script

    def synthesize_elevenlabs(self, script: str, voice_id: str = None) -> bytes:
        """Convert script text to MP3 audio using ElevenLabs TTS API (premium)."""
        if not self.elevenlabs_api_key:
            raise RuntimeError("ElevenLabs API key not configured")

        voice_id = voice_id or DEFAULT_VOICE_ID
        url = f"{ELEVENLABS_TTS_URL}/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key,
        }

        payload = {
            "text": script,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            }
        }

        import httpx
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=payload, headers=headers)

        if response.status_code == 401:
            raise RuntimeError("Invalid ElevenLabs API key")
        elif response.status_code == 429:
            raise RuntimeError("ElevenLabs rate limit exceeded — try again later")
        elif response.status_code == 422:
            raise RuntimeError("Script too long for ElevenLabs (max 5000 chars)")
        response.raise_for_status()

        audio_bytes = response.content

        # Validate we got actual audio, not an error page
        if not (audio_bytes[:3] == b'ID3' or audio_bytes[:2] == b'\xff\xfb'):
            raise RuntimeError("ElevenLabs returned invalid audio data")

        logger.info(f"ElevenLabs synthesized audio: {len(audio_bytes)} bytes")
        return audio_bytes

    def synthesize_openai(self, script: str) -> bytes:
        """Convert script text to MP3 audio using OpenAI TTS API (nova voice)."""
        from app.services.openai_client import get_openai_client

        client = get_openai_client()
        if client is None:
            raise RuntimeError("OpenAI client not available for TTS")

        response = client.audio.speech.create(
            model=OPENAI_TTS_MODEL,
            voice=OPENAI_TTS_VOICE,
            input=script,
            response_format="mp3",
            timeout=60.0,
        )

        audio_bytes = response.content

        if len(audio_bytes) < 100:
            raise RuntimeError("OpenAI TTS returned unexpectedly small audio")

        logger.info(f"OpenAI TTS (nova) synthesized audio: {len(audio_bytes)} bytes")
        return audio_bytes

    def synthesize_audio(self, script: str, provider: str = "elevenlabs") -> tuple:
        """
        Synthesize audio with the specified provider, falling back automatically.

        Returns: (audio_bytes, provider_used)
        """
        if provider == "elevenlabs" and self.elevenlabs_api_key:
            try:
                audio = self.synthesize_elevenlabs(script)
                return audio, "elevenlabs"
            except Exception as e:
                logger.warning(f"ElevenLabs TTS failed, falling back to OpenAI nova: {e}")
                # Fall through to OpenAI
        elif provider == "elevenlabs" and not self.elevenlabs_api_key:
            logger.info("ElevenLabs not configured, using OpenAI nova")

        # OpenAI TTS fallback / secondary provider
        try:
            audio = self.synthesize_openai(script)
            return audio, "openai"
        except Exception as e:
            raise RuntimeError(f"All TTS providers failed. Last error: {e}")

    async def get_or_generate(
        self,
        resource_id: str,
        topic: str,
        title: str,
        description: str,
        slide_content: str = "",
        provider: str = "elevenlabs",
    ) -> dict:
        """
        Get cached audio or generate new.
        Returns dict with 'filepath', 'script', and 'provider' info.
        """
        filepath = os.path.join(AUDIO_CACHE_DIR, f"{resource_id}.mp3")

        # Return cached file if it exists
        if os.path.isfile(filepath):
            logger.info(f"Audio cache hit: {resource_id}")
            return {"filepath": filepath, "script": None, "provider": "cached"}

        # Generate script
        script = await self.generate_script(topic, title, description, slide_content)

        # Synthesize audio with automatic fallback (run in thread to avoid blocking event loop)
        try:
            audio_bytes, provider_used = await asyncio.to_thread(self.synthesize_audio, script, provider)
        except Exception as tts_err:
            logger.warning(f"All TTS synthesis failed, returning script only: {tts_err}")
            return {"filepath": None, "script": script, "tts_failed": True, "tts_error": str(tts_err)}

        # Write to cache
        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        logger.info(f"Generated and cached audio ({provider_used}): {filepath}")
        return {"filepath": filepath, "script": script, "provider": provider_used}


# Singleton
_audio_summary_service: Optional[AudioSummaryService] = None


def get_audio_summary_service() -> AudioSummaryService:
    """Get or create AudioSummaryService singleton."""
    global _audio_summary_service
    if _audio_summary_service is None:
        _audio_summary_service = AudioSummaryService()
    return _audio_summary_service

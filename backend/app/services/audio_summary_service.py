"""
Audio Summary Service
Generates podcast-style audio summaries using GPT-4 (script) + ElevenLabs (voice).
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv

import requests

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


class AudioSummaryService:
    """Generates audio summaries for study plan activities."""

    def __init__(self):
        from app.services.openai_client import get_openai_client
        self.openai_client = get_openai_client()
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

        if self.elevenlabs_api_key:
            logger.info("ElevenLabs TTS initialized for audio summaries")
        else:
            logger.warning("ELEVENLABS_API_KEY not set — audio generation disabled")

        # Ensure cache directory exists
        os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)

    @property
    def is_available(self) -> bool:
        return self.openai_client is not None and self.elevenlabs_api_key is not None

    def generate_script(self, topic: str, activity_title: str, activity_description: str) -> str:
        """
        Use GPT-4 to write a conversational podcast-style script (500-800 words).
        """
        if not self.openai_client:
            raise RuntimeError("OpenAI client not available for script generation")

        prompt = f"""Write a conversational, podcast-style audio summary about the following study topic and activity.
The summary should be engaging and educational, as if a knowledgeable friend is explaining the concepts to a student.

**Topic**: {topic}
**Activity**: {activity_title}
**Details**: {activity_description}

Guidelines:
- Write 500-800 words in a natural, spoken style
- Start with a brief hook/intro
- Cover the key concepts clearly
- Use examples and analogies where helpful
- End with a quick recap of the main takeaways
- Do NOT include speaker labels, timestamps, or stage directions
- Write as continuous flowing text that reads well aloud

Output only the script text, nothing else."""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an educational content creator who writes engaging audio scripts for university students."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        script = response.choices[0].message.content.strip()
        logger.info(f"Generated audio script: {len(script)} characters, ~{len(script.split())} words")
        return script

    def synthesize_audio(self, script: str, voice_id: str = None) -> bytes:
        """
        Convert script text to MP3 audio using ElevenLabs TTS API.
        """
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

        response = requests.post(url, json=payload, headers=headers, timeout=120)

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

    def get_or_generate(
        self,
        resource_id: str,
        topic: str,
        title: str,
        description: str,
    ) -> dict:
        """
        Get cached audio or generate new.
        Returns dict with 'filepath' and 'script' (None if cached).
        """
        filepath = os.path.join(AUDIO_CACHE_DIR, f"{resource_id}.mp3")

        # Return cached file if it exists
        if os.path.isfile(filepath):
            logger.info(f"Audio cache hit: {resource_id}")
            return {"filepath": filepath, "script": None}

        # Generate script
        script = self.generate_script(topic, title, description)

        # Synthesize audio — gracefully degrade to script-only on TTS failure
        try:
            audio_bytes = self.synthesize_audio(script)
        except Exception as tts_err:
            logger.warning(f"TTS synthesis failed, returning script only: {tts_err}")
            return {"filepath": None, "script": script, "tts_failed": True, "tts_error": str(tts_err)}

        # Write to cache
        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        logger.info(f"Generated and cached audio: {filepath}")
        return {"filepath": filepath, "script": script}


# Singleton
_audio_summary_service: Optional[AudioSummaryService] = None


def get_audio_summary_service() -> AudioSummaryService:
    """Get or create AudioSummaryService singleton."""
    global _audio_summary_service
    if _audio_summary_service is None:
        _audio_summary_service = AudioSummaryService()
    return _audio_summary_service

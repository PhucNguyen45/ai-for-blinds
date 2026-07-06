"""
Edge TTS service — Vietnamese text-to-speech with natural voices.

Uses Edge TTS for high-quality Vietnamese speech synthesis.
Supports the Microsoft Hoai My neural voice (vi-VN-HoaiMyNeural).
"""

import logging
import os
import tempfile
import uuid
from typing import Optional


logger = logging.getLogger(__name__)

import edge_tts

from backend.config import settings


class TtsService:
    """Convert text to speech using Edge TTS with Vietnamese voices."""

    def __init__(self) -> None:
        os.makedirs(settings.tts_output_dir, exist_ok=True)

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
    ) -> Optional[str]:
        """
        Synthesize Vietnamese speech from text.

        Args:
            text: Vietnamese text to read aloud.
            voice: Edge TTS voice name (default: vi-VN-HoaiMyNeural).

        Returns:
            Path to the generated MP3 file, or None on failure.
        """
        if not text or not text.strip():
            return None

        voice = voice or settings.tts_voice
        output_path = os.path.join(
            settings.tts_output_dir,
            f"sgbe_tts_{uuid.uuid4().hex}.mp3",
        )

        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)

            if not os.path.exists(output_path):
                return None

            return output_path
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return None

    async def synthesize_with_emotion(
        self,
        text: str,
        emotion: str = "neutral",
        voice: Optional[str] = None,
    ) -> Optional[str]:
        """
        Synthesize speech with emotional tone (for literature reading).

        Note: Edge TTS doesn't natively support emotion parameters.
        This method adjusts voice style via SSML where possible.

        Args:
            text: Vietnamese text to read aloud.
            emotion: Emotional tone (neutral, happy, sad, angry, excited).
            voice: Edge TTS voice name.

        Returns:
            Path to MP3 file, or None on failure.
        """
        voice = voice or settings.tts_voice
        output_path = os.path.join(
            settings.tts_output_dir,
            f"sgbe_tts_{uuid.uuid4().hex}.mp3",
        )

        try:
            # Use SSML with prosody adjustments for emotional reading
            rate_map = {
                "happy": "+15%",
                "sad": "-10%",
                "angry": "+10%",
                "excited": "+20%",
                "neutral": "+0%",
            }
            pitch_map = {
                "happy": "+2st",
                "sad": "-2st",
                "angry": "+1st",
                "excited": "+3st",
                "neutral": "+0st",
            }

            rate = rate_map.get(emotion, "+0%")
            pitch = pitch_map.get(emotion, "+0st")

            ssml = (
                f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
                f'xml:lang="vi-VN">'
                f'<voice name="{voice}">'
                f'<prosody rate="{rate}" pitch="{pitch}">'
                f'{text}'
                f'</prosody>'
                f'</voice>'
                f'</speak>'
            )

            communicate = edge_tts.Communicate(ssml, voice)
            await communicate.save(output_path)

            if not os.path.exists(output_path):
                return None

            return output_path
        except Exception as e:
            logger.error(f"TTS emotional synthesis error: {e}")
            # Fallback to plain synthesis
            return await self.synthesize(text, voice)


# Singleton instance
tts_service = TtsService()

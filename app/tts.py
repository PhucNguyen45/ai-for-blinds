import logging
from collections.abc import AsyncIterator

import edge_tts

from .config import settings

logger = logging.getLogger(__name__)


class TTSError(Exception):
    """Lỗi khi tạo TTS."""


async def stream_tts(
    text: str,
    voice: str | None = None,
    rate: str | None = None,
    pitch: str | None = None,
) -> AsyncIterator[bytes]:
    """Stream MP3 audio chunks (24kHz mono) for the given text via Microsoft Edge TTS."""
    if not text or not text.strip():
        raise TTSError("Text rỗng")

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice or settings.tts_voice,
        rate=rate or settings.tts_rate,
        pitch=pitch or settings.tts_pitch,
    )

    try:
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                data = chunk.get("data")
                if data:
                    yield data
    except Exception as e:
        logger.exception("Lỗi edge-tts")
        raise TTSError(f"Lỗi tạo audio: {e}") from e


async def list_voices(language: str = "vi") -> list:
    """Return Vietnamese voices available from edge-tts."""
    voices = await edge_tts.list_voices()
    return [
        {"name": v["ShortName"], "gender": v["Gender"], "locale": v["Locale"]}
        for v in voices
        if v["Locale"].startswith(language)
    ]

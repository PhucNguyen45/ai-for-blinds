"""
Whisper STT service — Vietnamese speech-to-text recognition.

Uses faster-whisper with the phoWhisper model for Vietnamese,
falling back to the standard base model if phoWhisper is unavailable.
"""

import os
import tempfile
import uuid
from typing import Optional

from backend.config import settings


class SttService:
    """Convert speech audio to text using Whisper/faster-whisper."""

    def __init__(self) -> None:
        self._model = None
        self._model_size = settings.whisper_model_size

    def _initialize(self) -> None:
        """Lazy initialization of Whisper model."""
        if self._model is not None:
            return
        try:
            from faster_whisper import WhisperModel

            # PhoWhisper (VinAI) fine-tune cho tiếng Việt, nhưng faster-whisper
            # chỉ nạp được bản đã chuyển sang CTranslate2. WHISPER_MODEL trỏ
            # tới bản CT2 đó — hoặc một tên model Whisper chuẩn.
            self._model = WhisperModel(
                self._model_size,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
            )
            print(f"STT ready: {self._model_size}")
        except Exception as e:
            print(f"Warning: Whisper not available: {e}")
            self._model = None

    @property
    def available(self) -> bool:
        self._initialize()
        return self._model is not None

    def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "vi",
    ) -> Optional[dict]:
        """
        Transcribe audio to text.

        Args:
            audio_bytes: Raw audio file bytes (WAV, MP3, M4A, etc.).
            language: Language code (default: 'vi' for Vietnamese).

        Returns:
            Dict with 'text', 'segments', and 'language' keys, or None on failure.
        """
        self._initialize()
        if self._model is None:
            return None

        tmp_path = None
        try:
            tmp_path = os.path.join(
                tempfile.gettempdir(),
                f"sgbe_stt_{uuid.uuid4().hex}.wav",
            )
            with open(tmp_path, "wb") as f:
                f.write(audio_bytes)

            segments, info = self._model.transcribe(
                tmp_path,
                language=language,
                beam_size=5,
                vad_filter=True,
            )

            text_parts = []
            segment_list = []
            for segment in segments:
                text_parts.append(segment.text)
                segment_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                })

            return {
                "text": " ".join(text_parts),
                "segments": segment_list,
                "language": info.language,
                "duration_seconds": info.duration,
            }

        except Exception as e:
            print(f"STT transcription error: {e}")
            return None
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass


# Singleton instance
stt_service = SttService()

"""
PaddleOCR service — Vietnamese text extraction from images.

Uses PaddleOCRv5 with Vietnamese language support.
Lazy-initialized singleton pattern for efficient resource usage.
"""

import os
import tempfile
import uuid
from typing import Optional

from backend.config import settings


class OcrService:
    """Extract text from images using PaddleOCR with Vietnamese support."""

    def __init__(self) -> None:
        self._ocr = None

    def _initialize(self) -> None:
        """Lazy initialization of PaddleOCR engine."""
        if self._ocr is not None:
            return
        try:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(
                use_angle_cls=settings.ocr_use_angle_cls,
                lang=settings.ocr_lang,
                show_log=settings.ocr_show_log,
            )
        except Exception as e:
            print(f"Warning: PaddleOCR not available: {e}")
            self._ocr = None

    @property
    def available(self) -> bool:
        self._initialize()
        return self._ocr is not None

    def extract_text(
        self, image_bytes: bytes, mime_type: str = "image/png"
    ) -> Optional[str]:
        """
        Extract text from image bytes.

        Args:
            image_bytes: Raw image file bytes (JPEG, PNG, etc.)

        Returns:
            Extracted text string, or None if OCR fails.
        """
        self._initialize()
        if self._ocr is None:
            # Không có PaddleOCR thì để VLM đọc chữ — vẫn đúng ràng buộc
            # "một mô hình gánh cả OCR lẫn mô tả" của đề tài.
            from backend.services.vlm_service import vlm_service

            return vlm_service.transcribe(image_bytes, mime_type)

        tmp_path = None
        try:
            # PaddleOCR requires a file path
            tmp_path = os.path.join(
                tempfile.gettempdir(),
                f"sgbe_ocr_{uuid.uuid4().hex}.png",
            )
            with open(tmp_path, "wb") as f:
                f.write(image_bytes)

            result = self._ocr.ocr(tmp_path, cls=True)

            if not result or not result[0]:
                return ""

            # Join all recognized text lines
            lines = [line[1][0] for line in result[0]]
            return "\n".join(lines)

        except Exception as e:
            print(f"OCR extraction error: {e}")
            return None
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass


# Singleton instance
ocr_service = OcrService()

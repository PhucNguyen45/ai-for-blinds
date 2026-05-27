"""
Gemini Vision service — image description and scene understanding.

Uses Gemini 2.5 Flash to describe images in Vietnamese.
Provides rich, contextual descriptions tailored for blind students.
"""

import os
from typing import Optional

import google.generativeai as genai

from backend.config import settings


class VlmService:
    """
    Vision-Language Model service using Gemini 2.5 Flash.

    Generates detailed Vietnamese descriptions of images for blind students.
    """

    def __init__(self) -> None:
        settings.validate()
        genai.configure(api_key=settings.google_api_key)
        self._model = genai.GenerativeModel(settings.gemini_model)

    def describe(self, image_bytes: bytes, mime_type: str) -> Optional[str]:
        """
        Describe an image in Vietnamese.

        Args:
            image_bytes: Raw image data.
            mime_type: MIME type of the image (e.g., 'image/jpeg').

        Returns:
            Vietnamese description string, or None on failure.
        """
        try:
            response = self._model.generate_content([
                (
                    "Bạn là trợ lý cho học sinh khiếm thị Việt Nam. "
                    "Hãy mô tả chi tiết bức ảnh này bằng tiếng Việt một cách "
                    "tự nhiên, dễ hiểu. Nếu ảnh có văn bản, hãy đọc nội dung "
                    "văn bản đó. Nếu ảnh có biểu đồ, hãy mô tả số liệu và xu hướng."
                ),
                {"mime_type": mime_type, "data": image_bytes},
            ])
            return response.text
        except Exception as e:
            print(f"Gemini description error: {e}")
            return None

    def describe_with_context(
        self, image_bytes: bytes, mime_type: str, context: str
    ) -> Optional[str]:
        """
        Describe an image with additional context (e.g., textbook chapter).

        Args:
            image_bytes: Raw image data.
            mime_type: MIME type of the image.
            context: Additional context about what the student is studying.

        Returns:
            Vietnamese description string, or None on failure.
        """
        try:
            response = self._model.generate_content([
                (
                    f"Bạn là trợ lý cho học sinh khiếm thị Việt Nam. "
                    f"Học sinh đang học về: {context}. "
                    f"Hãy mô tả chi tiết bức ảnh này bằng tiếng Việt, "
                    f"liên hệ với nội dung đang học."
                ),
                {"mime_type": mime_type, "data": image_bytes},
            ])
            return response.text
        except Exception as e:
            print(f"Gemini contextual description error: {e}")
            return None


# Singleton instance
vlm_service = VlmService()

"""
Gemini Vision service — image description and scene understanding.

Uses Gemini 2.5 Flash to describe images in Vietnamese.
Provides rich, contextual descriptions tailored for blind students.
"""

import logging

logger = logging.getLogger(__name__)

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

    def describe(self, image_bytes: bytes, mime_type: str) -> str | None:
        """
        Describe an image in Vietnamese.

        Args:
            image_bytes: Raw image data.
            mime_type: MIME type of the image (e.g., 'image/jpeg').

        Returns:
            Vietnamese description string, or None on failure.
        """
        try:
            response = self._model.generate_content(
                [
                    (
                        "Bạn là trợ lý cho học sinh khiếm thị Việt Nam. "
                        "Hãy mô tả chi tiết bức ảnh này bằng tiếng Việt một cách "
                        "tự nhiên, dễ hiểu. Nếu ảnh có văn bản, hãy đọc nội dung "
                        "văn bản đó. Nếu ảnh có biểu đồ, hãy mô tả số liệu và xu hướng."
                    ),
                    {"mime_type": mime_type, "data": image_bytes},
                ]
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini description error: {e}")
            return None

    def describe_with_context(self, image_bytes: bytes, mime_type: str, context: str) -> str | None:
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
            response = self._model.generate_content(
                [
                    (
                        f"Bạn là trợ lý cho học sinh khiếm thị Việt Nam. "
                        f"Học sinh đang học về: {context}. "
                        f"Hãy mô tả chi tiết bức ảnh này bằng tiếng Việt, "
                        f"liên hệ với nội dung đang học."
                    ),
                    {"mime_type": mime_type, "data": image_bytes},
                ]
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini contextual description error: {e}")
            return None

    def generate_answer(self, question: str, context_chunks: list[dict]) -> str | None:
        """
        Generate a Vietnamese answer from retrieved textbook chunks using Gemini.

        Args:
            question: The student's question in Vietnamese
            context_chunks: List of dicts with 'text', 'metadata'
                (grade, subject, chapter, page_number)

        Returns:
            Generated answer string, or fallback to top chunk text if Gemini fails
        """
        try:
            if not context_chunks:
                return "Không có đủ thông tin để trả lời câu hỏi này."

            # Build context from chunks
            context_parts = []
            for i, chunk in enumerate(context_chunks, 1):
                meta = chunk.get("metadata", {}) or {}
                grade = meta.get("grade", "?")
                subject = meta.get("subject", "?")
                chapter = meta.get("chapter", "?")
                page = meta.get("page_number", "?")
                source = f"[{grade}/{subject} - {chapter} trang {page}]"
                context_parts.append(f"{source}\n{chunk.get('text', '')}")

            context_text = "\n\n".join(context_parts)

            prompt = f"""Bạn là trợ lý học tập cho học sinh khiếm thị Việt Nam.
Hãy trả lời câu hỏi dựa trên các thông tin từ sách giáo khoa dưới đây.

Yêu cầu:
- Trả lời bằng tiếng Việt, ngắn gọn, dễ hiểu
- Nếu thông tin trong SGK không đủ để trả lời, hãy nói rõ
- Trích dẫn nguồn (lớp/môn/chương/trang) khi có thể
- Phù hợp với học sinh khiếm thị (mô tả bằng lời, không dùng ký hiệu trực quan)

THÔNG TIN SÁCH GIÁO KHOA:
{context_text}

CÂU HỎI: {question}

TRẢ LỜI:"""

            response = self._model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()

            # Fallback: return top chunk text
            if context_chunks:
                return context_chunks[0].get("text", "Không thể tạo câu trả lời.")
            return "Không thể tạo câu trả lời."

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            # Fallback to top chunk text
            if context_chunks:
                return context_chunks[0].get("text", "Không thể tạo câu trả lời.")
            return "Không thể tạo câu trả lời do lỗi hệ thống."


# Singleton instance
vlm_service = VlmService()

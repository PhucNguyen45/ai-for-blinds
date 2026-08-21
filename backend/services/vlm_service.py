"""
Vision-Language Model service — image description in Vietnamese.

Talks to any OpenAI-compatible endpoint (OpenRouter while developing, a local
vLLM / SGLang server once the model runs on-premise). Falls back to the Gemini
SDK only when no OpenRouter key is configured, so the old dev setup keeps
working during the migration.

The model is chosen with the VLM_MODEL environment variable; nothing in this
file is tied to one vendor.
"""

import base64
from typing import Optional

from backend.config import settings


class VlmService:
    """
    Vision-Language Model service.

    Generates detailed Vietnamese descriptions of images for blind students.
    """

    # Shared instruction block: every output is read aloud by TTS, so the
    # model must produce plain spoken Vietnamese — no markup, no visual deixis.
    SPEECH_RULES = (
        "Toàn bộ câu trả lời sẽ được đọc to bằng giọng nói tổng hợp. "
        "Vì vậy: không dùng markdown, không dùng dấu sao, dấu gạch đầu dòng, "
        "tiêu đề hay bất kỳ ký hiệu đặc biệt nào. "
        "Không dùng cụm chỉ thị thị giác như 'như bạn thấy', 'hình bên trái', "
        "'ở phía trên'. "
        "Đọc số liệu thành chữ, ví dụ 'hai mươi lăm phần trăm' thay vì '25%'. "
        "Viết câu ngắn, trình bày theo thứ tự tuyến tính, vì người nghe "
        "không tua lại được."
    )

    BASE_PROMPT = (
        "Bạn là trợ lý cho học sinh khiếm thị Việt Nam. "
        "Hãy mô tả chi tiết bức ảnh này bằng tiếng Việt một cách tự nhiên, "
        "dễ hiểu. Nếu ảnh có văn bản, hãy đọc nội dung văn bản đó. "
        "Nếu ảnh có biểu đồ, hãy mô tả số liệu và xu hướng. "
    )

    def __init__(self) -> None:
        self._client = None
        self._gemini = None

    # ── Client construction (lazy: importing this module needs no key) ──

    def _get_client(self):
        """Build the OpenAI-compatible client on first use."""
        if self._client is None:
            settings.validate()
            from openai import OpenAI

            self._client = OpenAI(
                api_key=settings.vlm_api_key,
                base_url=settings.vlm_base_url,
            )
        return self._client

    def _get_gemini(self):
        """Legacy path, used only when no OpenRouter key is set."""
        if self._gemini is None:
            settings.validate()
            import google.generativeai as genai

            genai.configure(api_key=settings.google_api_key)
            self._gemini = genai.GenerativeModel(settings.gemini_model)
        return self._gemini

    @property
    def model_name(self) -> str:
        """Model currently answering requests — surfaced by /health."""
        if settings.vlm_provider == "openai":
            return settings.vlm_model
        return settings.gemini_model

    # ── Internal helpers ────────────────────────────────────────────────

    @staticmethod
    def _data_url(image_bytes: bytes, mime_type: str) -> str:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        return f"data:{mime_type};base64,{b64}"

    def _chat(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        """One vision turn against the OpenAI-compatible endpoint."""
        response = self._get_client().chat.completions.create(
            model=settings.vlm_model,
            max_tokens=settings.vlm_max_tokens,
            temperature=settings.vlm_temperature,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": self._data_url(image_bytes, mime_type)
                            },
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content

    def _generate(
        self, prompt: str, image_bytes: bytes, mime_type: str
    ) -> Optional[str]:
        """Route to whichever provider is configured, reporting failures."""
        try:
            if settings.vlm_provider == "openai":
                return self._chat(prompt, image_bytes, mime_type)

            response = self._get_gemini().generate_content([
                prompt,
                {"mime_type": mime_type, "data": image_bytes},
            ])
            return response.text
        except Exception as e:
            print(f"VLM error ({self.model_name}): {e}")
            return None

    # ── Public API ──────────────────────────────────────────────────────

    def describe(self, image_bytes: bytes, mime_type: str) -> Optional[str]:
        """
        Describe an image in Vietnamese.

        Args:
            image_bytes: Raw image data.
            mime_type: MIME type of the image (e.g., 'image/jpeg').

        Returns:
            Vietnamese description string, or None on failure.
        """
        return self._generate(
            self.BASE_PROMPT + self.SPEECH_RULES, image_bytes, mime_type
        )

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
        prompt = (
            "Bạn là trợ lý cho học sinh khiếm thị Việt Nam. "
            f"Học sinh đang học về: {context}. "
            "Hãy mô tả chi tiết bức ảnh này bằng tiếng Việt, liên hệ với nội "
            "dung đang học. " + self.SPEECH_RULES
        )
        return self._generate(prompt, image_bytes, mime_type)

    def transcribe(self, image_bytes: bytes, mime_type: str) -> Optional[str]:
        """
        Đọc nguyên văn chữ trong ảnh, không mô tả, không bình luận.

        Ràng buộc 2 của đề tài: một VLM gánh cả OCR lẫn mô tả. Nhờ vậy
        `/ocr` không cần PaddleOCR và không phải cài thêm vài GB thư viện.
        """
        prompt = (
            "Đọc toàn bộ chữ có trong ảnh này và chép lại chính xác bằng "
            "tiếng Việt, giữ nguyên thứ tự từ trên xuống dưới. "
            "Chỉ chép chữ, không mô tả hình ảnh, không thêm nhận xét, "
            "không thêm lời dẫn. Nếu ảnh không có chữ nào, trả lời đúng một "
            "câu: Ảnh này không có chữ."
        )
        return self._generate(prompt, image_bytes, mime_type)

    def answer_from_context(self, question: str, passages: list[str]) -> Optional[str]:
        """
        Answer a student question grounded in retrieved textbook passages.

        Used by /rag/query so the endpoint returns spoken Vietnamese instead of
        a raw chunk of textbook.

        Args:
            question: The student's question.
            passages: Textbook passages retrieved from the vector store.

        Returns:
            Vietnamese answer, or None on failure.
        """
        joined = "\n\n".join(f"Đoạn {i + 1}: {p}" for i, p in enumerate(passages))
        prompt = (
            "Bạn là trợ lý học tập cho học sinh khiếm thị Việt Nam. "
            "Chỉ trả lời dựa trên các đoạn sách giáo khoa dưới đây. "
            "Nếu các đoạn này không đủ để trả lời, hãy nói rõ là chưa tìm thấy "
            "trong sách giáo khoa, đừng tự suy đoán.\n\n"
            f"{joined}\n\n"
            f"Câu hỏi của học sinh: {question}\n\n" + self.SPEECH_RULES
        )
        try:
            if settings.vlm_provider == "openai":
                response = self._get_client().chat.completions.create(
                    model=settings.vlm_model,
                    max_tokens=settings.vlm_max_tokens,
                    temperature=settings.vlm_temperature,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content

            return self._get_gemini().generate_content(prompt).text
        except Exception as e:
            print(f"VLM answer error ({self.model_name}): {e}")
            return None


# Singleton instance
vlm_service = VlmService()

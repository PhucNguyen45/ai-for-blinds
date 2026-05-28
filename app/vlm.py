import asyncio
import io
import logging
from typing import Optional

import google.generativeai as genai
from PIL import Image

from .config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.gemini_api_key)

_SUPPORTED_MIME = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}


class VLMError(Exception):
    """Lỗi khi gọi VLM."""


def _validate_image(image_bytes: bytes, mime_type: Optional[str]) -> str:
    """Kiểm tra ảnh hợp lệ, trả về mime type chuẩn."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
    except Exception as e:
        raise VLMError(f"Ảnh không hợp lệ: {e}") from e

    fmt = (img.format or "").lower()
    detected = {
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "heic": "image/heic",
        "heif": "image/heif",
    }.get(fmt)

    if detected:
        return detected
    if mime_type in _SUPPORTED_MIME:
        return mime_type
    raise VLMError(f"Định dạng ảnh không được hỗ trợ: {fmt or mime_type}")


async def ask_vlm(image_bytes: bytes, question: str, mime_type: Optional[str] = None) -> str:
    """Gửi ảnh + câu hỏi tới Gemini, trả về câu trả lời text."""
    if not question.strip():
        raise VLMError("Câu hỏi không được để trống")

    resolved_mime = _validate_image(image_bytes, mime_type)

    model = genai.GenerativeModel(settings.gemini_model)

    def _call() -> str:
        response = model.generate_content(
            [
                {"mime_type": resolved_mime, "data": image_bytes},
                question,
            ],
            request_options={"timeout": settings.request_timeout_s},
        )
        text = getattr(response, "text", None)
        if not text:
            blocked = getattr(response, "prompt_feedback", None)
            raise VLMError(f"VLM không trả về kết quả (có thể bị block: {blocked})")
        return text

    try:
        return await asyncio.to_thread(_call)
    except VLMError:
        raise
    except Exception as e:
        logger.exception("Lỗi gọi Gemini")
        raise VLMError(f"Lỗi gọi VLM: {e}") from e

import asyncio
import io
import json
import logging
import re
from typing import Optional, Tuple

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from PIL import Image

from .config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.gemini_api_key)

_SUPPORTED_IMAGE_MIME = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
_SUPPORTED_AUDIO_MIME = {
    "audio/wav", "audio/mp3", "audio/mpeg", "audio/mp4", "audio/m4a",
    "audio/aac", "audio/ogg", "audio/opus", "audio/flac", "audio/webm",
}

_VOICE_SYSTEM_PROMPT = (
    "Bạn là trợ lý hình ảnh cho người khiếm thị. "
    "File audio chứa câu hỏi bằng tiếng Việt của người dùng về bức ảnh đính kèm. "
    "Hãy: (1) chép lại chính xác câu hỏi từ audio, (2) trả lời câu hỏi đó dựa vào ảnh, ngắn gọn, "
    "rõ ràng, bằng tiếng Việt tự nhiên dễ nghe (1-3 câu, tránh ký hiệu/markdown). "
    "Trả về DUY NHẤT một JSON object có 2 khóa: \"question\" (chuỗi) và \"answer\" (chuỗi). "
    "Không thêm ```json hay giải thích nào khác."
)


class VLMError(Exception):
    """Lỗi khi gọi VLM."""


class VLMRateLimitError(VLMError):
    """Vượt quota Gemini (free tier 5 RPM với 2.5-flash)."""
    def __init__(self, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        msg = "Đã hết lượt gọi miễn phí. "
        if retry_after:
            msg += f"Vui lòng thử lại sau {retry_after} giây."
        else:
            msg += "Vui lòng thử lại sau ít phút."
        super().__init__(msg)


def _validate_image(image_bytes: bytes, mime_type: Optional[str]) -> str:
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
    if mime_type in _SUPPORTED_IMAGE_MIME:
        return mime_type
    raise VLMError(f"Định dạng ảnh không được hỗ trợ: {fmt or mime_type}")


def _validate_audio_mime(mime_type: Optional[str]) -> str:
    if not mime_type:
        raise VLMError("Thiếu mime_type cho audio")
    base = mime_type.split(";")[0].strip().lower()
    if base not in _SUPPORTED_AUDIO_MIME:
        raise VLMError(f"Định dạng audio không được hỗ trợ: {mime_type}")
    return base


def _parse_voice_response(raw: str) -> Tuple[str, str]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise VLMError(f"VLM không trả về JSON hợp lệ: {raw[:200]}")
        data = json.loads(match.group(0))

    question = (data.get("question") or "").strip()
    answer = (data.get("answer") or "").strip()
    if not answer:
        raise VLMError("VLM không trả về câu trả lời")
    return question, answer


async def ask_vlm(image_bytes: bytes, question: str, mime_type: Optional[str] = None) -> str:
    """Text question + image → text answer."""
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
    except google_exceptions.ResourceExhausted as e:
        retry = _extract_retry_seconds(e)
        logger.warning("Gemini rate limit (text): retry in %ss", retry)
        raise VLMRateLimitError(retry) from e
    except Exception as e:
        logger.exception("Lỗi gọi Gemini")
        raise VLMError(f"Lỗi gọi VLM: {e}") from e


def _extract_retry_seconds(exc: Exception) -> Optional[int]:
    msg = str(exc)
    m = re.search(r"retry in ([0-9]+(?:\.[0-9]+)?)s", msg, re.IGNORECASE)
    if m:
        return int(float(m.group(1))) + 1
    m = re.search(r"seconds:\s*([0-9]+)", msg)
    if m:
        return int(m.group(1)) + 1
    return None


async def ask_vlm_voice(
    image_bytes: bytes,
    audio_bytes: bytes,
    image_mime: Optional[str] = None,
    audio_mime: Optional[str] = None,
) -> Tuple[str, str]:
    """Audio question + image → (transcribed_question, answer). Gemini does STT+VLM in one call."""
    resolved_image_mime = _validate_image(image_bytes, image_mime)
    resolved_audio_mime = _validate_audio_mime(audio_mime)

    model = genai.GenerativeModel(
        settings.gemini_model,
        system_instruction=_VOICE_SYSTEM_PROMPT,
    )

    def _call() -> str:
        response = model.generate_content(
            [
                {"mime_type": resolved_image_mime, "data": image_bytes},
                {"mime_type": resolved_audio_mime, "data": audio_bytes},
            ],
            generation_config={"response_mime_type": "application/json"},
            request_options={"timeout": settings.request_timeout_s},
        )
        text = getattr(response, "text", None)
        if not text:
            blocked = getattr(response, "prompt_feedback", None)
            raise VLMError(f"VLM không trả về kết quả (có thể bị block: {blocked})")
        return text

    try:
        raw = await asyncio.to_thread(_call)
    except VLMError:
        raise
    except google_exceptions.ResourceExhausted as e:
        retry = _extract_retry_seconds(e)
        logger.warning("Gemini rate limit (voice): retry in %ss", retry)
        raise VLMRateLimitError(retry) from e
    except Exception as e:
        logger.exception("Lỗi gọi Gemini (voice)")
        raise VLMError(f"Lỗi gọi VLM: {e}") from e

    return _parse_voice_response(raw)

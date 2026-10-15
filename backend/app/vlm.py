"""Lớp mô hình: mock hoặc API tương thích OpenAI (OpenRouter / vLLM on-premise)."""
import asyncio
import json
import re
from typing import Dict, List, Optional, Tuple

import httpx

from .config import settings
from .schemas import RESOLVED_PAGE_TYPES


class VLMError(Exception):
    pass


class VLMTimeout(VLMError):
    pass


# ---------------------------------------------------------------- mock

_MOCK_DESCRIPTIONS = {
    "text": "Đây là dữ liệu thử, chưa phải mô hình thật. Trang có một đoạn chữ gồm ba câu nói về quê hương em. Câu đầu là: Quê em có cánh đồng lúa rộng. Bạn có muốn nghe đọc hết đoạn không?",
    "map": "Đây là dữ liệu thử, chưa phải mô hình thật. Trang có một lược đồ một vùng của Việt Nam. Phía trên lược đồ là hướng Bắc. Có một con sông chảy từ phía Tây Bắc xuống phía Đông Nam, đổ ra biển ở phía Đông. Bạn có muốn nghe tên các tỉnh trên lược đồ không?",
    "chart": "Đây là dữ liệu thử, chưa phải mô hình thật. Trang có một biểu đồ cột về số dân qua ba năm. Cột tăng dần từ năm đầu đến năm cuối. Bạn có muốn nghe số liệu từng năm không?",
    "table": "Đây là dữ liệu thử, chưa phải mô hình thật. Trang có một bảng hai cột, ba hàng. Cột thứ nhất là tên vùng, cột thứ hai là diện tích. Bạn có muốn nghe từng hàng không?",
    "figure": "Đây là dữ liệu thử, chưa phải mô hình thật. Trang có một bức ảnh ruộng bậc thang trên sườn đồi. Các thửa ruộng xếp thành từng bậc như cầu thang, từ chân đồi lên tới đỉnh. Bạn có muốn nghe thêm chi tiết không?",
    "mixed": "Đây là dữ liệu thử, chưa phải mô hình thật. Trang có một đoạn chữ và hai hình. Đoạn chữ nói về vùng đồng bằng. Hình một là lược đồ vùng đồng bằng. Hình hai là ảnh một cánh đồng lúa. Bạn muốn nghe phần chữ hay phần hình trước?",
}


class MockVLM:
    async def describe(self, messages: List[Dict], page_type: str) -> str:
        await asyncio.sleep(settings.mock_delay)
        resolved = "mixed" if page_type == "auto" else page_type
        return json.dumps(
            {"page_type": resolved, "unreadable": False, "description": _MOCK_DESCRIPTIONS[resolved]},
            ensure_ascii=False,
        )

    async def ask(self, messages: List[Dict]) -> str:
        await asyncio.sleep(settings.mock_delay)
        question = messages[-1]["content"]
        return f"Đây là câu trả lời thử cho câu hỏi: {question}. Khi nối mô hình thật, câu trả lời sẽ dựa trên ảnh."


# ---------------------------------------------------------------- OpenAI-compatible


class OpenAICompatVLM:
    """Gọi POST {VLM_BASE_URL}/chat/completions. Khởi tạo client lười, timeout, thử lại."""

    def __init__(self, transport: Optional[httpx.AsyncBaseTransport] = None) -> None:
        self._transport = transport
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if settings.vlm_api_key:
                headers["Authorization"] = f"Bearer {settings.vlm_api_key}"
            if "openrouter.ai" in settings.vlm_base_url:
                headers["X-Title"] = "SgBe NCKH"
            self._client = httpx.AsyncClient(
                base_url=settings.vlm_base_url,
                headers=headers,
                timeout=settings.vlm_timeout,
                transport=self._transport,
            )
        return self._client

    async def _chat(self, messages: List[Dict]) -> str:
        payload = {
            "model": settings.vlm_model,
            "messages": messages,
            "max_tokens": settings.vlm_max_tokens,
            "temperature": settings.vlm_temperature,
        }
        last_error: Exception = VLMError("Không gọi được mô hình")
        for attempt in range(settings.vlm_max_retries + 1):
            try:
                resp = await self._get_client().post("/chat/completions", json=payload)
            except httpx.TimeoutException as exc:
                last_error = VLMTimeout(str(exc))
                continue
            except httpx.HTTPError as exc:
                last_error = VLMError(f"Lỗi kết nối: {exc}")
                continue
            if resp.status_code == 429 or resp.status_code >= 500:
                last_error = VLMError(f"Mô hình trả lỗi {resp.status_code}: {resp.text[:200]}")
                if attempt < settings.vlm_max_retries:
                    await asyncio.sleep(1.5)
                continue
            if resp.status_code >= 400:
                raise VLMError(f"Mô hình trả lỗi {resp.status_code}: {resp.text[:300]}")
            try:
                content = resp.json()["choices"][0]["message"]["content"]
            except (KeyError, IndexError, ValueError) as exc:
                raise VLMError(f"Phản hồi không đúng định dạng: {exc}")
            if isinstance(content, list):  # một số máy chủ trả danh sách phần
                content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
            return content or ""
        raise last_error

    async def describe(self, messages: List[Dict], page_type: str) -> str:
        return await self._chat(messages)

    async def ask(self, messages: List[Dict]) -> str:
        return await self._chat(messages)


# ---------------------------------------------------------------- tiện ích

_vlm = None


def get_vlm():
    global _vlm
    if _vlm is None:
        _vlm = MockVLM() if settings.vlm_mode == "mock" else OpenAICompatVLM()
    return _vlm


def reset_vlm(instance=None) -> None:
    """Dùng trong test hoặc khi đổi cấu hình lúc chạy."""
    global _vlm
    _vlm = instance


_JSON_BLOCK = re.compile(r"\{.*\}", re.S)


def parse_describe_output(text: str, requested_type: str) -> Tuple[str, str, bool]:
    """Trả (description, page_type, unreadable). Chịu được JSON bọc trong ``` hoặc văn bản thường."""
    page_type = requested_type if requested_type != "auto" else "mixed"
    cleaned = re.sub(r"```(?:json)?", "", text or "").strip()
    match = _JSON_BLOCK.search(cleaned)
    if match:
        try:
            obj = json.loads(match.group(0))
            desc = str(obj.get("description", "")).strip()
            if requested_type == "auto" and obj.get("page_type") in RESOLVED_PAGE_TYPES:
                page_type = obj["page_type"]
            unreadable = bool(obj.get("unreadable", False))
            if desc:
                return desc, page_type, unreadable
        except (ValueError, AttributeError):
            pass
    # Mô hình không trả JSON: dùng nguyên văn bản
    return cleaned, page_type, False

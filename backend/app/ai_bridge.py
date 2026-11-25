"""Nối backend (API v1, Nam) với module AI của Phúc (ai/pipeline.py, hợp đồng v0.1). Bật bằng VLM_MODE=ai.

Module AI không ném ngoại lệ: lỗi vận hành trả `status="error"` kèm `error.code`. Ở đây đổi các mã đó
sang mã lỗi API v1 và câu tiếng Việt cố định, để app đọc thẳng như mọi lỗi khác của backend.

Kết quả /v1/describe giữ đủ trường API v1 (description, page_type, unreadable, ...) để app cũ vẫn chạy,
và thêm các trường của hợp đồng v0.1 (status, summary_vi, interpretation_vi, image_type, uncertainties,
question_answering_ready) để app phân biệt "ảnh hỏng, chụp lại" với "mô tả bị cắt ngắn".
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

from .config import settings

# image_type (hợp đồng v0.1) -> page_type (API v1)
TYPE_TO_PAGE = {
    "bar_chart": "chart",
    "line_chart": "chart",
    "pie_chart": "chart",
    "table": "table",
    "flow_diagram": "figure",
    "cycle_diagram": "figure",
    "geometry": "figure",
    "map": "map",
    "text": "text",
}

# error.code (hợp đồng v0.1) -> (HTTP, mã API v1, câu đọc cho người dùng)
_ERRORS = {
    "timeout": (504, "VLM_TIMEOUT", "Máy chủ xử lý quá lâu. Bạn thử chụp lại nhé."),
    "invalid_image": (400, "INVALID_IMAGE", "Ảnh gửi lên không đọc được. Bạn chụp lại nhé."),
    "invalid_input": (422, "INVALID_REQUEST", "Câu hỏi chưa hợp lệ. Bạn hỏi lại nhé."),
    "config_error": (503, "AI_NOT_CONFIGURED", "Máy chủ chưa cấu hình mô hình. Bạn báo người hỗ trợ kiểm tra nhé."),
}
_DEFAULT_ERROR = (502, "VLM_ERROR", "Chưa kết nối được mô hình. Bạn thử lại sau ít phút nhé.")


class AiFailure(Exception):
    def __init__(self, status: int, code: str, message: str, detail: str = "") -> None:
        super().__init__(detail or code)
        self.status, self.code, self.message, self.detail = status, code, message, detail


def _pipeline():
    """Nạp ai/pipeline.py (các module của Phúc import theo gốc ai/, nên thêm ai/ vào sys.path)."""
    ai_dir = str(settings.ai_dir)
    if ai_dir not in sys.path:
        sys.path.insert(0, ai_dir)
    import pipeline  # noqa: PLC0415  (nạp lười: chế độ mock/openai không cần module AI)

    return pipeline


def _failure(error: Any) -> AiFailure:
    code = getattr(error, "code", None) or "unknown"
    status, api_code, message = _ERRORS.get(code, _DEFAULT_ERROR)
    return AiFailure(status, api_code, message, detail=f"{code}: {getattr(error, 'message', '')}"[:300])


def describe(image_path: Path, image_id: str, page_type: str) -> Dict[str, Any]:
    """Gọi describe_page() rồi trả các trường cho DescribeResult (trừ image_id, latency_ms, cached)."""
    res = _pipeline().describe_page(image_path, image_id=image_id)
    if res.status == "error":
        raise _failure(res.error)
    meta = res.meta
    return {
        "description": (res.interpretation_vi or res.summary_vi or "").strip(),
        "page_type": TYPE_TO_PAGE.get(res.image_type) or ("mixed" if page_type == "auto" else page_type),
        # partial = lời diễn giải bị cắt do giới hạn độ dài, KHÔNG phải ảnh hỏng
        "unreadable": res.status in ("unreadable", "unsupported"),
        "model": meta.model if meta else settings.model_name,
        # ảnh bị cổng chất lượng chặn thì chưa gọi VLM, không có meta
        "prompt_version": meta.prompt_id if meta else "capture_gate",
        "status": res.status,
        "summary_vi": res.summary_vi,
        "interpretation_vi": res.interpretation_vi,
        "image_type": res.image_type,
        "uncertainties": list(res.uncertainties),
        "question_answering_ready": res.question_answering_ready,
    }


def ask(image_path: Path, image_id: str, question: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    """Gọi ask_page(). Không truyền lời mô tả: đo trên dev của Phúc cho thấy truyền vào làm câu hỏi vị trí tệ hơn."""
    turns = [(t["question"], t["answer"]) for t in history]
    res = _pipeline().ask_page(image_path, question, history=turns, image_id=image_id)
    if res.status == "error":
        raise _failure(res.error)
    meta = res.meta
    return {
        "answer": res.answer_vi.strip(),
        "model": meta.model if meta else settings.model_name,
        "prompt_version": meta.prompt_id if meta else "",
    }

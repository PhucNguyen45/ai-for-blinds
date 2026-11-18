"""Đường ống mức hệ thống của module AI: cổng chất lượng ảnh -> mô tả (VLM) -> hỏi đáp.

Backend chỉ cần gọi hai hàm ở đây. Ảnh hỏng vật lý (quá tối, quá mờ) bị chặn trước khi tốn lượt VLM và nhận ngay lời
hướng dẫn chụp lại; lỗi phụ thuộc nội dung (chói che một phần, hình bị cắt) do prompt `b0g_v1` của VLM xử lý.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from capture.quality import CaptureReport, Thresholds, check_image
from contract.models import AnswerResult, DescriptionResult
from vlm.ask import ask_about_image
from vlm.common import SUPPORTED_SUFFIXES, error_result
from vlm.describer import describe_image

DEFAULT_PROMPT = "b0g_v1"


def describe_page(image_path: str | Path, *, gate: bool = True, thresholds: Thresholds = Thresholds(),
                  prompt_id: str = DEFAULT_PROMPT, image_id: str | None = None, **kwargs) -> DescriptionResult:
    """Mô tả trang đã chụp. `kwargs` chuyển nguyên cho `describe_image` (model, provider, timeout, ...)."""
    path = Path(image_path).expanduser()
    if gate and path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
        try:
            report: CaptureReport = check_image(path, thresholds)
        except OSError:
            return error_result("invalid_image", "Không đọc được tệp ảnh.", False, image_id=image_id)
        if not report.ok:
            return DescriptionResult(
                image_id=image_id, image_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                status="unreadable", summary_vi=report.guidance_vi,
                uncertainties=[f"capture_gate:{issue}" for issue in report.issues])
    return describe_image(path, prompt_id=prompt_id, image_id=image_id, **kwargs)


def ask_page(image_path: str | Path, question: str, **kwargs) -> AnswerResult:
    """Hỏi đáp theo hình (xem `vlm.ask.ask_about_image` về tham số `description`, `history`)."""
    return ask_about_image(image_path, question, **kwargs)

"""Hợp đồng đầu ra của module AI (BẢN NHÁP v0.1 — chưa thống nhất với Nam/Toàn).

Đây là đề xuất của Mảng A, dựa trên schema nội bộ v0.1 trong báo cáo 23/10/2026
và các điểm tích hợp còn mở (image_id, timeout, lỗi). Mọi thay đổi làm đổi nghĩa
trường cần tăng `schema_version` và thông báo cho Mảng B/C.

Lưu ý: `facts[].evidence` do VLM tự sinh, KHÔNG chứng minh dữ kiện đúng.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CONTRACT_VERSION = "0.1"

Status = Literal["ok", "partial", "unreadable", "unsupported", "error"]

ImageType = Literal[
    "bar_chart", "line_chart", "pie_chart", "table",
    "flow_diagram", "cycle_diagram", "geometry", "map",
    "text", "other", "unknown",
]

ErrorCode = Literal[
    "invalid_image", "config_error", "timeout", "http_error",
    "empty_response", "invalid_output", "invalid_input", "unknown",
]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Fact(_Strict):
    """Một dữ kiện có cấu trúc rút ra từ ảnh."""

    subject: str
    predicate: str
    object: str
    evidence: str | None = Field(
        default=None,
        description="Bằng chứng do mô hình tự nêu; không phải bằng chứng đã xác minh.",
    )


class Usage(_Strict):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class Meta(_Strict):
    """Thông tin tái lập: mô hình, prompt, tham số, hiệu năng."""

    model: str
    provider: str | None = None
    method: Literal["B0", "B1"] = "B0"
    prompt_id: str
    prompt_sha256: str
    temperature: float
    max_tokens: int
    finish_reason: str | None = None
    latency_seconds: float | None = None
    usage: Usage | None = None
    created_at_utc: datetime


class ErrorInfo(_Strict):
    """Lỗi vận hành. `message` không được chứa khóa API hoặc đường dẫn nội bộ."""

    code: ErrorCode
    message: str
    retryable: bool
    http_status: int | None = None


class DescriptionResult(_Strict):
    schema_version: Literal["0.1"] = CONTRACT_VERSION
    image_id: str | None = Field(
        default=None, description="Do bên gọi (backend) cấp; module AI chỉ trả lại."
    )
    image_sha256: str | None = None
    image_type: ImageType = "unknown"
    status: Status
    summary_vi: str = Field(
        default="", description="Tóm tắt tiếng Việt để phát trước (có thể rỗng khi lỗi)."
    )
    facts: list[Fact] = Field(default_factory=list)
    interpretation_vi: str = Field(
        default="", description="Lời diễn giải đầy đủ, dùng được cho TTS (không Markdown/JSON)."
    )
    uncertainties: list[str] = Field(default_factory=list)
    question_answering_ready: bool = Field(
        default=False,
        description="True nếu đủ căn cứ để hỏi đáp tiếp theo; chỉ có nghĩa khi status ok/partial.",
    )
    meta: Meta | None = None
    error: ErrorInfo | None = None

    @model_validator(mode="after")
    def _check_consistency(self) -> "DescriptionResult":
        if self.status == "error":
            if self.error is None:
                raise ValueError("status='error' cần trường error")
            if self.interpretation_vi:
                raise ValueError("status='error' không được có interpretation_vi")
        elif self.error is not None:
            raise ValueError("chỉ status='error' mới có trường error")

        if self.status in ("ok", "partial") and not self.interpretation_vi.strip():
            raise ValueError(f"status='{self.status}' cần interpretation_vi")

        if self.status in ("unreadable", "unsupported") and not self.summary_vi.strip():
            raise ValueError(f"status='{self.status}' cần summary_vi giải thích lý do")

        if self.question_answering_ready and self.status not in ("ok", "partial"):
            raise ValueError("question_answering_ready chỉ đúng khi status ok/partial")
        return self


AnswerStatus = Literal["ok", "partial", "error"]


class AnswerResult(_Strict):
    """Kết quả một lượt hỏi đáp theo hình (bản nháp, cùng phiên bản hợp đồng với DescriptionResult)."""

    schema_version: Literal["0.1"] = CONTRACT_VERSION
    image_id: str | None = None
    status: AnswerStatus
    answer_vi: str = Field(default="", description="Câu trả lời tiếng Việt, dùng được cho TTS (không Markdown).")
    meta: Meta | None = None
    error: ErrorInfo | None = None

    @model_validator(mode="after")
    def _check_consistency(self) -> "AnswerResult":
        if self.status == "error":
            if self.error is None or self.answer_vi:
                raise ValueError("status='error' cần error và không có answer_vi")
        else:
            if self.error is not None:
                raise ValueError("chỉ status='error' mới có trường error")
            if not self.answer_vi.strip():
                raise ValueError(f"status='{self.status}' cần answer_vi")
        return self

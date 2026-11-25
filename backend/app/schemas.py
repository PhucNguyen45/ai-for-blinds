"""Hợp đồng API v1. Mọi phản hồi bọc trong {"data": ..., "error": ...}."""
from typing import Generic, List, Literal, Optional, TypeVar

from pydantic import BaseModel, Field

# auto: để mô hình tự nhận loại trang. mixed: trang vừa có chữ vừa có hình.
PageType = Literal["auto", "text", "map", "chart", "table", "figure", "mixed"]
RESOLVED_PAGE_TYPES = ("text", "map", "chart", "table", "figure", "mixed")

T = TypeVar("T")


class ErrorInfo(BaseModel):
    code: str = Field(description="Mã lỗi máy đọc, ví dụ INVALID_IMAGE")
    message: str = Field(description="Câu tiếng Việt để app đọc thẳng cho người dùng")


class Envelope(BaseModel, Generic[T]):
    data: Optional[T] = None
    error: Optional[ErrorInfo] = None


class DescribeResult(BaseModel):
    image_id: str = Field(description="Dùng lại ở /v1/ask")
    description: str = Field(description="Văn nói thuần, không markdown, đọc thẳng bằng TTS")
    page_type: str = Field(description="text | map | chart | table | figure | mixed")
    unreadable: bool = Field(description="Có chỗ mô hình không đọc được")
    model: str
    prompt_version: str
    latency_ms: int
    cached: bool = Field(description="Kết quả lấy từ bộ nhớ đệm, không gọi lại mô hình")


class Turn(BaseModel):
    question: str
    answer: str


class AskRequest(BaseModel):
    image_id: str = Field(pattern=r"^[0-9a-f]{16}$")
    question: str = Field(min_length=1, max_length=500)
    history: List[Turn] = Field(default_factory=list, description="Các lượt hỏi đáp trước, cũ nhất trước")


class AskResult(BaseModel):
    image_id: str
    answer: str
    model: str
    prompt_version: str
    latency_ms: int


class SttResult(BaseModel):
    text: str
    latency_ms: int


class BookSummary(BaseModel):
    book: str
    title: str
    page_count: int


class PageRecord(BaseModel):
    book: str
    page: int
    page_type: str
    description: str
    image_sha256: str
    model: str
    prompt_version: str
    reviewed: bool = Field(description="Đã có người kiểm tra nội dung hay chưa")


class BookPages(BaseModel):
    book: str
    title: str
    pages: List[PageRecord]

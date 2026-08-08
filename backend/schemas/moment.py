"""
Moment schemas — request/response validation for the Persistent Visual Memory API.

Provides contracts for creating, listing, deleting, and semantically searching
LearningMoments stored in PostgreSQL + pgvector.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class MomentCreate(BaseModel):
    """Request schema for creating a learning moment."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Tiêu đề ngắn của khoảnh khắc học tập",
        examples=["Công thức tính diện tích hình tròn"],
    )
    content: str = Field(
        "",
        max_length=10000,
        description="Nội dung chi tiết (mô tả AI hoặc văn bản quét được)",
    )
    content_type: str = Field(
        "text",
        description="Loại nội dung: text | description | ocr | image_description",
    )
    grade: int | None = Field(None, ge=1, le=12, description="Lớp học (1-12)")
    subject: str | None = Field(None, description="Môn học (ví dụ: Toán, Văn, Sinh)")
    chapter: str | None = Field(None, max_length=128, description="Chương")
    page_number: int | None = Field(None, ge=1, description="Số trang")


class MomentResponse(BaseModel):
    """Response schema for a learning moment."""

    id: str = Field(..., description="ID của khoảnh khắc")
    title: str = Field(..., description="Tiêu đề")
    content: str = Field(..., description="Nội dung")
    content_type: str = Field(..., description="Loại nội dung")
    file_path: str | None = Field(None, description="Đường dẫn file ảnh/audio")
    file_type: str | None = Field(None, description="Loại file (jpg, png, m4a...)")
    grade: int | None = Field(None, description="Lớp học")
    subject: str | None = Field(None, description="Môn học")
    chapter: str | None = Field(None, description="Chương")
    page_number: int | None = Field(None, description="Số trang")
    created_at: datetime = Field(..., description="Thời điểm tạo")


class MomentSearchRequest(BaseModel):
    """Request schema for semantic search over learning moments."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Câu hỏi hoặc từ khóa tìm kiếm",
        examples=["Định lý Pytago"],
    )
    n_results: int = Field(
        5,
        ge=1,
        le=20,
        description="Số lượng kết quả cần trả về",
    )


class MomentSearchResult(BaseModel):
    """A single moment returned by semantic search, with relevance distance."""

    id: str = Field(..., description="ID của khoảnh khắc")
    title: str = Field(..., description="Tiêu đề")
    content: str = Field(..., description="Nội dung")
    content_type: str = Field(..., description="Loại nội dung")
    created_at: datetime = Field(..., description="Thời điểm tạo")
    distance: float = Field(..., description="Khoảng cách cosine similarity (thấp = gần)")


class MomentSearchResponse(BaseModel):
    """Response schema for semantic search."""

    query: str = Field(..., description="Câu hỏi gốc")
    results: list[MomentSearchResult] = Field(
        default_factory=list,
        description="Danh sách kết quả sắp theo độ liên quan",
    )

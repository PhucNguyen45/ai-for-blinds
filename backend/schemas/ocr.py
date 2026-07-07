"""
OCR schemas — request/response validation for POST /ocr.

Ensures consistent data contracts between frontend and backend.
"""

from pydantic import BaseModel, Field


class OcrResponse(BaseModel):
    """Response schema for OCR endpoint."""

    text: str = Field(
        ...,
        description="Văn bản đã trích xuất từ ảnh",
        examples=["Đây là nội dung văn bản được nhận dạng từ ảnh."],
    )


class OcrError(BaseModel):
    """Error response schema for OCR endpoint."""

    success: bool = Field(False, description="Luôn là false khi lỗi")
    message: str = Field(..., description="Thông báo lỗi bằng tiếng Việt")
    detail: str | None = Field(None, description="Chi tiết lỗi kỹ thuật")

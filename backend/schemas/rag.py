"""
RAG schemas — request/response validation for POST /rag/query.

Ensures consistent contracts for textbook Q&A between frontend and backend.
Response includes answer text and source citation for trustworthiness.
"""

from pydantic import BaseModel, Field


class RagQueryRequest(BaseModel):
    """Request schema for RAG query endpoint."""
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Câu hỏi của học sinh về nội dung SGK",
        examples=["Nguyên phân là gì?", "Giải thích định luật bảo toàn năng lượng"],
    )
    n_results: int = Field(
        5,
        ge=1,
        le=20,
        description="Số lượng đoạn văn bản cần truy xuất",
    )
    grade: int | None = Field(
        None,
        ge=1,
        le=12,
        description="Lọc theo lớp (1-12)",
    )
    subject: str | None = Field(
        None,
        description="Lọc theo môn học (ví dụ: Toán, Văn, Sinh)",
    )


class SourceCitation(BaseModel):
    """Citation from a specific textbook chunk."""
    chunk_id: str = Field(..., description="ID của đoạn văn bản trong ChromaDB")
    text: str = Field(..., description="Nội dung đoạn văn bản trích dẫn")
    grade: int | None = Field(None, description="Lớp")
    subject: str | None = Field(None, description="Môn học")
    chapter: str | None = Field(None, description="Chương")
    page_number: int | None = Field(None, description="Số trang")
    distance: float = Field(..., description="Khoảng cách cosine similarity")


class RagQueryResponse(BaseModel):
    """Response schema for RAG query endpoint."""
    answer: str = Field(
        ...,
        description="Câu trả lời dựa trên nội dung SGK",
        examples=["Nguyên phân là quá trình phân chia tế bào..."],
    )
    source: SourceCitation | None = Field(
        None,
        description="Trích dẫn nguồn từ SGK đáng tin cậy nhất",
    )
    sources: list[SourceCitation] = Field(
        default_factory=list,
        description="Danh sách các nguồn tham khảo",
    )

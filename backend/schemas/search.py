"""
Search schemas — request/response validation for POST /search.

Contracts for internet retrieval (IR) between frontend and backend.
"""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request schema for the IR search endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Câu truy vấn tìm kiếm bằng tiếng Việt",
        examples=["Thủ đô của Việt Nam là gì?", "bài thơ Tây Tiến"],
    )
    n_results: int = Field(
        5,
        ge=1,
        le=20,
        description="Số lượng kết quả cần trả về",
    )


class SearchResult(BaseModel):
    """A single search result (web or news)."""

    title: str = Field("", description="Tiêu đề kết quả")
    snippet: str = Field("", description="Đoạn trích nội dung")
    url: str = Field("", description="Liên kết nguồn")
    source: str = Field("web", description="Nguồn: 'web' hoặc 'news'")
    score: float = Field(0.0, description="Điểm liên quan (0-1)")


class SearchResponse(BaseModel):
    """Response schema for the IR search endpoint."""

    query: str = Field(..., description="Câu truy vấn gốc")
    results: list[SearchResult] = Field(
        default_factory=list,
        description="Danh sách kết quả tìm kiếm",
    )

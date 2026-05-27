"""
TextbookContent model — stores SGK (textbook) content for RAG.

Each row represents a chunk of textbook content with:
- The raw text (extracted via OCR from PDF/scanned pages)
- A vector embedding (for semantic search with pgvector)
- Metadata about the source (grade, subject, chapter, page)
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class TextbookContent(Base):
    __tablename__ = "textbook_contents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Source metadata
    grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    subject: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    chapter: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    chapter_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Content
    title: Mapped[str] = mapped_column(String(256), default="Untitled")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # SHA-256 for dedup

    # Vector embedding (pgvector) — text representation for portability
    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    learning_moments = relationship("LearningMoment", back_populates="textbook")

    __table_args__ = (
        Index("idx_textbook_grade_subject", "grade", "subject"),
        Index("idx_textbook_content_hash", "content_hash"),
    )

    def __repr__(self) -> str:
        return f"<TextbookContent(id={self.id}, title={self.title})>"

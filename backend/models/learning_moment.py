"""
LearningMoment model — a "learning moment" captured and stored for later recall.

This is the core of the Persistent Visual Memory feature.
Each moment stores:
- The original image/file that was captured
- The AI-generated description or extracted text
- A vector embedding (for similarity search via pgvector)
- The page/chapter context if from a textbook
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class LearningMoment(Base):
    __tablename__ = "learning_moments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )

    # Content
    title: Mapped[str] = mapped_column(String(256), default="Learning Moment")
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_type: Mapped[str] = mapped_column(
        String(32), default="text"
    )  # text | description | ocr | image_description

    # File reference (original image/audio)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_type: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    # Context from textbook (for RAG integration)
    textbook_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("textbook_contents.id"), nullable=True
    )
    page_number: Mapped[Optional[int]] = mapped_column(nullable=True)
    chapter: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Vector embedding (pgvector) — stored as text for portability
    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User", back_populates="learning_moments")
    textbook = relationship("TextbookContent", back_populates="learning_moments")

    __table_args__ = (
        Index("idx_learning_moments_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<LearningMoment(id={self.id}, title={self.title})>"

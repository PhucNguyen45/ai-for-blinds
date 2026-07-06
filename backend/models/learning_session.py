"""
LearningSession model — records a single study session.

Each session has a type (scan, read, voice_note, qa, describe)
and tracks duration, items processed, and outcome.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if TYPE_CHECKING:
    from .feedback import Feedback


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )

    # Session type: scan | read | voice_note | qa | describe | sonify
    session_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    items_processed: Mapped[int] = mapped_column(Integer, default=0)

    # Optional notes about the session outcome
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="learning_sessions")
    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="session")

    def __repr__(self) -> str:
        return f"<LearningSession(id={self.id}, type={self.session_type})>"

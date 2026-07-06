"""Feedback model for user ratings and comments on learning moments and sessions."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models import Base

if TYPE_CHECKING:
    from backend.models.learning_moment import LearningMoment
    from backend.models.learning_session import LearningSession


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid4().hex)
    learning_moment_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("learning_moments.id", ondelete="SET NULL"), nullable=True
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("learning_sessions.id", ondelete="SET NULL"), nullable=True
    )
    rating: Mapped[int] = mapped_column(default=5)  # 1-5
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationships
    learning_moment: Mapped[Optional["LearningMoment"]] = relationship(back_populates="feedbacks")
    session: Mapped[Optional["LearningSession"]] = relationship(back_populates="feedbacks")

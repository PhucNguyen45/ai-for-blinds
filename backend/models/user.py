"""
User model — represents a student using SgBe Vision.

Tracks profile info, preferences for accessibility (TTS speed/pitch/volume),
and device identifiers for push notifications.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    display_name: Mapped[str] = mapped_column(String(128), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(256), unique=True, nullable=True)

    # Accessibility preferences
    tts_speed: Mapped[float] = mapped_column(Float, default=0.5)
    tts_pitch: Mapped[float] = mapped_column(Float, default=1.0)
    tts_volume: Mapped[float] = mapped_column(Float, default=1.0)
    prefers_dark_mode: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    learning_sessions = relationship("LearningSession", back_populates="user")
    learning_moments = relationship("LearningMoment", back_populates="user")
    voice_notes = relationship("VoiceNote", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.display_name})>"

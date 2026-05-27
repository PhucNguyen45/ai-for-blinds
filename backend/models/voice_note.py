"""
VoiceNote model — persisted voice recording metadata.

Mirrors the frontend VoiceNote model for server-side persistence.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class VoiceNote(Base):
    __tablename__ = "voice_notes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )

    # Content
    title: Mapped[str] = mapped_column(String(256), default="Voice Note")
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Transcription (via Whisper STT)
    transcription: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_transcribed: Mapped[bool] = mapped_column(default=False)

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
    user = relationship("User", back_populates="voice_notes")

    def __repr__(self) -> str:
        return f"<VoiceNote(id={self.id}, title={self.title})>"

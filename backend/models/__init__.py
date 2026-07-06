"""
SgBe Vision — SQLAlchemy Database Models.

All models use declarative base with common TimestampMixin.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from .user import User
from .learning_session import LearningSession
from .learning_moment import LearningMoment
from .voice_note import VoiceNote
from .textbook_content import TextbookContent
from .feedback import Feedback
__all__ = [
    "Base",
    "User",
    "LearningSession",
    "LearningMoment",
    "VoiceNote",
    "TextbookContent",
    "Feedback",
]

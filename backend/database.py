"""
Database connection and session management.

Uses SQLAlchemy 2.0 with PostgreSQL and pgvector extension.
Supports both sync and async sessions.
"""

from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config import settings

# Synchronous engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency: get a database session (sync)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Call on startup."""
    from backend.models import Base

    Base.metadata.create_all(bind=engine)
    print("Database tables created / verified.")

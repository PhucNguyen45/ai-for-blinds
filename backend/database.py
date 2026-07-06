"""
Database connection and session management.

Uses SQLAlchemy 2.0 async with asyncpg for PostgreSQL.
"""

import logging

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


logger = logging.getLogger(__name__)

from backend.config import settings

# Convert sync URL to async URL
_database_url = settings.database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

# Async engine
engine = create_async_engine(
    _database_url,
    echo=settings.debug,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# Async session factory
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """Dependency: get a database session (async)."""
    async with SessionLocal() as session:
        yield session


async def init_db():
    """Create all tables. Call on startup."""
    from backend.models import Base

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created / verified.")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")

"""
Common FastAPI dependencies used across all route handlers.

Includes:
- Database session management (get_db)
- Shared dependency injection patterns
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from backend.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency: get a database session.

    Usage:
        @router.post("/endpoint")
        async def handler(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

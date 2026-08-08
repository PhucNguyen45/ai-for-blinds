"""
Moment service — Persistent Visual Memory (CRUD + semantic search).

Stores LearningMoments in PostgreSQL with vector embeddings (serialized as
JSON text for portability, matching the migration). Semantic search computes
cosine similarity in Python, so it works without the pgvector extension.

Graceful degradation: when the database or embedding model is unavailable,
the service reports `available = False` and routes return 503.
"""

import json
import logging
import uuid

logger = logging.getLogger(__name__)

from backend.config import settings
from backend.database import get_db


class MomentService:
    """Persistent Visual Memory service backed by PostgreSQL."""

    def __init__(self) -> None:
        self._embedder = None

    # ── Availability ────────────────────────────────────────────

    @property
    def available(self) -> bool:
        """Whether the database is reachable. Tries a no-op query."""
        try:
            import asyncio

            async def _probe():
                async for _ in get_db():
                    return True
                return True

            return asyncio.get_event_loop().run_until_complete(_probe())
        except Exception as e:
            logger.warning(f"Moment service DB probe failed: {e}")
            return False

    # ── Embedding ───────────────────────────────────────────────

    def _get_embedder(self):
        """Lazy-load the sentence embedding model."""
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer

            self._embedder = SentenceTransformer(settings.embedding_model)
        return self._embedder

    def embed(self, text: str) -> list[float] | None:
        """Embed text into a vector. Returns None if the model is unavailable."""
        try:
            model = self._get_embedder()
            vector = model.encode(text).tolist()
            return [float(v) for v in vector]
        except Exception as e:
            logger.error(f"Moment embedding error: {e}")
            return None

    # ── User resolution (device-based) ──────────────────────────

    async def _get_or_create_user(self, session, device_id: str):
        """Find a user by device_id, or create one if absent."""
        from sqlalchemy import select

        from backend.models.user import User

        if not device_id:
            return None

        result = await session.execute(select(User).where(User.device_id == device_id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(device_id=device_id)
            session.add(user)
            await session.flush()
        return user

    # ── CRUD ────────────────────────────────────────────────────

    async def create(
        self,
        *,
        device_id: str,
        title: str,
        content: str,
        content_type: str = "text",
        grade: int | None = None,
        subject: str | None = None,
        chapter: str | None = None,
        page_number: int | None = None,
    ) -> dict | None:
        """Create a learning moment with an embedding."""
        from backend.models.learning_moment import LearningMoment

        embedding = self.embed(title + ". " + content)

        try:
            async for session in get_db():
                user = await self._get_or_create_user(session, device_id)
                if user is None:
                    logger.warning("Moment create skipped: no device_id")
                    return None

                moment = LearningMoment(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    title=title,
                    content=content or None,
                    content_type=content_type,
                    grade=grade,
                    subject=subject,
                    chapter=chapter,
                    page_number=page_number,
                    embedding=json.dumps(embedding) if embedding else None,
                )
                session.add(moment)
                await session.commit()
                await session.refresh(moment)
                return self._to_dict(moment)
            return None
        except Exception as e:
            logger.error(f"Moment create error: {e}")
            return None

    async def list_for_device(self, device_id: str, limit: int = 100) -> list[dict]:
        """List moments for a device, newest first."""
        from sqlalchemy import select

        from backend.models.learning_moment import LearningMoment

        try:
            async for session in get_db():
                user = await self._get_or_create_user(session, device_id)
                if user is None:
                    return []

                result = await session.execute(
                    select(LearningMoment)
                    .where(LearningMoment.user_id == user.id)
                    .order_by(LearningMoment.created_at.desc())
                    .limit(limit)
                )
                return [self._to_dict(m) for m in result.scalars().all()]
            return []
        except Exception as e:
            logger.error(f"Moment list error: {e}")
            return []

    async def delete(self, device_id: str, moment_id: str) -> bool:
        """Delete a moment owned by the device."""
        from sqlalchemy import delete, select

        from backend.models.learning_moment import LearningMoment

        try:
            async for session in get_db():
                user = await self._get_or_create_user(session, device_id)
                if user is None:
                    return False

                result = await session.execute(
                    select(LearningMoment).where(
                        LearningMoment.id == moment_id,
                        LearningMoment.user_id == user.id,
                    )
                )
                moment = result.scalar_one_or_none()
                if moment is None:
                    return False

                await session.execute(
                    delete(LearningMoment).where(LearningMoment.id == moment.id)
                )
                await session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Moment delete error: {e}")
            return False

    # ── Semantic search ─────────────────────────────────────────

    async def search(
        self,
        device_id: str,
        query: str,
        n_results: int = 5,
    ) -> list[dict]:
        """Search moments by embedding similarity (cosine)."""
        from sqlalchemy import select

        from backend.models.learning_moment import LearningMoment

        query_embedding = self.embed(query)
        if query_embedding is None:
            return []

        try:
            async for session in get_db():
                user = await self._get_or_create_user(session, device_id)
                if user is None:
                    return []

                result = await session.execute(
                    select(LearningMoment).where(LearningMoment.user_id == user.id)
                )
                moments = result.scalars().all()

                scored = []
                for m in moments:
                    if not m.embedding:
                        continue
                    try:
                        vec = json.loads(m.embedding)
                    except (TypeError, ValueError):
                        continue
                    distance = _cosine_distance(query_embedding, vec)
                    scored.append(
                        {
                            "id": m.id,
                            "title": m.title,
                            "content": m.content or "",
                            "content_type": m.content_type,
                            "created_at": m.created_at,
                            "distance": round(distance, 4),
                        }
                    )

                scored.sort(key=lambda x: x["distance"])
                return scored[:n_results]
            return []
        except Exception as e:
            logger.error(f"Moment search error: {e}")
            return []

    # ── Helpers ─────────────────────────────────────────────────

    def _to_dict(self, moment) -> dict:
        return {
            "id": moment.id,
            "title": moment.title,
            "content": moment.content or "",
            "content_type": moment.content_type,
            "file_path": moment.file_path,
            "file_type": moment.file_type,
            "grade": moment.grade,
            "subject": moment.subject,
            "chapter": moment.chapter,
            "page_number": moment.page_number,
            "created_at": moment.created_at.isoformat() if moment.created_at else None,
        }


def _cosine_distance(a: list[float], b: list[float]) -> float:
    """Cosine distance (1 - cosine similarity) between two vectors."""
    if len(a) != len(b) or not a:
        return 1.0
    import math

    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 1.0
    return 1.0 - dot / (na * nb)


# Singleton instance
moment_service = MomentService()

"""
RAG service — retrieval-augmented generation for textbook Q&A.

Uses ChromaDB + CLIP/sentence embeddings to:
1. Index Vietnamese textbook content (SGK) by chunks
2. Retrieve relevant passages for student questions
3. Generate answers grounded in textbook content via Gemini

Supports multiple embedding models with Vietnamese text support.
"""

import logging
import os

logger = logging.getLogger(__name__)

from backend.config import settings


class RagService:
    """
    Retrieval-Augmented Generation service.

    Enables students to ask questions about textbooks and get
    answers grounded in the actual SGK content.
    """

    def __init__(self) -> None:
        self._collection = None
        self._embedding_model = None

    def _initialize(self) -> None:
        """Lazy initialization of ChromaDB and embedding model."""
        if self._collection is not None:
            return
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            os.makedirs(settings.chroma_persist_dir, exist_ok=True)

            client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )

            self._collection = client.get_or_create_collection(
                name=settings.chroma_collection,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"ChromaDB ready: '{settings.chroma_collection}' collection")
        except Exception as e:
            logger.warning(f"ChromaDB not available: {e}")

    @property
    def available(self) -> bool:
        self._initialize()
        return self._collection is not None

    def add_textbook_chunk(
        self,
        chunk_id: str,
        text: str,
        metadata: dict | None = None,
    ) -> bool:
        """
        Index a single chunk of textbook content.

        Args:
            chunk_id: Unique identifier (e.g., 'grade10_math_ch3_p42').
            text: The text content of the chunk.
            metadata: Dict with grade, subject, chapter, page_number, etc.

        Returns:
            True if indexed successfully.
        """
        self._initialize()
        if self._collection is None:
            return False

        try:
            self._collection.add(
                documents=[text],
                ids=[chunk_id],
                metadatas=[metadata or {}],
            )
            return True
        except Exception as e:
            logger.error(f"ChromaDB add error: {e}")
            return False

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[dict]:
        """
        Search textbook content for relevant passages.

        Args:
            query: Student's question or search query.
            n_results: Number of results to return.
            filter_metadata: Optional metadata filter (e.g., {'grade': 10}).

        Returns:
            List of dicts with 'id', 'text', 'metadata', 'distance'.
        """
        self._initialize()
        if self._collection is None:
            return []

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata,
            )

            hits = []
            for i in range(len(results["ids"][0])):
                hits.append(
                    {
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else 0,
                    }
                )
            return hits
        except Exception as e:
            logger.error(f"ChromaDB search error: {e}")
            return []

    def count_chunks(self) -> int:
        """Return the number of indexed textbook chunks."""
        self._initialize()
        if self._collection is None:
            return 0
        try:
            return self._collection.count()
        except Exception:
            return 0


# Singleton instance
rag_service = RagService()

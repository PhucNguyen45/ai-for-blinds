#!/usr/bin/env python3
"""
Seed script: đọc nội dung SGK từ data/sgk/ và index vào ChromaDB.
Hỗ trợ: .txt, .md files.

Usage:
    python data/scripts/seed_rag.py

Environment:
    DATABASE_URL (optional) — nếu có, cũng lưu vào PostgreSQL
    GOOGLE_API_KEY (optional) — nếu có, dùng Gemini để tóm tắt chunks
"""

import os
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)


def find_text_files(sgk_dir: Path) -> list[Path]:
    """Find all .txt and .md files in sgk directory."""
    files = []
    for ext in ("*.txt", "*.md"):
        files.extend(sgk_dir.rglob(ext))
    return sorted(files)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def extract_metadata(filepath: Path) -> dict:
    """Extract grade, subject, chapter from file path structure.
    
    Expected structure:
        data/sgk/{grade}/{subject}/{chapter}.txt
    Example:
        data/sgk/10/Sinh hoc/Bai 18 - Nguyen phan.txt
    """
    parts = filepath.relative_to(*filepath.parts[:3]).parts  # relative to data/
    metadata = {
        "grade": parts[1] if len(parts) > 1 else "",
        "subject": parts[2] if len(parts) > 2 else "",
        "chapter": filepath.stem if filepath.stem else "",
        "source": str(filepath),
    }
    return metadata


def seed_chromadb(chunks: list[tuple[str, dict]]):
    """Index chunks into ChromaDB."""
    try:
        from backend.services.rag_service import rag_service
    except ImportError:
        logger.error("Cannot import rag_service. Make sure backend/ is in PYTHONPATH.")
        return

    if not rag_service.available:
        logger.warning("ChromaDB not available. Skipping.")
        return

    count = 0
    for text, metadata in chunks:
        rag_service.add_textbook_chunk(text, metadata)
        count += 1
        if count % 10 == 0:
            logger.info(f"  Indexed {count} chunks...")

    total = rag_service.count_chunks()
    logger.info(f"Done. Total chunks in ChromaDB: {total}")


def main():
    sgk_dir = Path(__file__).resolve().parent.parent / "sgk"
    if not sgk_dir.exists():
        logger.error(f"SGK directory not found: {sgk_dir}")
        logger.info("Place textbook files in data/sgk/{grade}/{subject}/{chapter}.txt")
        sys.exit(1)

    files = find_text_files(sgk_dir)
    if not files:
        logger.warning(f"No .txt or .md files found in {sgk_dir}")
        logger.info("Create files in: data/sgk/{grade}/{subject}/{chapter}.txt")
        sys.exit(0)

    logger.info(f"Found {len(files)} textbook files")

    all_chunks = []
    for filepath in files:
        metadata = extract_metadata(filepath)
        text = filepath.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        
        for chunk in chunks:
            all_chunks.append((chunk, metadata.copy()))
        
        logger.info(f"  {filepath.name}: {len(chunks)} chunks ({len(text)} chars)")

    logger.info(f"\nTotal chunks to index: {len(all_chunks)}")
    seed_chromadb(all_chunks)
    logger.info("Seed hoàn tất!")


if __name__ == "__main__":
    main()

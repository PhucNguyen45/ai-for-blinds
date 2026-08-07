"""Pytest fixtures for SgBe Vision backend tests."""

import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

# ── Set required env vars BEFORE any backend imports ──
os.environ.setdefault("GOOGLE_API_KEY", "test-fake-api-key")
os.environ.setdefault("YOLO_DEVICE", "cpu")


# ── Helper: create a mock module with named exports ──
def _mock_module(name: str, **attrs) -> types.ModuleType:
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


# ── Mock sqlalchemy.ext.asyncio before database.py imports it ──
sys.modules["sqlalchemy.ext.asyncio"] = _mock_module(
    "sqlalchemy.ext.asyncio",
    create_async_engine=MagicMock(return_value=MagicMock()),
    async_sessionmaker=MagicMock(return_value=MagicMock()),
    AsyncSession=MagicMock(),
)

# ── Mock parent packages needed for sub-package imports ──
for parent in ("google", "edge", "faster_whisper", "paddle", "ultralytics", "chromadb"):
    if parent not in sys.modules:
        sys.modules[parent] = _mock_module(parent)

# ── Mock heavy AI packages ──
_ai_modules = {
    "google.generativeai": MagicMock(),
    "edge_tts": MagicMock(),
    "faster_whisper": MagicMock(),
    "paddleocr": MagicMock(),
    "ultralytics": MagicMock(),
    "cv2": MagicMock(),
    "PIL": MagicMock(),
    "chromadb.config": MagicMock(),
}
for mod_name, mock in _ai_modules.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mock

# chromadb module attributes needed by rag_service imports
if "chromadb" in sys.modules:
    mod = sys.modules["chromadb"]
    mod.PersistentClient = MagicMock()
    mod.Settings = MagicMock

# ── Mock backend.main BEFORE routes import it ──
# Route files do `from backend.main import limiter`, but main.py also imports
# routes, creating a circular dependency. We pre-mock backend.main with a
# REAL Limiter instance so that @limiter.limit() decorators work correctly.
from slowapi import Limiter
from slowapi.util import get_remote_address

_limiter = Limiter(key_func=get_remote_address)

if "backend.main" not in sys.modules:
    backend_main_mock = _mock_module("backend.main", limiter=_limiter)
    sys.modules["backend.main"] = backend_main_mock

# ── Ensure backend is importable ──
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Create a test FastAPI app, registering routers directly.

    Avoids the circular import in backend/main.py (routes → main → routes)
    by importing routers after pre-mocking backend.main with a real Limiter.
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded

    # Import routers (they use limiter from the mocked backend.main)
    from backend.api.routes import describe, detect, money, ocr, rag, search, sonify, stt, tts
    from backend.config import settings

    _app = FastAPI(title=settings.app_name, version=settings.app_version)

    # Rate limiting - reuse the same limiter instance from the mock
    limiter = _limiter
    _app.state.limiter = limiter
    _app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # Register routes
    _app.include_router(describe.router, tags=["Vision"])
    _app.include_router(ocr.router, tags=["OCR"])
    _app.include_router(tts.router, tags=["TTS"])
    _app.include_router(stt.router, tags=["STT"])
    _app.include_router(rag.router, prefix="/rag", tags=["RAG"])
    _app.include_router(detect.router, tags=["Detection"])
    _app.include_router(money.router, tags=["Money"])
    _app.include_router(search.router, tags=["Search"])
    _app.include_router(sonify.router, tags=["Sonification"])

    # Health endpoint
    @_app.get("/")
    def health():
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": settings.app_version,
        }

    return _app


@pytest.fixture
def client(app):
    """Test client with default auth header (X-API-Key)."""
    with TestClient(app) as c:
        c.headers.update({"X-API-Key": "sgbe_dev_key_2024"})
        yield c


@pytest.fixture
def sample_image_bytes():
    """Return a factory that creates minimal valid PNG bytes for testing."""
    import struct
    import zlib

    def _create_png():
        width, height = 1, 1
        ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
        raw_data = b"\x00\xff\x00\x00"
        compressed = zlib.compress(raw_data)
        idat_crc = zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF
        iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF

        png = b"\x89PNG\r\n\x1a\n"
        png += struct.pack(">I", 13) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)
        png += (
            struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", idat_crc)
        )
        png += struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)
        return png

    return _create_png


@pytest.fixture
def sample_audio_bytes():
    """Return a factory that creates minimal WAV bytes for testing STT endpoints."""
    import math
    import struct

    def _create_wav():
        sample_rate = 16000
        duration = 0.1
        num_samples = int(sample_rate * duration)
        samples = []
        for i in range(num_samples):
            sample = int(16000 * math.sin(2 * math.pi * 440 * i / sample_rate))
            samples.append(sample & 0xFFFF)

        data_size = num_samples * 2
        wav = b"RIFF"
        wav += struct.pack("<I", 36 + data_size)
        wav += b"WAVE"
        wav += b"fmt "
        wav += struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
        wav += b"data"
        wav += struct.pack("<I", data_size)
        for s in samples:
            wav += struct.pack("<H", s)
        return wav

    return _create_wav

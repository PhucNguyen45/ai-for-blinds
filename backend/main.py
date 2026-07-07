"""
SgBe Vision — Backend API Entry Point.

FastAPI application with modular route registration.
AI services are lazy-initialized in each service module.
"""

import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.config import configure_logging, settings
from backend.database import init_db
from backend.deps import limiter

configure_logging()
logger = logging.getLogger(__name__)

# ── Routes ─────────────────────────────────────────────────────
from backend.api.routes import describe, detect, ocr, rag, sonify, stt, tts

# ── App Initialization ──────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Trợ lý học tập AI đa phương thức cho học sinh khiếm thị Việt Nam",
)

# ── Rate Limiting ─────────────────────────────────────────────────

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Middleware ────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# ── Route Registration ──────────────────────────────────────────

app.include_router(describe.router, tags=["Vision"])
app.include_router(ocr.router, tags=["OCR"])
app.include_router(tts.router, tags=["TTS"])
app.include_router(stt.router, tags=["STT"])
app.include_router(rag.router, prefix="/rag", tags=["RAG"])
app.include_router(detect.router, tags=["Detection"])
app.include_router(sonify.router, tags=["Sonification"])


# ── Startup / Health ─────────────────────────────────────────────


@app.on_event("startup")
async def startup():
    """Initialize database tables on startup."""
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"Database initialization skipped: {e}")
        logger.warning("Backend will run without database. Some features may be limited.")


@app.get("/")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


# ── Main ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

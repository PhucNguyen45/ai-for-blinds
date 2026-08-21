"""
SgBe Vision — Backend API Entry Point.

FastAPI application with modular route registration.
AI services are lazy-initialized in each service module.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import init_db

# ── Routes ─────────────────────────────────────────────────────
from backend.api.routes import describe, ocr, tts, stt, rag

# ── App Initialization ──────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Trợ lý học tập AI đa phương thức cho học sinh khiếm thị Việt Nam",
)

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


# ── Startup / Health ─────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Initialize database tables on startup."""
    try:
        init_db()
    except Exception as e:
        print(f"Database initialization skipped: {e}")
        print("Backend will run without database. Some features may be limited.")


@app.get("/")
def health():
    """Health check endpoint."""
    from backend.services.vlm_service import vlm_service

    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "vlm": {
            "provider": settings.vlm_provider,
            "model": vlm_service.model_name,
            "configured": bool(settings.vlm_api_key or settings.google_api_key),
        },
    }


# ── Main ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

"""
SgBe Vision — Backend Configuration.

Centralized settings loaded from environment variables.
All AI services, database, and app settings are configured here.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Settings:
    # ── App ──────────────────────────────────────────────────────
    app_name: str = "SgBe Vision API"
    app_version: str = "1.0.0"
    debug: bool = os.environ.get("DEBUG", "false").lower() == "true"
    host: str = os.environ.get("HOST", "0.0.0.0")
    port: int = int(os.environ.get("PORT", "8000"))

    # ── CORS ─────────────────────────────────────────────────────
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    cors_credentials: bool = True
    cors_methods: list[str] = field(default_factory=lambda: ["*"])
    cors_headers: list[str] = field(default_factory=lambda: ["*"])

    # ── Gemini (VLM) ─────────────────────────────────────────────
    google_api_key: Optional[str] = os.environ.get("GOOGLE_API_KEY")
    gemini_model: str = "gemini-2.5-flash"

    # ── Database (PostgreSQL + pgvector) ─────────────────────────
    database_url: Optional[str] = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://sgbe_admin:sgbe_secret@localhost:5432/sgbe_vision",
    )

    # ── File Upload ──────────────────────────────────────────────
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    allowed_content_types: set[str] = field(default_factory=lambda: {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/bmp",
    })

    # ── Edge TTS ─────────────────────────────────────────────────
    tts_voice: str = "vi-VN-HoaiMyNeural"  # Default Vietnamese voice
    tts_output_dir: str = os.environ.get("TTS_OUTPUT_DIR", "/tmp/sgbe_tts")

    # ── PaddleOCR ────────────────────────────────────────────────
    ocr_lang: str = "vi"  # Vietnamese primary, also detects English
    ocr_use_angle_cls: bool = True
    ocr_show_log: bool = False

    # ── Whisper (STT) ────────────────────────────────────────────
    whisper_model_size: str = os.environ.get("WHISPER_MODEL", "base")
    whisper_device: str = os.environ.get("WHISPER_DEVICE", "cpu")
    whisper_compute_type: str = os.environ.get("WHISPER_COMPUTE", "int8")

    # ── ChromaDB (RAG) ──────────────────────────────────────────
    chroma_persist_dir: str = os.environ.get(
        "CHROMA_PERSIST_DIR", "./data/embeddings"
    )
    chroma_collection: str = "sgbe_textbook"
    embedding_model: str = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # ── YOLOv8 (Object Detection) ───────────────────────────────
    yolo_model_path: str = os.environ.get(
        "YOLO_MODEL_PATH", "./models/yolo/yolov8n.pt"
    )
    yolo_confidence: float = 0.5

    # ── Validate required settings ──────────────────────────────
    def validate(self) -> None:
        if not self.google_api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY environment variable is required.\n"
                "Set it with: export GOOGLE_API_KEY='your-key-here'"
            )


# Singleton settings instance
settings = Settings()

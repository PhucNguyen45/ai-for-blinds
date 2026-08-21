"""
SgBe Vision — Backend Configuration.

Centralized settings loaded from environment variables.
All AI services, database, and app settings are configured here.
"""

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from the repo root so `os.environ` below sees it.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass
class Settings:
    # ── App ──────────────────────────────────────────────────────
    app_name: str = "SgBe Vision API"
    app_version: str = "1.0.0"
    debug: bool = os.environ.get("DEBUG", "false").lower() == "true"
    host: str = os.environ.get("HOST", "0.0.0.0")
    port: int = int(os.environ.get("PORT", "8000"))

    # ── CORS ─────────────────────────────────────────────────────
    # A wildcard origin together with credentials is rejected by browsers, and
    # the mobile client never sends cookies — so credentials stay off.
    cors_origins: list[str] = field(
        default_factory=lambda: os.environ.get("CORS_ORIGINS", "*").split(",")
    )
    cors_credentials: bool = False
    cors_methods: list[str] = field(default_factory=lambda: ["*"])
    cors_headers: list[str] = field(default_factory=lambda: ["*"])

    # ── VLM ──────────────────────────────────────────────────────
    # Any OpenAI-compatible endpoint. OpenRouter while developing, a local
    # vLLM / SGLang server for the on-premise deployment — same protocol, so
    # only these values change.
    vlm_api_key: Optional[str] = os.environ.get("OPENROUTER_API_KEY")
    vlm_base_url: str = os.environ.get(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    vlm_model: str = os.environ.get("VLM_MODEL", "google/gemma-4-31b-it:free")
    vlm_max_tokens: int = int(os.environ.get("VLM_MAX_TOKENS", "1024"))
    vlm_temperature: float = float(os.environ.get("VLM_TEMPERATURE", "0.3"))

    # ── Gemini — chỉ dùng khi không có OPENROUTER_API_KEY ────────
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
    tts_output_dir: str = os.environ.get(
        "TTS_OUTPUT_DIR", os.path.join(tempfile.gettempdir(), "sgbe_tts")
    )

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
    # all-MiniLM-L6-v2 là model tiếng Anh; tìm kiếm tiếng Việt sẽ lệch.
    embedding_model: str = os.environ.get(
        "EMBEDDING_MODEL", "bkai-foundation-models/vietnamese-bi-encoder"
    )

    # ── YOLOv8 (Object Detection) ───────────────────────────────
    yolo_model_path: str = os.environ.get(
        "YOLO_MODEL_PATH", "./models/yolo/yolov8n.pt"
    )
    yolo_confidence: float = 0.5

    # ── Validate required settings ──────────────────────────────
    @property
    def vlm_provider(self) -> str:
        """Which client `vlm_service` builds: 'openai' or 'gemini'."""
        return "openai" if self.vlm_api_key else "gemini"

    def validate(self) -> None:
        if self.vlm_api_key or self.google_api_key:
            return
        raise RuntimeError(
            "Chưa có khoá cho mô hình thị giác. Đặt OPENROUTER_API_KEY "
            "(khuyến nghị) hoặc GOOGLE_API_KEY trong file .env ở gốc repo."
        )


# Singleton settings instance
settings = Settings()

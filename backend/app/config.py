"""Cấu hình đọc từ biến môi trường (file backend/.env).

Đổi từ OpenRouter sang máy chủ on-premise (vLLM) chỉ cần đổi VLM_BASE_URL,
VLM_API_KEY và VLM_MODEL — không sửa code.
"""
import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")


class Settings:
    def __init__(self) -> None:
        # mock: trả dữ liệu giả, không cần mạng (để làm app song song)
        # openai: gọi API tương thích OpenAI (OpenRouter hoặc vLLM) bằng prompt prompts/v1 của backend
        # ai: gọi module AI của Phúc (ai/pipeline.py: cổng chất lượng ảnh, mô tả, hỏi đáp có tính toán);
        #     nhà cung cấp và model đọc từ ai/.env (một chỗ duy nhất, xem ai/.env.example)
        self.vlm_mode = os.getenv("VLM_MODE", "mock").lower()
        self.ai_dir = Path(os.getenv("AI_DIR", str(REPO_ROOT / "ai")))
        self.vlm_base_url = os.getenv("VLM_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
        self.vlm_api_key = os.getenv("VLM_API_KEY", "")
        self.vlm_model = os.getenv("VLM_MODEL", "qwen/qwen3-vl-30b-a3b-instruct")
        self.vlm_timeout = float(os.getenv("VLM_TIMEOUT", "120"))
        self.vlm_max_retries = int(os.getenv("VLM_MAX_RETRIES", "1"))
        self.vlm_max_tokens = int(os.getenv("VLM_MAX_TOKENS", "1024"))
        self.vlm_temperature = float(os.getenv("VLM_TEMPERATURE", "0.2"))

        self.prompt_version = os.getenv("PROMPT_VERSION", "v1")
        self.prompts_dir = Path(os.getenv("PROMPTS_DIR", str(REPO_ROOT / "prompts")))
        self.data_dir = Path(os.getenv("DATA_DIR", str(REPO_ROOT / "data")))

        self.max_image_mb = float(os.getenv("MAX_IMAGE_MB", "10"))
        self.image_max_side = int(os.getenv("IMAGE_MAX_SIDE", "1600"))
        self.max_audio_mb = float(os.getenv("MAX_AUDIO_MB", "10"))

        # mock: trả câu cố định. Toàn sẽ thêm chế độ "phowhisper" trong app/stt.py
        self.stt_mode = os.getenv("STT_MODE", "mock").lower()
        self.mock_stt_text = os.getenv("MOCK_STT_TEXT", "Trên lược đồ có những tỉnh nào?")
        self.mock_delay = float(os.getenv("MOCK_DELAY_SECONDS", "1.0"))

    def ai_config(self) -> dict:
        """Cấu hình của module AI: ai/.env, biến môi trường ghi đè (cùng quy tắc với ai/vlm/describer.py)."""
        return {**dotenv_values(self.ai_dir / ".env"), **os.environ}

    def ai_model_label(self) -> str:
        """Ví dụ "lmstudio:google/gemma-4-e4b"; chỉ tên nhà cung cấp nếu chưa đặt model."""
        cfg = self.ai_config()
        provider = (cfg.get("VLM_PROVIDER") or "openrouter").strip().lower()
        model = (cfg.get(f"{provider.upper()}_MODEL") or "").split("#")[0].strip()
        return f"{provider}:{model}" if model else provider

    @property
    def model_name(self) -> str:
        if self.vlm_mode == "mock":
            return "mock"
        if self.vlm_mode == "ai":
            return self.ai_model_label()
        return self.vlm_model


settings = Settings()

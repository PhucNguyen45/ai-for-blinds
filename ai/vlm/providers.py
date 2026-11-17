"""Chọn nhà cung cấp VLM: OpenRouter hoặc Google AI Studio (Gemini API).

Cả hai đều dùng giao thức chat/completions kiểu OpenAI, nên chỉ khác địa chỉ, khóa, tên model
và vài tham số. Nhà cung cấp lấy từ tham số `provider`, nếu không thì biến `VLM_PROVIDER`,
mặc định "openrouter" (giữ hành vi cũ).

Biến môi trường:
  openrouter: OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL (tùy chọn)
  google:     GOOGLE_API_KEY (hoặc GEMINI_API_KEY), GOOGLE_MODEL, GOOGLE_BASE_URL (tùy chọn),
              GOOGLE_REASONING_EFFORT (mặc định "none"; đặt rỗng để không gửi tham số)

Thông báo lỗi ở đây không bao giờ chứa giá trị khóa.
"""

from __future__ import annotations

from dataclasses import dataclass

PROVIDERS = ("openrouter", "google")
DEFAULT_BASE_URLS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "google": "https://generativelanguage.googleapis.com/v1beta/openai",
}


class ConfigError(Exception):
    """Thiếu hoặc sai cấu hình; message an toàn để trả cho người gọi."""


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    api_key: str = ""
    model: str = ""
    reasoning_effort: str | None = None

    def __repr__(self) -> str:  # không để lộ khóa khi in log
        return f"Provider(name={self.name!r}, model={self.model!r}, base_url={self.base_url!r})"


def resolve_provider(config: dict, provider: str | None = None,
                     model: str | None = None) -> Provider:
    name = (provider or config.get("VLM_PROVIDER") or "openrouter").strip().lower()
    if name not in PROVIDERS:
        raise ConfigError(f"Nhà cung cấp không hợp lệ (chấp nhận: {', '.join(PROVIDERS)}).")

    if name == "openrouter":
        key = config.get("OPENROUTER_API_KEY")
        chosen = model or config.get("OPENROUTER_MODEL")
        base = config.get("OPENROUTER_BASE_URL") or DEFAULT_BASE_URLS[name]
        effort = None
        missing = "OPENROUTER_API_KEY / OPENROUTER_MODEL"
    else:
        key = config.get("GOOGLE_API_KEY") or config.get("GEMINI_API_KEY")
        chosen = model or config.get("GOOGLE_MODEL")
        for prefix in ("google/", "models/"):  # tên kiểu OpenRouter / kiểu danh sách của Google
            if chosen and chosen.startswith(prefix):
                chosen = chosen[len(prefix):]
        base = config.get("GOOGLE_BASE_URL") or DEFAULT_BASE_URLS[name]
        effort = config.get("GOOGLE_REASONING_EFFORT", "none").strip() or None
        missing = "GOOGLE_API_KEY / GOOGLE_MODEL"

    if not key or not chosen:
        raise ConfigError(f"Thiếu cấu hình cho nhà cung cấp '{name}' ({missing}).")
    return Provider(name=name, base_url=base.rstrip("/"), api_key=key, model=chosen,
                    reasoning_effort=effort)

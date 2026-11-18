"""Chọn nhà cung cấp VLM: OpenRouter, Google AI Studio (Gemini API) hoặc LM Studio chạy cục bộ.

Cả ba đều dùng giao thức chat/completions kiểu OpenAI, nên chỉ khác địa chỉ, khóa, tên model
và vài tham số. Nhà cung cấp lấy từ tham số `provider`, nếu không thì biến `VLM_PROVIDER`,
mặc định "openrouter" (giữ hành vi cũ).

Biến môi trường:
  openrouter: OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL (tùy chọn)
  google:     GOOGLE_API_KEY (hoặc GEMINI_API_KEY), GOOGLE_MODEL, GOOGLE_BASE_URL (tùy chọn),
              GOOGLE_REASONING_EFFORT (mặc định "none"; đặt rỗng để không gửi tham số)
  lmstudio:   LMSTUDIO_BASE_URL (tùy chọn; bỏ trống = tự dò), LMSTUDIO_MODEL (bỏ trống = model
              đầu tiên LM Studio báo), LMSTUDIO_API_KEY (tùy chọn; LM Studio mặc định không cần)

LM Studio chạy trên Windows còn mã chạy trong WSL2 (chế độ NAT) nên "localhost" thường KHÔNG tới
được Windows; mã tự thử localhost, cổng mặc định của WSL (gateway) và nameserver trong WSL.

Thông báo lỗi ở đây không bao giờ chứa giá trị khóa.
"""

from __future__ import annotations

import socket
import struct
from dataclasses import dataclass
from functools import lru_cache

import httpx

PROVIDERS = ("openrouter", "google", "lmstudio")
DEFAULT_BASE_URLS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "google": "https://generativelanguage.googleapis.com/v1beta/openai",
    "lmstudio": "http://localhost:1234/v1",
}
DEFAULT_TIMEOUTS = {"openrouter": 60.0, "google": 60.0, "lmstudio": 300.0}  # mô hình cục bộ chậm hơn
LMSTUDIO_PORT = 1234


class ConfigError(Exception):
    """Thiếu hoặc sai cấu hình; message an toàn để trả cho người gọi."""


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    api_key: str = ""
    model: str = ""
    reasoning_effort: str | None = None
    timeout: float = 60.0

    def __repr__(self) -> str:  # không để lộ khóa khi in log
        return f"Provider(name={self.name!r}, model={self.model!r}, base_url={self.base_url!r})"


# ---------------------------------------------------------------- LM Studio: tự dò

def _wsl_gateway() -> str | None:
    """Địa chỉ Windows host trong WSL2 NAT = gateway mặc định (đọc /proc/net/route)."""
    try:
        with open("/proc/net/route", encoding="utf-8") as f:
            for line in list(f)[1:]:
                parts = line.split()
                if len(parts) > 2 and parts[1] == "00000000":
                    return socket.inet_ntoa(struct.pack("<L", int(parts[2], 16)))
    except (OSError, ValueError):
        pass
    return None


def _wsl_nameserver() -> str | None:
    try:
        with open("/etc/resolv.conf", encoding="utf-8") as f:
            for line in f:
                if line.startswith("nameserver"):
                    return line.split()[1]
    except (OSError, IndexError):
        pass
    return None


def lmstudio_candidates() -> list[str]:
    hosts = ["localhost", _wsl_gateway(), _wsl_nameserver()]
    seen: list[str] = []
    for h in hosts:
        if h and h not in seen:
            seen.append(h)
    return [f"http://{h}:{LMSTUDIO_PORT}/v1" for h in seen]


@lru_cache(maxsize=1)
def find_lmstudio_url(timeout: float = 1.5) -> str | None:
    """Trả địa chỉ LM Studio đầu tiên trả lời GET /models; None nếu không tới được."""
    for base in lmstudio_candidates():
        try:
            if httpx.get(base + "/models", timeout=timeout).status_code == 200:
                return base
        except httpx.HTTPError:
            continue
    return None


def first_lmstudio_model(base_url: str, timeout: float = 5.0) -> str | None:
    try:
        r = httpx.get(base_url + "/models", timeout=timeout)
        ids = [m["id"] for m in r.json().get("data", [])] if r.status_code == 200 else []
    except (httpx.HTTPError, ValueError, KeyError):
        return None
    return ids[0] if ids else None


# ---------------------------------------------------------------- giải quyết cấu hình

def resolve_provider(config: dict, provider: str | None = None,
                     model: str | None = None) -> Provider:
    name = (provider or config.get("VLM_PROVIDER") or "openrouter").strip().lower()
    if name not in PROVIDERS:
        raise ConfigError(f"Nhà cung cấp không hợp lệ (chấp nhận: {', '.join(PROVIDERS)}).")

    if name == "lmstudio":
        base = (config.get("LMSTUDIO_BASE_URL") or "").strip() or find_lmstudio_url()
        if not base:
            raise ConfigError(
                "Không kết nối được LM Studio: hãy bật server (tab Developer), bật 'Serve on Local "
                "Network', cho phép cổng 1234 qua tường lửa Windows, hoặc đặt LMSTUDIO_BASE_URL.")
        base = base.rstrip("/")
        chosen = model or config.get("LMSTUDIO_MODEL") or first_lmstudio_model(base)
        if not chosen:
            raise ConfigError("LM Studio chưa nạp model nào: nạp một model thị giác hoặc đặt "
                              "LMSTUDIO_MODEL.")
        return Provider(name=name, base_url=base, api_key=config.get("LMSTUDIO_API_KEY") or "lm-studio",
                        model=chosen, timeout=DEFAULT_TIMEOUTS[name])

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
                    reasoning_effort=effort, timeout=DEFAULT_TIMEOUTS[name])


def lmstudio_loaded_config(root, model):
    """Cấu hình instance đang nạp của `model` (API gốc của LM Studio, không phải /v1) hoặc None."""
    r = httpx.get(root + "/api/v1/models", timeout=10)
    r.raise_for_status()
    for m in r.json().get("models", []):
        if m.get("key") == model and m.get("loaded_instances"):
            return {"key": m["key"], "quantization": m.get("quantization"),
                    "size_bytes": m.get("size_bytes"), "params": m.get("params_string"),
                    "max_context_length": m.get("max_context_length"),
                    "instance": m["loaded_instances"][0]}
    return None

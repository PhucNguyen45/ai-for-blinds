"""Module AI tối thiểu: ảnh học liệu -> DescriptionResult (hợp đồng v0.1).

Hiện chỉ hỗ trợ prompt B0 (văn bản 4 mục). B0 chưa trích xuất dữ kiện có cấu trúc nên
`facts` rỗng, `image_type` là "unknown" và `question_answering_ready` là False; các trường
này sẽ được điền khi có phương pháp B1.

Hàm `describe_image` KHÔNG ném ngoại lệ vì lỗi vận hành (mạng, HTTP, cấu hình, ảnh);
nó trả về `status="error"` kèm `error` để backend xử lý thống nhất.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import httpx
from dotenv import dotenv_values

from contract.models import (
    DescriptionResult, ErrorCode, ErrorInfo, Meta, Usage,
)
from vlm.openrouter_client import build_chat_payload, post_chat_completion

AI_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = AI_ROOT / "prompts"
SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
PROMPT_ID_RE = re.compile(r"^[a-z0-9_]+$")

PostFn = Callable[..., httpx.Response]


def _error(code: ErrorCode, message: str, retryable: bool, *, image_id=None,
           image_sha256=None, meta=None, http_status=None) -> DescriptionResult:
    return DescriptionResult(
        image_id=image_id, image_sha256=image_sha256, status="error", meta=meta,
        error=ErrorInfo(code=code, message=message, retryable=retryable,
                        http_status=http_status),
    )


def _load_prompt(prompt_id: str) -> str:
    if not PROMPT_ID_RE.fullmatch(prompt_id):
        raise ValueError(f"prompt_id không hợp lệ: {prompt_id!r}")
    path = PROMPTS_DIR / f"{prompt_id}.txt"
    if not path.is_file():
        raise ValueError(f"Không tìm thấy prompt: {prompt_id}")
    return path.read_text(encoding="utf-8").strip()


def _extract_summary(text: str) -> str:
    """Lấy nội dung mục '1. Chủ đề' của B0; nếu không có, lấy câu đầu tiên."""
    match = re.search(r"(?m)^\s*1\.\s*[^:\n]{0,20}:\s*(.+?)(?=^\s*2\.|\Z)", text, re.S)
    summary = (match.group(1) if match else text).strip()
    first = re.split(r"(?<=[.!?])\s", summary, maxsplit=1)[0]
    return re.sub(r"\s+", " ", first).strip()


def describe_image(
    image_path: str | Path,
    *,
    image_id: str | None = None,
    prompt_id: str = "b0_v1",
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 600,
    timeout: float = 60.0,
    post: PostFn = post_chat_completion,
    env: dict | None = None,
) -> DescriptionResult:
    """Diễn giải một ảnh học liệu bằng VLM và trả về DescriptionResult."""
    path = Path(image_path).expanduser()

    if path.suffix.lower() not in SUPPORTED_SUFFIXES or not path.is_file():
        return _error("invalid_image", "Ảnh không tồn tại hoặc định dạng không được hỗ trợ.",
                      False, image_id=image_id)
    data = path.read_bytes()
    if not data or len(data) > MAX_IMAGE_BYTES:
        return _error("invalid_image", "Ảnh rỗng hoặc vượt quá 10 MB.", False,
                      image_id=image_id)
    sha = hashlib.sha256(data).hexdigest()

    try:
        prompt = _load_prompt(prompt_id)
    except ValueError as exc:
        return _error("config_error", str(exc), False, image_id=image_id, image_sha256=sha)

    config = env if env is not None else {**dotenv_values(AI_ROOT / ".env"), **os.environ}
    api_key = config.get("OPENROUTER_API_KEY")
    base_url = config.get("OPENROUTER_BASE_URL")
    model = model or config.get("OPENROUTER_MODEL")
    if not (api_key and base_url and model):
        return _error("config_error", "Thiếu cấu hình OpenRouter (khóa, địa chỉ hoặc model).",
                      False, image_id=image_id, image_sha256=sha)

    created = datetime.now(timezone.utc)
    meta = Meta(
        model=model, prompt_id=prompt_id,
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        temperature=temperature, max_tokens=max_tokens, created_at_utc=created,
    )
    ctx = {"image_id": image_id, "image_sha256": sha, "meta": meta}

    payload = build_chat_payload(model, prompt, str(path), temperature, max_tokens)
    start = time.perf_counter()
    try:
        response = post(payload, api_key, base_url, timeout=timeout)
    except httpx.TimeoutException:
        return _error("timeout", "Hết thời gian chờ mô hình.", True, **ctx)
    except httpx.HTTPError:
        return _error("http_error", "Lỗi kết nối tới dịch vụ mô hình.", True, **ctx)
    meta.latency_seconds = round(time.perf_counter() - start, 3)

    if response.status_code != 200:
        retryable = response.status_code in (408, 429) or response.status_code >= 500
        return _error("http_error", f"Dịch vụ mô hình trả về HTTP {response.status_code}.",
                      retryable, http_status=response.status_code, **ctx)

    try:
        body = response.json()
        choice = body["choices"][0]
        text = (choice["message"].get("content") or "").strip()
    except (ValueError, KeyError, IndexError, TypeError):
        return _error("empty_response", "Phản hồi của mô hình không đúng định dạng.", True, **ctx)

    meta.finish_reason = choice.get("finish_reason")
    usage = body.get("usage") or {}
    meta.usage = Usage(prompt_tokens=usage.get("prompt_tokens"),
                       completion_tokens=usage.get("completion_tokens"))

    if not text:
        return _error("empty_response", "Mô hình không trả về nội dung.", True, **ctx)

    truncated = meta.finish_reason == "length"
    return DescriptionResult(
        image_id=image_id, image_sha256=sha, image_type="unknown",
        status="partial" if truncated else "ok",
        summary_vi=_extract_summary(text), interpretation_vi=text,
        uncertainties=(["Câu trả lời bị cắt do giới hạn độ dài."] if truncated else []),
        question_answering_ready=False, meta=meta,
    )

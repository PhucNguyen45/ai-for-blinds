"""Mô tả ảnh học liệu bằng một lượt gọi VLM (phương pháp B0, B0e, B0g) -> DescriptionResult (hợp đồng v0.1).

Các prompt khác nhau chỉ ở nội dung (xem `ai/prompts/`): `b0_v1` (gốc), `b0e_v1` (nêu đủ giá trị), `b0g_v1` (thêm
hướng dẫn "ảnh không đọc được, chụp lại"). B0 chưa trích xuất dữ kiện có cấu trúc nên `facts` rỗng, `image_type`
là "unknown"; phương pháp hai bước nằm ở `vlm/b1.py`.

`describe_image` KHÔNG ném ngoại lệ vì lỗi vận hành (mạng, HTTP, cấu hình, ảnh): nó trả về `status="error"`
kèm `error` để backend xử lý thống nhất.
"""

from __future__ import annotations

import hashlib
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values

from contract.models import DescriptionResult, Meta, Usage
from vlm.client import build_chat_payload, post_chat_completion
from vlm.common import (
    AI_ROOT, MAX_IMAGE_BYTES, SUPPORTED_SUFFIXES, UNREADABLE_RE, PostFn, StageFailure, chat_vi, error_result, extract_summary,
    load_prompt, strip_markdown,
)
from vlm.providers import ConfigError, resolve_provider


def describe_image(
    image_path: str | Path,
    *,
    image_id: str | None = None,
    prompt_id: str = "b0_v1",
    model: str | None = None,
    provider: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 600,
    timeout: float | None = None,
    post: PostFn = post_chat_completion,
    env: dict | None = None,
) -> DescriptionResult:
    """Diễn giải một ảnh học liệu bằng VLM và trả về DescriptionResult."""
    path = Path(image_path).expanduser()

    if path.suffix.lower() not in SUPPORTED_SUFFIXES or not path.is_file():
        return error_result("invalid_image", "Ảnh không tồn tại hoặc định dạng không được hỗ trợ.",
                      False, image_id=image_id)
    data = path.read_bytes()
    if not data or len(data) > MAX_IMAGE_BYTES:
        return error_result("invalid_image", "Ảnh rỗng hoặc vượt quá 10 MB.", False,
                      image_id=image_id)
    sha = hashlib.sha256(data).hexdigest()

    try:
        prompt = load_prompt(prompt_id)
    except ValueError as exc:
        return error_result("config_error", str(exc), False, image_id=image_id, image_sha256=sha)

    config = env if env is not None else {**dotenv_values(AI_ROOT / ".env"), **os.environ}
    try:
        prov = resolve_provider(config, provider, model)
    except ConfigError as exc:
        return error_result("config_error", str(exc), False, image_id=image_id, image_sha256=sha)
    api_key, base_url, model = prov.api_key, prov.base_url, prov.model
    timeout = timeout or prov.timeout

    created = datetime.now(timezone.utc)
    meta = Meta(
        model=model, provider=prov.name, prompt_id=prompt_id,
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        temperature=temperature, max_tokens=max_tokens, created_at_utc=created,
    )
    ctx = {"image_id": image_id, "image_sha256": sha, "meta": meta}

    payload = build_chat_payload(model, prompt, str(path), temperature, max_tokens,
                                 provider=prov.name, reasoning_effort=prov.reasoning_effort)
    try:
        text, finish, usage, latency, cleaned = chat_vi(payload, api_key, base_url, timeout, post, prov.name)
    except StageFailure as exc:
        return error_result(exc.code, exc.message, exc.retryable, http_status=exc.http_status, **ctx)
    meta.latency_seconds = round(latency, 3)
    meta.finish_reason = finish
    meta.usage = Usage(prompt_tokens=usage.get("prompt_tokens"), completion_tokens=usage.get("completion_tokens"))

    truncated = meta.finish_reason == "length"
    text = strip_markdown(unicodedata.normalize("NFC", text))
    flagged = UNREADABLE_RE.match(text)
    if flagged:
        reason = re.sub(r"\s+", " ", text[flagged.end():]).strip() or (
            "Ảnh chưa đủ rõ để đọc. Bạn chụp lại giúp mình nhé.")
        return DescriptionResult(image_id=image_id, image_sha256=sha, status="unreadable",
                                 summary_vi=reason, meta=meta)
    return DescriptionResult(
        image_id=image_id, image_sha256=sha, image_type="unknown",
        status="partial" if truncated else "ok",
        summary_vi=extract_summary(text), interpretation_vi=text,
        uncertainties=((["Câu trả lời bị cắt do giới hạn độ dài."] if truncated else [])
                       + (["Đã loại ký tự ngoài tiếng Việt khỏi câu trả lời."] if cleaned else [])),
        question_answering_ready=False, meta=meta,
    )

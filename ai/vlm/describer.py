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
from vlm.providers import ConfigError, resolve_provider

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


def strip_markdown(text: str) -> str:
    """Bỏ ký hiệu Markdown mà một số model vẫn sinh ra (in đậm, tiêu đề, gạch đầu dòng, mã)."""
    text = re.sub(r"```[a-z]*\n?|`", "", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = re.sub(r"(\*\*|__)(.+?)\1", r"\2", text, flags=re.S)
    text = re.sub(r"(?m)^(\s*)[-*•]\s+", r"\1", text)
    text = re.sub(r"(?<!\w)\*(\S[^*\n]*?)\*(?!\w)", r"\1", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _http_message(status: int) -> str:
    if status in (400, 404):
        return (f"Dịch vụ mô hình trả về HTTP {status}: kiểm tra tên model và tham số "
                "(model có thể không tồn tại hoặc không còn khả dụng).")
    return f"Dịch vụ mô hình trả về HTTP {status}."


def _extract_summary(text: str) -> str:
    """Lấy nội dung mục '1. Chủ đề' của B0; nếu không có, lấy câu đầu tiên."""
    match = re.search(r"(?m)^\s*1\.\s*[^:\n]{0,20}:\s*(.+?)(?=^\s*2\.|\Z)", text, re.S)
    summary = (match.group(1) if match else text).strip()
    summary = re.sub(r"^\s*\d+\.\s*", "", summary)
    first = re.split(r"(?<=[.!?])\s", summary, maxsplit=1)[0]
    return re.sub(r"\s+", " ", first).strip()


def describe_image(
    image_path: str | Path,
    *,
    image_id: str | None = None,
    prompt_id: str = "b0_v1",
    model: str | None = None,
    provider: str | None = None,
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
    try:
        prov = resolve_provider(config, provider, model)
    except ConfigError as exc:
        return _error("config_error", str(exc), False, image_id=image_id, image_sha256=sha)
    api_key, base_url, model = prov.api_key, prov.base_url, prov.model

    created = datetime.now(timezone.utc)
    meta = Meta(
        model=model, provider=prov.name, prompt_id=prompt_id,
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        temperature=temperature, max_tokens=max_tokens, created_at_utc=created,
    )
    ctx = {"image_id": image_id, "image_sha256": sha, "meta": meta}

    payload = build_chat_payload(model, prompt, str(path), temperature, max_tokens,
                                 provider=prov.name, reasoning_effort=prov.reasoning_effort)
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
        return _error("http_error", _http_message(response.status_code),
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
    text = strip_markdown(text)
    return DescriptionResult(
        image_id=image_id, image_sha256=sha, image_type="unknown",
        status="partial" if truncated else "ok",
        summary_vi=_extract_summary(text), interpretation_vi=text,
        uncertainties=(["Câu trả lời bị cắt do giới hạn độ dài."] if truncated else []),
        question_answering_ready=False, meta=meta,
    )


# --------------------------------------------------------------------------
# B1: trích xuất dữ kiện có cấu trúc (ảnh -> JSON), rồi diễn giải (JSON -> văn bản)
# --------------------------------------------------------------------------

import json as _json

from contract.models import Fact

_IMAGE_TYPES = {"bar_chart", "line_chart", "pie_chart", "table", "flow_diagram",
                "cycle_diagram", "geometry", "map", "text", "other"}


class _StageFailure(Exception):
    def __init__(self, code: ErrorCode, message: str, retryable: bool, http_status=None):
        self.code, self.message = code, message
        self.retryable, self.http_status = retryable, http_status


def _chat_once(payload, api_key, base_url, timeout, post):
    """Gọi một lần; trả (text, finish_reason, usage_dict, latency) hoặc ném _StageFailure."""
    start = time.perf_counter()
    try:
        response = post(payload, api_key, base_url, timeout=timeout)
    except httpx.TimeoutException:
        raise _StageFailure("timeout", "Hết thời gian chờ mô hình.", True)
    except httpx.HTTPError:
        raise _StageFailure("http_error", "Lỗi kết nối tới dịch vụ mô hình.", True)
    latency = time.perf_counter() - start
    if response.status_code != 200:
        retryable = response.status_code in (408, 429) or response.status_code >= 500
        raise _StageFailure("http_error", _http_message(response.status_code),
                            retryable, response.status_code)
    try:
        body = response.json()
        choice = body["choices"][0]
        text = (choice["message"].get("content") or "").strip()
    except (ValueError, KeyError, IndexError, TypeError):
        raise _StageFailure("empty_response", "Phản hồi của mô hình không đúng định dạng.", True)
    if not text:
        raise _StageFailure("empty_response", "Mô hình không trả về nội dung.", True)
    return text, choice.get("finish_reason"), body.get("usage") or {}, latency


def parse_extraction(text: str) -> dict:
    """Parse JSON của bước trích xuất; chấp nhận khung ```json và văn bản thừa quanh JSON."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("không tìm thấy đối tượng JSON")
    data = _json.loads(cleaned[start:end + 1])
    if not isinstance(data, dict) or not isinstance(data.get("facts"), list):
        raise ValueError("thiếu danh sách facts")
    facts = []
    for item in data["facts"]:
        if not isinstance(item, dict):
            continue
        parts = [str(item.get(k, "")).strip() for k in ("subject", "predicate", "object")]
        if not any(parts):
            continue
        evidence = str(item.get("evidence", "")).strip() or None
        facts.append(Fact(subject=parts[0], predicate=parts[1], object=parts[2],
                          evidence=evidence))
    uncertainties = [str(u).strip() for u in (data.get("uncertainties") or [])
                     if str(u).strip()] if isinstance(data.get("uncertainties"), list) else []
    image_type = data.get("image_type") if data.get("image_type") in _IMAGE_TYPES else "other"
    status = "unreadable" if data.get("status") == "unreadable" else "ok"
    return {"image_type": image_type, "status": status, "facts": facts,
            "uncertainties": uncertainties}


def describe_image_b1(
    image_path: str | Path,
    *,
    image_id: str | None = None,
    model: str | None = None,
    provider: str | None = None,
    temperature: float = 0.2,
    extract_max_tokens: int = 1500,
    describe_max_tokens: int = 800,
    timeout: float = 90.0,
    post: PostFn = post_chat_completion,
    env: dict | None = None,
    trace: dict | None = None,
) -> DescriptionResult:
    """B1: (1) ảnh -> JSON dữ kiện; (2) JSON -> diễn giải tiếng Việt (không gửi lại ảnh).

    `trace` (tùy chọn) nhận văn bản thô của từng bước để lưu bằng chứng thực nghiệm.
    """
    path = Path(image_path).expanduser()
    if path.suffix.lower() not in SUPPORTED_SUFFIXES or not path.is_file():
        return _error("invalid_image", "Ảnh không tồn tại hoặc định dạng không được hỗ trợ.",
                      False, image_id=image_id)
    data = path.read_bytes()
    if not data or len(data) > MAX_IMAGE_BYTES:
        return _error("invalid_image", "Ảnh rỗng hoặc vượt quá 10 MB.", False, image_id=image_id)
    sha = hashlib.sha256(data).hexdigest()

    try:
        extract_prompt = _load_prompt("b1_extract_v1")
        describe_prompt = _load_prompt("b1_describe_v1")
    except ValueError as exc:
        return _error("config_error", str(exc), False, image_id=image_id, image_sha256=sha)

    config = env if env is not None else {**dotenv_values(AI_ROOT / ".env"), **os.environ}
    try:
        prov = resolve_provider(config, provider, model)
    except ConfigError as exc:
        return _error("config_error", str(exc), False, image_id=image_id, image_sha256=sha)
    api_key, base_url, model = prov.api_key, prov.base_url, prov.model

    meta = Meta(
        model=model, provider=prov.name, method="B1", prompt_id="b1_v1",
        prompt_sha256=hashlib.sha256(
            (extract_prompt + "\n---\n" + describe_prompt).encode("utf-8")).hexdigest(),
        temperature=temperature, max_tokens=extract_max_tokens + describe_max_tokens,
        created_at_utc=datetime.now(timezone.utc),
    )
    ctx = {"image_id": image_id, "image_sha256": sha, "meta": meta}
    total_latency, prompt_tokens, completion_tokens = 0.0, 0, 0

    def finish_meta(finish_reason):
        meta.latency_seconds = round(total_latency, 3)
        meta.finish_reason = finish_reason
        meta.usage = Usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

    try:
        payload = build_chat_payload(model, extract_prompt, str(path), temperature,
                                     extract_max_tokens, provider=prov.name,
                                     reasoning_effort=prov.reasoning_effort)
        text1, fin1, usage1, lat1 = _chat_once(payload, api_key, base_url, timeout, post)
        total_latency += lat1
        prompt_tokens += usage1.get("prompt_tokens") or 0
        completion_tokens += usage1.get("completion_tokens") or 0
        if trace is not None:
            trace["stage1_text"], trace["stage1_finish"] = text1, fin1

        try:
            extracted = parse_extraction(text1)
        except Exception:
            finish_meta(fin1)
            return _error("invalid_output", "Bước trích xuất không trả về JSON hợp lệ.", True, **ctx)

        if extracted["status"] == "unreadable":
            finish_meta(fin1)
            reason = extracted["uncertainties"][0] if extracted["uncertainties"] else (
                "Ảnh quá mờ hoặc thiếu thông tin nên chưa thể đọc nhãn và số liệu.")
            return DescriptionResult(
                image_id=image_id, image_sha256=sha, image_type=extracted["image_type"],
                status="unreadable", summary_vi=reason,
                uncertainties=extracted["uncertainties"], meta=meta)
        if not extracted["facts"]:
            finish_meta(fin1)
            return _error("invalid_output", "Không trích xuất được dữ kiện nào.", True, **ctx)

        facts_json = _json.dumps(
            [f.model_dump(exclude={"evidence"}) for f in extracted["facts"]],
            ensure_ascii=False)
        payload = build_chat_payload(model, describe_prompt + "\n" + facts_json, None,
                                     temperature, describe_max_tokens, provider=prov.name,
                                     reasoning_effort=prov.reasoning_effort)
        text2, fin2, usage2, lat2 = _chat_once(payload, api_key, base_url, timeout, post)
        total_latency += lat2
        prompt_tokens += usage2.get("prompt_tokens") or 0
        completion_tokens += usage2.get("completion_tokens") or 0
        if trace is not None:
            trace["stage2_text"], trace["stage2_finish"] = text2, fin2
    except _StageFailure as failure:
        finish_meta(None)
        return _error(failure.code, failure.message, failure.retryable,
                      http_status=failure.http_status, **ctx)

    finish_meta(fin2)
    text2 = strip_markdown(text2)
    truncated = fin1 == "length" or fin2 == "length"
    uncertainties = list(extracted["uncertainties"])
    if truncated:
        uncertainties.append("Một bước bị cắt do giới hạn độ dài; dữ kiện có thể chưa đầy đủ.")
    return DescriptionResult(
        image_id=image_id, image_sha256=sha, image_type=extracted["image_type"],
        status="partial" if truncated else "ok",
        summary_vi=_extract_summary(text2), facts=extracted["facts"],
        interpretation_vi=text2, uncertainties=uncertainties,
        question_answering_ready=not truncated, meta=meta)

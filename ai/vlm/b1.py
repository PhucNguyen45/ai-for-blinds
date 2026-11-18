"""Phương pháp B1: hai bước. (1) ảnh -> JSON dữ kiện có cấu trúc; (2) JSON -> diễn giải tiếng Việt (không gửi lại ảnh).

Bước hai chỉ thấy dữ kiện đã trích xuất nên lỗi ở bước một lan sang bước hai (đã quan sát với model 4B).
Nếu JSON của bước một hỏng, `parse_extraction` cố khôi phục các bộ ba chủ thể/quan hệ/đối tượng.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values

from contract.models import DescriptionResult, Fact, Meta, Usage
from vlm.client import build_chat_payload, post_chat_completion
from vlm.common import (
    AI_ROOT, MAX_IMAGE_BYTES, SUPPORTED_SUFFIXES, PostFn, StageFailure, chat_once, chat_vi, error_result, extract_summary,
    load_prompt, strip_markdown,
)
from vlm.providers import ConfigError, resolve_provider

_IMAGE_TYPES = {"bar_chart", "line_chart", "pie_chart", "table", "flow_diagram",
                "cycle_diagram", "geometry", "map", "text", "other"}


_TRIPLE_RE = re.compile(
    r'"subject"\s*:\s*"(.*?)"\s*,\s*"predicate"\s*:\s*"(.*?)"\s*,\s*"object"\s*:\s*"(.*?)"'
    r'\s*(?=,\s*"evidence"|\})', re.S)


def _salvage(cleaned: str) -> dict:
    """Khôi phục facts khi JSON hỏng (thường do dấu nháy kép không escape trong 'evidence')."""
    triples = _TRIPLE_RE.findall(cleaned)
    if not triples:
        raise ValueError("JSON hỏng và không khôi phục được dữ kiện")
    facts = [{"subject": a, "predicate": b, "object": c} for a, b, c in triples]
    kind = re.search(r'"image_type"\s*:\s*"([a-z_]+)"', cleaned)
    unread = re.search(r'"status"\s*:\s*"unreadable"', cleaned)
    return {"image_type": kind.group(1) if kind else "other",
            "status": "unreadable" if unread else "ok", "facts": facts,
            "uncertainties": [], "_salvaged": True}


def parse_extraction(text: str) -> dict:
    """Parse JSON của bước trích xuất; chấp nhận khung ```json và văn bản thừa quanh JSON.

    Nếu JSON hỏng, thử khôi phục các bộ ba chủ thể/quan hệ/đối tượng (cờ `salvaged` = True)."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("không tìm thấy đối tượng JSON")
    try:
        data = json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError:
        data = _salvage(cleaned[start:end + 1])
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
            "uncertainties": uncertainties, "salvaged": bool(data.get("_salvaged"))}


def describe_image_b1(
    image_path: str | Path,
    *,
    image_id: str | None = None,
    model: str | None = None,
    provider: str | None = None,
    temperature: float = 0.2,
    extract_max_tokens: int = 1500,
    describe_max_tokens: int = 800,
    timeout: float | None = None,
    post: PostFn = post_chat_completion,
    env: dict | None = None,
    trace: dict | None = None,
) -> DescriptionResult:
    """B1: (1) ảnh -> JSON dữ kiện; (2) JSON -> diễn giải tiếng Việt (không gửi lại ảnh).

    `trace` (tùy chọn) nhận văn bản thô của từng bước để lưu bằng chứng thực nghiệm.
    """
    path = Path(image_path).expanduser()
    if path.suffix.lower() not in SUPPORTED_SUFFIXES or not path.is_file():
        return error_result("invalid_image", "Ảnh không tồn tại hoặc định dạng không được hỗ trợ.",
                      False, image_id=image_id)
    data = path.read_bytes()
    if not data or len(data) > MAX_IMAGE_BYTES:
        return error_result("invalid_image", "Ảnh rỗng hoặc vượt quá 10 MB.", False, image_id=image_id)
    sha = hashlib.sha256(data).hexdigest()

    try:
        extract_prompt = load_prompt("b1_extract_v1")
        describe_prompt = load_prompt("b1_describe_v1")
    except ValueError as exc:
        return error_result("config_error", str(exc), False, image_id=image_id, image_sha256=sha)

    config = env if env is not None else {**dotenv_values(AI_ROOT / ".env"), **os.environ}
    try:
        prov = resolve_provider(config, provider, model)
    except ConfigError as exc:
        return error_result("config_error", str(exc), False, image_id=image_id, image_sha256=sha)
    api_key, base_url, model = prov.api_key, prov.base_url, prov.model
    timeout = timeout or max(prov.timeout, 90.0)

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
        text1, fin1, usage1, lat1 = chat_once(payload, api_key, base_url, timeout, post, prov.name)
        total_latency += lat1
        prompt_tokens += usage1.get("prompt_tokens") or 0
        completion_tokens += usage1.get("completion_tokens") or 0
        if trace is not None:
            trace["stage1_text"], trace["stage1_finish"] = text1, fin1

        try:
            extracted = parse_extraction(text1)
        except Exception:
            finish_meta(fin1)
            return error_result("invalid_output", "Bước trích xuất không trả về JSON hợp lệ.", True, **ctx)

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
            return error_result("invalid_output", "Không trích xuất được dữ kiện nào.", True, **ctx)

        facts_json = json.dumps(
            [f.model_dump(exclude={"evidence"}) for f in extracted["facts"]],
            ensure_ascii=False)
        payload = build_chat_payload(model, describe_prompt + "\n" + facts_json, None,
                                     temperature, describe_max_tokens, provider=prov.name,
                                     reasoning_effort=prov.reasoning_effort)
        text2, fin2, usage2, lat2, _ = chat_vi(payload, api_key, base_url, timeout, post, prov.name)
        total_latency += lat2
        prompt_tokens += usage2.get("prompt_tokens") or 0
        completion_tokens += usage2.get("completion_tokens") or 0
        if trace is not None:
            trace["stage2_text"], trace["stage2_finish"] = text2, fin2
    except StageFailure as failure:
        finish_meta(None)
        return error_result(failure.code, failure.message, failure.retryable,
                      http_status=failure.http_status, **ctx)

    finish_meta(fin2)
    text2 = strip_markdown(text2)
    truncated = fin1 == "length" or fin2 == "length"
    uncertainties = list(extracted["uncertainties"])
    if extracted.get("salvaged"):
        uncertainties.append("Bước trích xuất trả JSON lỗi; dữ kiện được khôi phục (bỏ trường evidence).")
    if truncated:
        uncertainties.append("Một bước bị cắt do giới hạn độ dài; dữ kiện có thể chưa đầy đủ.")
    return DescriptionResult(
        image_id=image_id, image_sha256=sha, image_type=extracted["image_type"],
        status="partial" if truncated else "ok",
        summary_vi=extract_summary(text2), facts=extracted["facts"],
        interpretation_vi=text2, uncertainties=uncertainties,
        question_answering_ready=not truncated, meta=meta)

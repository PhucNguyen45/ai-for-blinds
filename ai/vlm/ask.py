"""Hỏi đáp theo hình: câu hỏi của học sinh về trang đã chụp -> AnswerResult.

Ngữ cảnh gửi cho VLM theo thứ tự: prompt hệ thống `ask_v1`; ảnh cùng lời mô tả đã đọc cho học sinh; các lượt
hỏi đáp trước (nếu có); câu hỏi mới. Định dạng này trùng với dữ liệu huấn luyện (`finetune/export_sft.py`).

Như `describe_image`, hàm KHÔNG ném ngoại lệ vì lỗi vận hành: trả `status="error"` kèm `error`.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from dotenv import dotenv_values

from contract.models import AnswerResult, ErrorInfo, Meta, Usage
from vlm.calc import safe_eval, spoken
from vlm.client import build_messages_payload, build_user_content, post_chat_completion
from vlm.common import (
    AI_ROOT, MAX_IMAGE_BYTES, SUPPORTED_SUFFIXES, PostFn, StageFailure, chat_vi, load_prompt, strip_markdown,
)
from vlm.providers import ConfigError, resolve_provider

PROMPT_ID = "ask_v1"
CALC_PROMPT_ID = "ask_calc_v1"  # model viết biểu thức, mã tính kết quả (xem vlm/calc.py)
MAX_QUESTION_CHARS = 500
MAX_HISTORY_TURNS = 6  # giữ ngữ cảnh gọn để không tràn context của model nhỏ
ACK = "Mình đã xem trang này. Bạn muốn hỏi gì?"  # lượt đáp mở đầu, giống dữ liệu huấn luyện


def _error(code, message, retryable, *, image_id=None, meta=None, http_status=None) -> AnswerResult:
    return AnswerResult(image_id=image_id, status="error", meta=meta,
                        error=ErrorInfo(code=code, message=message, retryable=retryable,
                                        http_status=http_status))


def build_messages(system: str, image_path, description: str, history: Sequence[tuple[str, str]],
                   question: str) -> list[dict]:
    intro = "Đây là trang học sinh vừa chụp."
    if description.strip():
        intro += " Bạn đã mô tả cho học sinh như sau:\n" + description.strip()
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": build_user_content(intro, str(image_path))},
                {"role": "assistant", "content": ACK}]
    for q, a in list(history)[-MAX_HISTORY_TURNS:]:
        messages += [{"role": "user", "content": q}, {"role": "assistant", "content": a}]
    messages.append({"role": "user", "content": question})
    return messages


def ask_about_image(
    image_path: str | Path,
    question: str,
    *,
    description: str = "",
    history: Sequence[tuple[str, str]] = (),
    image_id: str | None = None,
    model: str | None = None,
    provider: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 400,
    timeout: float | None = None,
    post: PostFn = post_chat_completion,
    env: dict | None = None,
    calc: bool = True,
) -> AnswerResult:
    """Trả lời một câu hỏi về ảnh. `history` là danh sách (câu hỏi, câu trả lời) của các lượt trước.

    `calc=True`: model viết biểu thức cho câu hỏi tính toán và mã tính kết quả (xem `vlm/calc.py`); nếu model
    không trả JSON hợp lệ thì quay lại cách trả lời trực tiếp bằng prompt `ask_v1`."""
    question = unicodedata.normalize("NFC", (question or "").strip())
    if not question:
        return _error("invalid_input", "Câu hỏi đang trống.", False, image_id=image_id)
    if len(question) > MAX_QUESTION_CHARS:
        return _error("invalid_input", f"Câu hỏi dài quá {MAX_QUESTION_CHARS} ký tự.", False, image_id=image_id)
    path = Path(image_path).expanduser()
    if path.suffix.lower() not in SUPPORTED_SUFFIXES or not path.is_file():
        return _error("invalid_image", "Ảnh không tồn tại hoặc định dạng không được hỗ trợ.", False,
                      image_id=image_id)
    if not path.stat().st_size or path.stat().st_size > MAX_IMAGE_BYTES:
        return _error("invalid_image", "Ảnh rỗng hoặc vượt quá 10 MB.", False, image_id=image_id)

    config = env if env is not None else {**dotenv_values(AI_ROOT / ".env"), **os.environ}
    try:
        system = load_prompt(CALC_PROMPT_ID if calc else PROMPT_ID)
        plain_system = load_prompt(PROMPT_ID)
        prov = resolve_provider(config, provider, model)
    except (ValueError, ConfigError) as exc:
        return _error("config_error", str(exc), False, image_id=image_id)
    meta = Meta(model=prov.model, provider=prov.name, prompt_id=CALC_PROMPT_ID if calc else PROMPT_ID,
                prompt_sha256=hashlib.sha256(system.encode("utf-8")).hexdigest(),
                temperature=temperature, max_tokens=max_tokens, created_at_utc=datetime.now(timezone.utc))

    def call(sys_prompt):
        payload = build_messages_payload(
            prov.model, build_messages(sys_prompt, path, description, history, question), temperature, max_tokens,
            prov.name, prov.reasoning_effort)
        return chat_vi(payload, prov.api_key, prov.base_url, timeout or prov.timeout, post, prov.name)

    try:
        text, finish, usage, latency, _ = call(system)
        if calc:
            answer = _answer_from_calc_json(text)
            if answer is None:  # JSON hỏng hoặc biểu thức không hợp lệ: trả lời trực tiếp
                text, finish, usage2, latency2, _ = call(plain_system)
                usage = {k: (usage.get(k) or 0) + (usage2.get(k) or 0) for k in ("prompt_tokens", "completion_tokens")}
                latency += latency2
                meta.prompt_id = f"{CALC_PROMPT_ID}+{PROMPT_ID}"
            else:
                text = answer
    except StageFailure as exc:
        return _error(exc.code, exc.message, exc.retryable, image_id=image_id, meta=meta,
                      http_status=exc.http_status)
    meta.finish_reason, meta.latency_seconds = finish, round(latency, 3)
    meta.usage = Usage(prompt_tokens=usage.get("prompt_tokens"), completion_tokens=usage.get("completion_tokens"))
    answer = re.sub(r"\s+", " ", strip_markdown(unicodedata.normalize("NFC", text))).strip()
    if not answer:
        return _error("empty_response", "Mô hình không trả về nội dung.", True, image_id=image_id, meta=meta)
    return AnswerResult(image_id=image_id, status="partial" if finish == "length" else "ok",
                        answer_vi=answer, meta=meta)


def _answer_from_calc_json(text: str) -> str | None:
    """Câu trả lời từ JSON của `ask_calc_v1`; None nếu không dùng được (để quay lại trả lời trực tiếp)."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start:end + 1])
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    if data.get("can_tinh") is True:
        value = safe_eval(str(data.get("bieu_thuc", "")))
        template = str(data.get("tra_loi_mau", ""))
        if value is None or template.count("{kq}") != 1:
            return None
        return template.replace("{kq}", spoken(value))
    answer = data.get("tra_loi")
    return answer.strip() if isinstance(answer, str) and answer.strip() else None

"""Phần dùng chung của lớp VLM: hằng số, nạp prompt, làm sạch văn bản, gọi một lượt chat.

Mọi lỗi vận hành của một lượt gọi được gói thành `StageFailure` để các hàm cấp cao (mô tả, B1, hỏi đáp) chuyển thành
kết quả `status="error"` theo hợp đồng, không ném ngoại lệ ra backend.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Callable

import httpx

from contract.models import DescriptionResult, ErrorCode, ErrorInfo

AI_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = AI_ROOT / "prompts"
SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
PROMPT_ID_RE = re.compile(r"^[a-z0-9_]+$")
# Prompt có hướng dẫn "ảnh không đọc được" yêu cầu model mở đầu bằng cụm này (ví dụ prompt b0g_v1).
UNREADABLE_RE = re.compile(r"^\W*kh[oô]ng\s+đ[oọ]c\s+đ[uư][oơợ]c\s*[:\-–—]?\s*", re.I)

PostFn = Callable[..., httpx.Response]


def load_prompt(prompt_id: str) -> str:
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


def conn_message(provider_name: str) -> str:
    if provider_name == "lmstudio":
        return ("Không kết nối được LM Studio: kiểm tra server đang chạy, đã bật 'Serve on Local "
                "Network' và tường lửa Windows cho phép cổng 1234.")
    return "Lỗi kết nối tới dịch vụ mô hình."


def http_message(status: int) -> str:
    if status in (400, 404):
        return (f"Dịch vụ mô hình trả về HTTP {status}: kiểm tra tên model và tham số "
                "(model có thể không tồn tại hoặc không còn khả dụng).")
    return f"Dịch vụ mô hình trả về HTTP {status}."


class StageFailure(Exception):
    def __init__(self, code: ErrorCode, message: str, retryable: bool, http_status=None):
        self.code, self.message = code, message
        self.retryable, self.http_status = retryable, http_status


def chat_once(payload, api_key, base_url, timeout, post, provider_name=""):
    """Gọi một lần; trả (text, finish_reason, usage_dict, latency) hoặc ném StageFailure."""
    start = time.perf_counter()
    try:
        response = post(payload, api_key, base_url, timeout=timeout)
    except httpx.TimeoutException:
        raise StageFailure("timeout", "Hết thời gian chờ mô hình.", True)
    except httpx.HTTPError:
        raise StageFailure("http_error", conn_message(provider_name), True)
    latency = time.perf_counter() - start
    if response.status_code != 200:
        retryable = response.status_code in (408, 429) or response.status_code >= 500
        raise StageFailure("http_error", http_message(response.status_code),
                            retryable, response.status_code)
    try:
        body = response.json()
        choice = body["choices"][0]
        text = (choice["message"].get("content") or "").strip()
    except (ValueError, KeyError, IndexError, TypeError):
        raise StageFailure("empty_response", "Phản hồi của mô hình không đúng định dạng.", True)
    if not text:
        raise StageFailure("empty_response", "Mô hình không trả về nội dung.", True)
    return text, choice.get("finish_reason"), body.get("usage") or {}, latency


# Ký tự của hệ chữ không dùng trong tiếng Việt (Hán, Nhật, Hàn, Kirin, Ả Rập): đã gặp chữ Hán lẫn vào câu trả lời
FOREIGN_SCRIPT_RE = re.compile(r"[\u0400-\u04ff\u0600-\u06ff\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]")


def has_foreign_script(text: str) -> bool:
    return bool(FOREIGN_SCRIPT_RE.search(text))


def chat_vi(payload, api_key, base_url, timeout, post, provider_name=""):
    """Như `chat_once` nhưng bảo đảm đầu ra không lẫn chữ ngoài tiếng Việt: nếu có thì gọi lại một lần, nếu vẫn có
    thì loại các ký tự đó. Trả (text, finish_reason, usage, latency, đã_loại_ký_tự)."""
    text, finish, usage, latency = chat_once(payload, api_key, base_url, timeout, post, provider_name)
    if not has_foreign_script(text):
        return text, finish, usage, latency, False
    text2, finish2, usage2, latency2 = chat_once(payload, api_key, base_url, timeout, post, provider_name)
    usage = {k: (usage.get(k) or 0) + (usage2.get(k) or 0) for k in ("prompt_tokens", "completion_tokens")}
    cleaned = has_foreign_script(text2)
    if cleaned:
        text2 = re.sub(r" {2,}", " ", FOREIGN_SCRIPT_RE.sub("", text2)).strip() or text2
    return text2, finish2, usage, latency + latency2, cleaned


def error_result(code: ErrorCode, message: str, retryable: bool, *, image_id=None,
           image_sha256=None, meta=None, http_status=None) -> DescriptionResult:
    return DescriptionResult(
        image_id=image_id, image_sha256=image_sha256, status="error", meta=meta,
        error=ErrorInfo(code=code, message=message, retryable=retryable,
                        http_status=http_status),
    )


def extract_summary(text: str) -> str:
    """Lấy nội dung mục '1. Chủ đề' của B0; nếu không có, lấy câu đầu tiên."""
    match = re.search(r"(?m)^\s*1\.\s*[^:\n]{0,20}:\s*(.+?)(?=^\s*2\.|\Z)", text, re.S)
    summary = (match.group(1) if match else text).strip()
    summary = re.sub(r"^\s*\d+\.\s*", "", summary)
    first = re.split(r"(?<=[.!?])\s", summary, maxsplit=1)[0]
    return re.sub(r"\s+", " ", first).strip()

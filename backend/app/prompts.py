"""Nạp prompt từ thư mục prompts/<phiên bản>/ (Toàn giữ nội dung).

Cấu trúc:
  prompts/v1/system.md   – quy tắc chung + định dạng đầu ra JSON
  prompts/v1/<loại>.md   – hướng dẫn riêng cho auto, text, map, chart, table, figure, mixed
  prompts/v1/ask.md      – hỏi đáp nhiều lượt
"""
import base64
from typing import Dict, List

from .config import settings


class PromptNotFound(Exception):
    pass


def load_prompt(name: str, version: str = "") -> str:
    version = version or settings.prompt_version
    path = settings.prompts_dir / version / f"{name}.md"
    if not path.is_file():
        raise PromptNotFound(f"Không tìm thấy prompt {path}")
    return path.read_text(encoding="utf-8").strip()


def _image_part(jpeg: bytes) -> Dict:
    b64 = base64.b64encode(jpeg).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}


def describe_messages(jpeg: bytes, page_type: str) -> List[Dict]:
    system = load_prompt("system") + "\n\n" + load_prompt(page_type)
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": [
                _image_part(jpeg),
                {"type": "text", "text": "Hãy mô tả trang này theo đúng hướng dẫn và trả về JSON."},
            ],
        },
    ]


def ask_messages(jpeg: bytes, description: str, question: str, history: List[Dict]) -> List[Dict]:
    messages: List[Dict] = [
        {"role": "system", "content": load_prompt("ask")},
        {
            "role": "user",
            "content": [
                _image_part(jpeg),
                {"type": "text", "text": f"Đây là trang học sinh vừa chụp. Bạn đã mô tả cho học sinh như sau:\n{description}"},
            ],
        },
        {"role": "assistant", "content": "Mình đã xem trang này. Bạn muốn hỏi gì?"},
    ]
    for turn in history[-6:]:
        messages.append({"role": "user", "content": turn["question"]})
        messages.append({"role": "assistant", "content": turn["answer"]})
    messages.append({"role": "user", "content": question})
    return messages

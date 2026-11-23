from __future__ import annotations

import base64
import mimetypes
import httpx
from pathlib import Path


def file_to_data_url(file_path: Path) -> str:
    """Chuyển file ảnh thành data URL Base64."""
    mime_type, _ = mimetypes.guess_type(file_path.name)

    if mime_type is None:
        mime_type = "application/octet-stream"

    data = base64.b64encode(
        file_path.read_bytes()
    ).decode("utf-8")

    return f"data:{mime_type};base64,{data}"


def build_user_content(
    prompt: str,
    image_path: str | None,
) -> list[dict]:
    """Dựng nội dung (văn bản + ảnh) của một tin nhắn người dùng gửi cho VLM."""
    content: list[dict] = [
        {"type": "text", "text": prompt}
    ]

    if image_path:
        path = Path(image_path).expanduser().resolve()

        if not path.is_file():
            raise FileNotFoundError(
                f"Image not found: {path}"
            )

        content.append({
            "type": "image_url",
            "image_url": {
                "url": file_to_data_url(path)
            },
        })

    return content


def build_messages_payload(
    model: str,
    messages: list[dict],
    temperature: float = 0.2,
    max_tokens: int = 400,
    provider: str = "openrouter",
    reasoning_effort: str | None = None,
) -> dict:
    """Dựng payload chat/completions (định dạng OpenAI) cho nhà cung cấp đã chọn."""
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if provider == "lmstudio":
        # LM Studio: chỉ gửi reasoning_effort khi được đặt (model có chế độ suy nghĩ như Gemma 4 cần "none").
        if reasoning_effort:
            payload["reasoning_effort"] = reasoning_effort
    elif provider == "google":
        # Gemini API (tương thích OpenAI) không nhận trường "reasoning" của OpenRouter.
        if reasoning_effort:
            payload["reasoning_effort"] = reasoning_effort
    else:
        payload["reasoning"] = {"enabled": False}
    return payload


def build_chat_payload(
    model: str,
    prompt: str,
    image_path: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 400,
    provider: str = "openrouter",
    reasoning_effort: str | None = None,
) -> dict:
    """Payload một lượt: một tin nhắn người dùng gồm prompt và (tùy chọn) một ảnh."""
    messages = [{"role": "user", "content": build_user_content(prompt, image_path)}]
    return build_messages_payload(model, messages, temperature, max_tokens, provider, reasoning_effort)


def post_chat_completion(
    payload: dict,
    api_key: str,
    base_url: str,
    timeout: float = 60.0,
) -> httpx.Response:
    """Gửi một request chat/completions tới nhà cung cấp tương thích OpenAI."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    if "openrouter.ai" in base_url:  # tiêu đề định danh ứng dụng chỉ dành cho OpenRouter
        headers["HTTP-Referer"] = "https://github.com/PhucNguyen45/ai-for-blinds"
        headers["X-Title"] = "AI for Blinds Research"

    url = f"{base_url.rstrip('/')}/chat/completions"

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            url,
            headers=headers,
            json=payload,
        )

    return response

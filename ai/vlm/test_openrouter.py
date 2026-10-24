from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv


def load_env() -> None:
    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"
    load_dotenv(env_path)


def file_to_data_url(file_path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(file_path.name)
    if mime_type is None:
        mime_type = "application/octet-stream"

    data = base64.b64encode(file_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{data}"


def build_user_content(prompt: str, image_path: str | None) -> list[dict]:
    content: list[dict] = [{"type": "text", "text": prompt}]

    if image_path:
        path = Path(image_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")

        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": file_to_data_url(path)
                },
            }
        )

    return content


def main() -> None:
    parser = argparse.ArgumentParser(description="Test OpenRouter VLM connection")
    parser.add_argument("--prompt", default="Trả lời đúng một từ: OK")
    parser.add_argument("--image", default=None)
    parser.add_argument("--max-tokens", type=int, default=400)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument(
        "--save-json",
        default="evaluation/last_response.json",
        help="Nơi lưu raw JSON response",
    )
    args = parser.parse_args()

    load_env()

    api_key = os.environ["OPENROUTER_API_KEY"]
    base_url = os.environ["OPENROUTER_BASE_URL"].rstrip("/")
    model = os.environ["OPENROUTER_MODEL"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/PhucNguyen45/ai-for-blinds",
        "X-Title": "AI for Blinds Research",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": build_user_content(args.prompt, args.image),
            }
        ],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "reasoning": {"enabled": False},
    }

    start = time.perf_counter()

    with httpx.Client(timeout=60) as client:
        response = client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
        )

    elapsed = time.perf_counter() - start

    print("HTTP status:", response.status_code)
    print("Latency (s):", f"{elapsed:.2f}")

    if response.status_code != 200:
        print("Response body:")
        print(response.text)
        raise SystemExit(1)

    data = response.json()

    save_path = Path(args.save_json)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    choice = data["choices"][0]
    answer = choice["message"]["content"]
    finish_reason = choice.get("finish_reason")
    usage = data.get("usage", {})

    print("\n=== Model ===")
    print(model)

    print("\n=== Finish reason ===")
    print(finish_reason)

    print("\n=== Usage ===")
    print(json.dumps(usage, ensure_ascii=False, indent=2))

    print("\n=== Answer ===")
    print(answer)

    print(f"\nRaw JSON saved to: {save_path}")


if __name__ == "__main__":
    main()

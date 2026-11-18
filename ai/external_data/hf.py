"""Truy cập công khai Hugging Face (API Hub và datasets-server), lịch sự và chỉ đọc.

Không dùng token, không vượt qua cổng truy cập: bộ dữ liệu bị khóa (gated) hoặc riêng tư được ghi nhận là "không truy cập được".
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

HUB = "https://huggingface.co"
SERVER = "https://datasets-server.huggingface.co"
HEADERS = {"User-Agent": "research-client/0.1"}
ROOT = Path(__file__).resolve().parents[2] / "data" / "external"
DELAY = 1.0
_last = [0.0]


def _get(url, *, params=None, timeout=40, stream=False):
    wait = DELAY - (time.monotonic() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.monotonic()
    return httpx.get(url, params=params, headers=HEADERS, timeout=timeout, follow_redirects=True)


def api_dataset(repo_id):
    """(trạng thái http, JSON) của /api/datasets/<id>?blobs=true."""
    r = _get(f"{HUB}/api/datasets/{repo_id}", params={"blobs": "true"})
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


def card_text(repo_id):
    r = _get(f"{HUB}/datasets/{repo_id}/raw/main/README.md")
    return r.text if r.status_code == 200 else None


def server_json(endpoint, **params):
    r = _get(f"{SERVER}/{endpoint}", params=params)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


def search(term, limit=20):
    r = _get(f"{HUB}/api/datasets", params={"search": term, "limit": limit, "full": "false"})
    return r.json() if r.status_code == 200 else []


def dump(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

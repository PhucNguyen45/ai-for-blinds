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

# Nguồn duy nhất cho việc xếp bộ dữ liệu vào mục (thư mục thật trong data/external/). Tên thư mục = repo_id đổi "/" thành "__".
GROUPS = {
    "1_hoc_tap": ["ViSGKCap", "D-Truong__ViEduVQA", "anvo25__vmmu"],
    "2_cuoc_song": ["uitnlp__OpenViVQA-dataset", "Ouyangxuelili__vlsp2023-vqa-dataset", "huyhuy123__ViOCRVQA", "5CD-AI__Viet-Table-Markdown"],
    "3_hon_hop": ["VLAI-AIVN__ViInfographicVQA"],
}
DELAY = 1.0
_last = [0.0]


def group_of(dir_name: str) -> str | None:
    """Mục của một thư mục bộ dữ liệu theo GROUPS; None nếu chưa được phân loại."""
    return next((g for g, names in GROUPS.items() if dir_name in names), None)


def dir_name_of(repo_id: str) -> str:
    """Tên thư mục của một bộ: ViSGKCap giữ tên ngắn có sẵn, các bộ khác là repo_id với "/" thành "__"."""
    return "ViSGKCap" if repo_id == "bbdontcry/ViSGKCap" else repo_id.replace("/", "__")


def dataset_dir(dir_name: str, *, must_exist: bool = True) -> Path:
    """Đường dẫn thư mục bộ dữ liệu: tìm trong từng mục rồi ở ROOT (chịu được bố cục cũ). Nếu chưa có và `must_exist` sai
    thì trả về nơi nó NÊN nằm (mục theo GROUPS, hoặc ROOT nếu chưa phân loại) để bộ tải ghi vào đúng chỗ."""
    for sub in (*GROUPS, ""):
        p = ROOT / sub / dir_name if sub else ROOT / dir_name
        if p.is_dir() and not p.is_symlink():
            return p
    if must_exist:
        raise FileNotFoundError(f"Không thấy thư mục bộ dữ liệu: {dir_name} (đã tìm trong {', '.join(GROUPS)} và {ROOT})")
    g = group_of(dir_name)
    return ROOT / g / dir_name if g else ROOT / dir_name


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

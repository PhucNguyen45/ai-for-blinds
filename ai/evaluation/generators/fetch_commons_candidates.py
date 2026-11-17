#!/usr/bin/env python3
"""Tải ảnh ứng viên từ Wikimedia Commons kèm metadata nguồn gốc/giấy phép.

Chỉ nhận giấy phép tự do (CC0, Public domain, CC BY, CC BY-SA). Ảnh được lưu
ở data/benchmark/candidates/ (CHƯA vào manifest chính) cùng candidates.json.
Một ảnh chỉ được đưa vào benchmark sau khi có ground truth do người kiểm chứng.

Chạy từ thư mục ai/:
    uv run python evaluation/generators/fetch_commons_candidates.py
"""

import hashlib
import io
import json
import re
import time
from pathlib import Path

import httpx
from PIL import Image

BENCH = Path(__file__).resolve().parents[3] / "data" / "benchmark"
OUT = BENCH / "candidates"
API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "ai-for-blinds-research/0.1 (educational research dataset)"}
ALLOWED = re.compile(r"^(CC0|Public domain|PD|CC BY(-SA)? [34]\.0)", re.I)
THUMB_WIDTH = 1400
PER_QUERY = 4

# (nhóm, loại dự kiến, truy vấn)
QUERIES = [
    ("chart", "bar_chart", "bar chart statistics"),
    ("chart", "line_chart", "line chart statistics graph"),
    ("chart", "pie_chart", "pie chart"),
    ("figure", "cycle_diagram", "water cycle diagram"),
    ("figure", "cycle_diagram", "life cycle diagram butterfly"),
    ("figure", "flow_diagram", "photosynthesis diagram"),
    ("figure", "flow_diagram", "food web diagram"),
    ("figure", "diagram", "human digestive system diagram labeled"),
    ("figure", "geometry", "Pythagorean theorem diagram"),
    ("figure", "diagram", "electric circuit diagram simple"),
    ("map", "map", "map of Vietnam"),
    ("map", "map", "map of Southeast Asia"),
]


def search(client, query):
    params = {
        "action": "query", "generator": "search",
        "gsrsearch": f"filetype:bitmap {query}", "gsrnamespace": 6,
        "gsrlimit": 12, "prop": "imageinfo",
        "iiprop": "url|extmetadata|size|mime", "iiurlwidth": THUMB_WIDTH,
        "iiextmetadatafilter": "LicenseShortName|Artist|Credit|ImageDescription",
        "format": "json",
    }
    r = client.get(API, params=params)
    r.raise_for_status()
    pages = r.json().get("query", {}).get("pages", {})
    return sorted(pages.values(), key=lambda p: p.get("index", 0))


def download(client, url):
    """Tải ảnh, kiểm tra HTTP và nội dung là ảnh thật; thử lại có chờ khi bị giới hạn."""
    for attempt in range(1, 5):
        r = client.get(url)
        if r.status_code == 200:
            try:
                Image.open(io.BytesIO(r.content)).verify()
                return r.content
            except Exception:
                pass
        time.sleep(8 * attempt)
    return None


def clean(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def main():
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    index_path = OUT / "candidates.json"
    existing = (json.loads(index_path.read_text(encoding="utf-8"))
                if index_path.exists() else {"items": []})
    seen = {c["commons_title"] for c in existing["items"]}
    items = existing["items"]

    with httpx.Client(headers=HEADERS, timeout=60, follow_redirects=True) as client:
        for group, category, query in QUERIES:
            taken = 0
            for page in search(client, query):
                if taken >= PER_QUERY:
                    break
                info = page["imageinfo"][0]
                meta = info["extmetadata"]
                lic = clean(meta.get("LicenseShortName", {}).get("value"))
                title = page["title"]
                if (title in seen or not ALLOWED.match(lic)
                        or info["mime"] not in ("image/png", "image/jpeg")
                        or info["width"] < 700 or "thumburl" not in info):
                    continue
                data = download(client, info["thumburl"])
                time.sleep(3)  # lịch sự với máy chủ
                if data is None:
                    print("  bỏ qua (không tải được):", title)
                    continue
                n = len(items) + 1
                ext = "png" if info["mime"] == "image/png" else "jpg"
                path = OUT / "images" / f"cand_{n:03d}.{ext}"
                path.write_bytes(data)
                items.append({
                    "candidate_id": f"cand_{n:03d}", "group": group,
                    "category_guess": category, "query": query,
                    "image": f"candidates/images/{path.name}",
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "commons_title": title,
                    "source_page": info["descriptionurl"],
                    "original_size": [info["width"], info["height"]],
                    "downloaded_width": THUMB_WIDTH,
                    "license": lic,
                    "author": clean(meta.get("Artist", {}).get("value")),
                    "description": clean(meta.get("ImageDescription", {}).get("value"))[:300],
                    "status": "candidate_unreviewed",
                })
                seen.add(title)
                taken += 1
            print(f"{query!r}: +{taken}")

    index_path.write_text(json.dumps({"items": items}, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    print("Tổng ứng viên:", len(items))


if __name__ == "__main__":
    main()

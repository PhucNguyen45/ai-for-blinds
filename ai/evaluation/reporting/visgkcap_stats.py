#!/usr/bin/env python3
"""Thống kê bộ ViSGKCap đã tải về máy (data/external/ViSGKCap, không có trong repo).

Cần pyarrow, không nằm trong phụ thuộc của dự án; chạy bằng môi trường tạm:
  uv run --with pyarrow python evaluation/reporting/visgkcap_stats.py [--out báo_cáo.md]

Chỉ đọc các cột chữ (không nạp ảnh) và đo kích thước ảnh trên một mẫu nhỏ. Thống kê loại nội dung dựa trên từ khóa
trong chú thích ngắn: chỉ để ước lượng thô, chú thích do máy sinh chưa được kiểm chứng.
"""

import argparse
import io
import re
import statistics as st
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq
from PIL import Image

DATA = Path(__file__).resolve().parents[3] / "data" / "external" / "ViSGKCap" / "data"
KEYWORDS = {"biểu đồ": r"biểu đồ", "bảng": r"\bbảng\b", "bản đồ": r"bản đồ", "sơ đồ": r"sơ đồ",
            "hình học": r"hình (vuông|chữ nhật|tam giác|tròn)|góc|cạnh|chu vi|diện tích", "phép tính": r"phép (tính|cộng|trừ|nhân|chia)|đặt tính"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args()
    cols = ["id", "caption_short", "caption_detail", "metadata_type", "metadata_collection", "metadata_title",
            "metadata_grade", "metadata_subject", "metadata_publisher"]
    lines = ["# Thống kê ViSGKCap (cục bộ)", "", "Nguồn: huggingface.co/datasets/bbdontcry/ViSGKCap; không giấy phép khai báo; chỉ dùng nội bộ.", ""]
    all_rows = []
    for split in ("train", "validation", "test"):
        for f in sorted(DATA.glob(f"{split}-*.parquet")):
            t = pq.read_table(f, columns=cols).to_pylist()
            for r in t:
                r["split"] = split
            all_rows += t
    lines.append(f"Tổng số trang: {len(all_rows)} ({dict(Counter(r['split'] for r in all_rows))})")
    for key, title in (("metadata_type", "Loại"), ("metadata_collection", "Bộ sách"), ("metadata_grade", "Lớp"),
                       ("metadata_subject", "Môn"), ("metadata_publisher", "Nhà xuất bản")):
        lines += ["", f"**{title}:** " + ", ".join(f"{k} ({v})" for k, v in Counter(r[key] for r in all_rows).most_common(12))]
    book = Counter((r["metadata_title"]) for r in all_rows)
    lines += ["", f"**Số đầu sách khác nhau:** {len(book)}; nhiều nhất: " + ", ".join(f"{k} ({v})" for k, v in book.most_common(6))]
    lines += ["", "**Nội dung theo từ khóa trong chú thích ngắn (một trang có thể thuộc nhiều nhóm):**", "",
              "| Nhóm | Số trang | Tỉ lệ |", "|---|---|---|"]
    for name, rx in KEYWORDS.items():
        n = sum(bool(re.search(rx, r["caption_short"] or "", re.I)) for r in all_rows)
        lines.append(f"| {name} | {n} | {n / len(all_rows):.1%} |")
    cs = [len((r["caption_short"] or "").split()) for r in all_rows]
    cd = [len((r["caption_detail"] or "").split()) for r in all_rows]
    lines += ["", f"**Độ dài chú thích (từ):** ngắn trung vị {st.median(cs):.0f} (tối đa {max(cs)}); chi tiết trung vị {st.median(cd):.0f} (tối đa {max(cd)})."]
    t = pq.read_table(next(DATA.glob("test-*.parquet")), columns=["image"]).slice(0, 40).to_pylist()
    sizes = Counter()
    for r in t:
        with Image.open(io.BytesIO(r["image"]["bytes"])) as im:
            sizes[im.size] += 1
    lines += ["", "**Kích thước ảnh (40 trang đầu của tập kiểm tra):** " + ", ".join(f"{w}×{h} ({n})" for (w, h), n in sizes.most_common(6))]
    text = "\n".join(lines) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

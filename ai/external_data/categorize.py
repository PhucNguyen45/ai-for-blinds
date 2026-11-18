#!/usr/bin/env python3
"""Phân loại dữ liệu ngoài thành hai mục để theo dõi: HỌC TẬP (SGK, minh họa SGK, giáo dục) và CUỘC SỐNG (cảnh đời thường, tài liệu, sách, tin tức).

Không di chuyển dữ liệu: tạo "khung nhìn" bằng liên kết mềm trong data/external/1_hoc_tap/ và 2_cuoc_song/ (mọi đường dẫn của công cụ khác giữ nguyên),
bảng phân loại ở data/external/PHAN_LOAI.md và data/external/_reports/phan_loai*.csv, kèm bản tóm tắt không chứa dữ liệu ở ai/evaluation/reports/datasets/.

ViInfographicVQA có cột chủ đề nên được chia theo từng ảnh: chủ đề "Giáo dục - Khoa Học" vào HỌC TẬP, các chủ đề còn lại vào CUỘC SỐNG.
Căn cứ phân loại là nội dung đã xem (câu hỏi, ảnh mẫu, chủ đề) chứ không chỉ tên bộ; lý do ghi trong bảng.

  uv run --with pyarrow --with numpy python external_data/categorize.py
"""

import csv
import os
import sys
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from external_data import hf  # noqa: E402

ROOT = hf.ROOT
PUBLIC = Path(__file__).resolve().parents[1] / "evaluation" / "reports" / "datasets"
HOC, SONG = "hoc_tap", "cuoc_song"
EDU_TOPICS = {"Giáo dục - Khoa Học"}

# thư mục -> (mục, tên hiển thị, lý do)
DATASETS = {
    "ViSGKCap": (HOC, "bbdontcry/ViSGKCap", "Trang sách giáo khoa Cánh Diều lớp 1-3 (Toán, Tiếng Việt, Tự nhiên và Xã hội, Đạo đức)."),
    "D-Truong__ViEduVQA": (HOC, "D-Truong/ViEduVQA", "Hỏi đáp trên tranh minh họa tiểu học; đã xác nhận có trang SGK Cánh Diều (trùng ViSGKCap). Nội dung tranh là cảnh đời thường vẽ trong SGK."),
    "VLAI-AIVN__ViInfographicVQA": ("tách theo chủ đề", "VLAI-AIVN/ViInfographicVQA", "Infographic tin tức; chủ đề 'Giáo dục - Khoa Học' vào HỌC TẬP, 8 chủ đề còn lại (kinh tế, y tế, văn hóa, thiên tai, thể thao, thời tiết, quốc phòng, nhân vật) vào CUỘC SỐNG."),
    "uitnlp__OpenViVQA-dataset": (SONG, "uitnlp/OpenViVQA-dataset", "Ảnh đời thường ở Việt Nam (phố, quán, nhà, ghe), hỏi đáp mở."),
    "Ouyangxuelili__vlsp2023-vqa-dataset": (SONG, "Ouyangxuelili/vlsp2023-vqa-dataset", "Bản sao một phần của OpenViVQA (cảnh đời thường); đã bị loại khỏi vai trò huấn luyện vì trùng."),
    "huyhuy123__ViOCRVQA": (SONG, "huyhuy123/ViOCRVQA", "Ảnh bìa sách (không phải SGK): hỏi tên sách, tác giả, nhà xuất bản, thể loại."),
    "5CD-AI__Viet-Table-Markdown": (SONG, "5CD-AI/Viet-Table-Markdown", "Ảnh bảng/biểu mẫu trong báo cáo, tin tức, hành chính; từ khóa học đường chỉ ~5% (mẫu 400)."),
}


def infographic_topics():
    """{id mẫu: chủ đề} cho mẫu dạng parquet (tệp#n) và ảnh jpg (qua images_paths)."""
    src = ROOT / "VLAI-AIVN__ViInfographicVQA" / "data"
    by_row, by_jpg, n = {}, {}, 0
    for f in sorted(src.glob("*.parquet")):
        t = pq.read_table(f, columns=["images_paths", "image_type"]).to_pylist()
        for r in t:
            n += 1
            by_row[f"{f.name}#{n}"] = r["image_type"]
            for p in r["images_paths"] or []:
                by_jpg.setdefault(p, r["image_type"])
    return by_row, by_jpg


def main():
    overlay = list(csv.DictReader((ROOT / "_reports" / "splits_overlay.csv").open(encoding="utf-8")))
    by_dir = {name: [] for name in DATASETS}
    dir_of = {v[1]: k for k, v in DATASETS.items()}
    for r in overlay:
        if r["dataset"] in dir_of:
            by_dir[dir_of[r["dataset"]]].append(r)
    by_row, by_jpg = infographic_topics()

    def category(dname, r):
        cat = DATASETS[dname][0]
        if dname != "VLAI-AIVN__ViInfographicVQA":
            return cat, ""
        sid = r["sample_id"]
        topic = by_jpg.get(sid.split("/", 1)[1]) if sid.startswith("images/") else by_row.get(sid)
        return (HOC if topic in EDU_TOPICS else SONG), topic or ""

    # liên kết mềm
    for sub in ("1_hoc_tap", "2_cuoc_song"):
        d = ROOT / sub
        d.mkdir(exist_ok=True)
        for old in d.iterdir():
            if old.is_symlink():
                old.unlink()
    for dname, (cat, _, _) in DATASETS.items():
        targets = [("1_hoc_tap", HOC), ("2_cuoc_song", SONG)] if cat not in (HOC, SONG) else [("1_hoc_tap" if cat == HOC else "2_cuoc_song", cat)]
        for sub, _ in targets:
            link = ROOT / sub / dname
            os.symlink(os.path.relpath(ROOT / dname, ROOT / sub), link)

    # đếm theo mục và vai trò
    table = {}
    with (ROOT / "_reports" / "phan_loai_mau.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["dataset", "sample_id", "muc", "chu_de", "role"])
        for dname, items in by_dir.items():
            for r in items:
                cat, topic = category(dname, r)
                table.setdefault((dname, cat), Counter())[r["role"]] += 1
                w.writerow([r["dataset"], r["sample_id"], cat, topic, r["role"]])
    topics = Counter()
    for r in overlay:
        if r["dataset"] == "VLAI-AIVN/ViInfographicVQA" and not r["sample_id"].startswith("images/"):
            topics[by_row.get(r["sample_id"], "?")] += 1

    def size_gb(name):
        d = ROOT / name
        return sum(p.stat().st_size for p in d.rglob("*") if p.is_file() and not p.name.endswith(".part")) / 1e9

    L = ["# Dữ liệu ngoài: phân theo mục HỌC TẬP và CUỘC SỐNG", "",
         "Không di chuyển dữ liệu. Khung nhìn bằng liên kết mềm: `data/external/1_hoc_tap/` và `data/external/2_cuoc_song/` (ViInfographicVQA có mặt ở cả hai vì chia theo chủ đề).",
         "Số mẫu là số dòng/ảnh trong lớp phủ train/val/test (`splits_overlay.csv`), gồm cả mẫu bị loại (`excluded`). Phân loại dựa trên nội dung đã xem, xem cột lý do.", ""]
    for cat, title in ((HOC, "1. HỌC TẬP"), (SONG, "2. CUỘC SỐNG")):
        L += [f"## {title}", "", "| Bộ dữ liệu | Thư mục | Số mẫu | train | val | test | bị loại | Dung lượng (GB) | Nội dung |", "|---|---|---|---|---|---|---|---|---|"]
        tot = Counter()
        for dname, (dcat, label, why) in DATASETS.items():
            c = table.get((dname, cat))
            if not c:
                continue
            n = sum(c.values())
            tot.update(c)
            share = "" if dcat in (HOC, SONG) else " (một phần)"
            L.append(f"| {label}{share} | `{dname}/` | {n} | {c['train']} | {c['val']} | {c['test']} | {c['excluded']} | {size_gb(dname):.1f}{' (cả bộ)' if share else ''} | {why} |")
        L += [f"| **Tổng** | | **{sum(tot.values())}** | {tot['train']} | {tot['val']} | {tot['test']} | {tot['excluded']} | | |", ""]
    L += ["## Chủ đề của ViInfographicVQA (số Q/A trong parquet)", "", "| Chủ đề | Mục | Số Q/A |", "|---|---|---|"]
    L += [f"| {t} | {'HỌC TẬP' if t in EDU_TOPICS else 'CUỘC SỐNG'} | {n} |" for t, n in topics.most_common()]
    L += ["", "## Lưu ý", "",
          "- Phân loại theo nội dung, không theo giấy phép. ViEduVQA CC BY-NC; các bộ khác phần lớn không khai báo giấy phép; ảnh SGK có bản quyền, chỉ dùng nghiên cứu nội bộ.",
          "- ViEduVQA xếp HỌC TẬP vì có trang SGK; hình ảnh bên trong là cảnh đời thường vẽ cho trẻ em. Tỉ lệ ảnh thuộc SGK trong bộ chưa đo hết.",
          "- Khoảng trống: chưa có SGK lớp 4-5, chưa có biểu đồ/bản đồ SGK thật; mục HỌC TẬP hiện chủ yếu là lớp 1-3.", ""]
    text = "\n".join(L)
    (ROOT / "PHAN_LOAI.md").write_text(text, encoding="utf-8")
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "phan_loai_hoc_tap_cuoc_song.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

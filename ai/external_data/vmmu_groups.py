#!/usr/bin/env python3
"""Nối các ảnh của VMMU thuộc cùng một câu hỏi (cạnh theo mã câu hỏi), để chia split theo cụm không làm rò rỉ.

VMMU có 210 câu hỏi xuất hiện 5 lần dưới dạng ảnh khác nhau (nguyên trang, cắt khung, chỉ chữ cho OCR...); pHash không nối được các biến thể cắt
khung, nên nối theo cột `ID` (bỏ hậu tố `_vqa.png` / `_text.png`). Chỉ ĐỌC dữ liệu; cần chỉ mục `_index/anvo25__vmmu.jsonl` (do `dedup.py index` tạo).
Đầu ra cục bộ: data/external/_reports/vmmu_question_edges.csv (sha_a, sha_b), do make_splits.py đọc cùng với content_verified_edges.csv.

  uv run --with pyarrow --with numpy python external_data/vmmu_groups.py
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from external_data import hf  # noqa: E402

NAME = "anvo25__vmmu"


def main():
    src = hf.dataset_dir(NAME)
    sha_of = {}
    for line in (hf.ROOT / "_index" / f"{NAME}.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        sha_of[r["id"]] = r["sha256"]
    by_question, n = defaultdict(set), 0
    for f in sorted(src.rglob("*.parquet")):  # cùng thứ tự và cách đếm với dedup.iter_samples
        for batch in pq.ParquetFile(f).iter_batches(batch_size=64, columns=["ID", "image"]):
            for r in batch.to_pylist():
                n += 1
                if r["image"] and r["image"].get("bytes"):
                    sid = f"{f.name}#{n}"
                    by_question[re.sub(r"_(vqa|text)\.png$", "", r["ID"])].add(sha_of[sid])
    edges = [(sorted(v)[0], s) for v in by_question.values() for s in sorted(v)[1:]]
    out = hf.ROOT / "_reports" / "vmmu_question_edges.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sha_a", "sha_b"])
        w.writerows(edges)
    multi = sum(len(v) > 1 for v in by_question.values())
    print(f"{NAME}: {n} dòng, {len(by_question)} câu hỏi, {multi} câu có nhiều ảnh khác nhau, {len(edges)} cạnh -> {out}")


if __name__ == "__main__":
    main()

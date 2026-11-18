#!/usr/bin/env python3
"""Xuất Q/A có sẵn trong dữ liệu ngoài sang JSONL hội thoại (định dạng như ai/finetune/export_sft.py), CHỈ cho mẫu vai trò `train` của lớp phủ.

Phạm vi hiện tại: ViEduVQA và ViInfographicVQA (đơn ảnh, câu hỏi/đáp nằm ngay trong parquet). Ảnh được ghi một lần theo SHA-256 vào
data/external/_sft/images/. Mỗi dòng mang nguồn, giấy phép khai báo và cờ `answer_source: ai_generated_unverified`: đáp án do máy sinh,
CHƯA phải ground truth và KHÔNG viết theo văn nói/định dạng JSON của hệ thống; chỉ phù hợp để dạy hỏi đáp, cần rà soát trước khi dùng.
Không bao giờ xuất mẫu `excluded`, `val`, `test`.

  uv run --with pyarrow --with numpy python external_data/to_sft.py [--limit-per-dataset N]
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from external_data import hf  # noqa: E402
from external_data.rows import read_rows  # noqa: E402

ROOT = hf.ROOT
OVERLAY = ROOT / "_reports" / "splits_overlay.csv"
OUT = ROOT / "_sft"
SPECS = {
    "D-Truong/ViEduVQA": {"dir": "D-Truong__ViEduVQA", "q": "Question", "a": "Answer", "license": "cc-by-nc-4.0"},
    "VLAI-AIVN/ViInfographicVQA": {"dir": "VLAI-AIVN__ViInfographicVQA", "q": "question", "a": "answer", "license": "không khai báo"},
}
ASK_SYSTEM = (Path(__file__).resolve().parents[1] / "prompts" / "ask_v1.txt").read_text(encoding="utf-8").strip()


def wanted_rows(limit):
    per = Counter()
    for r in csv.DictReader(OVERLAY.open(encoding="utf-8")):
        spec = SPECS.get(r["dataset"])
        if not spec or r["role"] != "train" or ".parquet#" not in r["sample_id"]:
            continue
        if r["dataset"] == "VLAI-AIVN/ViInfographicVQA" and r["sample_id"].startswith("multi_"):
            continue  # tập đa ảnh cần nhiều ảnh mỗi câu hỏi: chưa hỗ trợ
        if limit and per[r["dataset"]] >= limit:
            continue
        per[r["dataset"]] += 1
        yield r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-per-dataset", type=int, default=0)
    a = ap.parse_args()
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    out_path = OUT / "qa_external_train.jsonl"
    counts, skipped = Counter(), Counter()
    by_ds: dict[str, dict[str, dict]] = {}
    for r in wanted_rows(a.limit_per_dataset):
        by_ds.setdefault(r["dataset"], {})[r["sample_id"]] = r
    with out_path.open("w", encoding="utf-8") as fh:
        for ds, wanted in by_ds.items():
            spec = SPECS[ds]
            for sample, row in read_rows(ROOT / spec["dir"], list(wanted), ["image", spec["q"], spec["a"]]):
                r = wanted[sample]
                q, ans = (row.get(spec["q"]) or "").strip(), (row.get(spec["a"]) or "").strip()
                if not q or not ans or not row["image"] or not row["image"].get("bytes"):
                    skipped[ds] += 1
                    continue
                data = row["image"]["bytes"]
                ext = ".png" if data[:8] == b"\x89PNG\r\n\x1a\n" else ".jpg"
                img = OUT / "images" / f"{r['image_sha256']}{ext}"
                if not img.exists():
                    img.write_bytes(data)
                rec = {"id": f"{spec['dir']}:{sample}", "kind": "ask", "role": "train", "source_dataset": ds,
                       "license_declared": spec["license"], "answer_source": "ai_generated_unverified", "cluster_id": r["cluster_id"],
                       "messages": [{"role": "system", "content": ASK_SYSTEM},
                                    {"role": "user", "content": [{"type": "image", "image": str(img)}, {"type": "text", "text": q}]},
                                    {"role": "assistant", "content": ans}]}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                counts[ds] += 1
    print("Đã ghi", out_path)
    for ds in SPECS:
        print(f"  {ds}: {counts[ds]} dòng (bỏ qua {skipped[ds]})")
    (OUT / "SOURCE.txt").write_text("Xuất từ lớp phủ splits_overlay.csv, chỉ vai trò train. Đáp án do máy sinh, chưa kiểm chứng. Chỉ dùng nghiên cứu nội bộ.\n", encoding="utf-8")


if __name__ == "__main__":
    main()

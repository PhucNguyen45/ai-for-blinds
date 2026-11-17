#!/usr/bin/env python3
"""Kiểm tra tính toàn vẹn của data/benchmark/manifest.json.

Chạy từ thư mục ai/:
    uv run python evaluation/generators/validate_benchmark.py

Kiểm tra: file tồn tại, sha256 khớp, id duy nhất, trường bắt buộc, schema
ground truth, split hợp lệ, biến thể không rò rỉ dev/test, tóm tắt phân bố.
Thoát mã 1 nếu có lỗi.
"""

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

BENCH = Path(__file__).resolve().parents[3] / "data" / "benchmark"
REQUIRED = ["id", "category", "group", "source", "image", "ground_truth", "sha256",
            "ground_truth_sha256", "difficulty", "split", "expected_status", "license"]
SPLITS = {"dev", "test"}
DIFFICULTIES = {"easy", "medium", "hard"}
STATUSES = {"ok", "unreadable"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((BENCH / "manifest.json").read_text(encoding="utf-8"))
    items = manifest["items"]
    errors, warnings = [], []
    ids = [i["id"] for i in items]
    for dup in {i for i in ids if ids.count(i) > 1}:
        errors.append(f"id trùng: {dup}")
    by_id = {i["id"]: i for i in items}

    for it in items:
        iid = it.get("id", "?")
        for key in REQUIRED:
            if key not in it:
                errors.append(f"{iid}: thiếu trường '{key}'")
        if it.get("split") not in SPLITS:
            errors.append(f"{iid}: split không hợp lệ")
        if it.get("difficulty") not in DIFFICULTIES:
            errors.append(f"{iid}: difficulty không hợp lệ")
        if it.get("expected_status") not in STATUSES:
            errors.append(f"{iid}: expected_status không hợp lệ")
        for path_key, hash_key in (("image", "sha256"), ("ground_truth", "ground_truth_sha256")):
            p = (BENCH / it[path_key]).resolve()
            if not p.is_relative_to(BENCH.resolve()):
                errors.append(f"{iid}: đường dẫn không an toàn {it[path_key]}")
            elif not p.is_file() and it.get("restricted"):
                warnings.append(f"{iid}: {path_key} hạn chế phân phối không có trên máy này (bỏ qua kiểm hash)")
            elif not p.is_file():
                errors.append(f"{iid}: thiếu file {it[path_key]}")
            elif sha256(p) != it[hash_key]:
                errors.append(f"{iid}: sai hash {it[path_key]}")
        if it.get("truth_schema") == "truth_v0.2" and (BENCH / it["ground_truth"]).is_file():
            truth = json.loads((BENCH / it["ground_truth"]).read_text(encoding="utf-8"))
            if truth["id"] != iid:
                errors.append(f"{iid}: id trong ground truth là {truth['id']}")
            if truth["expected_status"] != it["expected_status"]:
                errors.append(f"{iid}: expected_status lệch giữa manifest và truth")
            if not truth["propositions"] or not truth["questions"]:
                errors.append(f"{iid}: thiếu mệnh đề hoặc câu hỏi")
            if not any(p["critical"] for p in truth["propositions"]) and it["expected_status"] == "ok":
                errors.append(f"{iid}: không có mệnh đề critical")
        base = it.get("derived_from")
        if base:
            if base not in by_id:
                errors.append(f"{iid}: derived_from '{base}' không tồn tại")
            elif by_id[base]["split"] != it["split"]:
                errors.append(f"{iid}: split khác ảnh gốc {base} (rò rỉ dev/test)")

    print(f"Benchmark v{manifest['version']}: {len(items)} mẫu")
    for title, key in (("Theo nhóm", "group"), ("Theo loại", "category"),
                       ("Theo split", "split"), ("Theo độ khó", "difficulty"),
                       ("Theo trạng thái kỳ vọng", "expected_status")):
        counts = Counter(i[key] for i in items if key in i)
        print(f"\n{title}:")
        for k, v in sorted(counts.items()):
            print(f"  {k:<16}{v}")
    props = qs = 0
    for it in items:
        if it.get("truth_schema") == "truth_v0.2" and (BENCH / it["ground_truth"]).is_file():
            t = json.loads((BENCH / it["ground_truth"]).read_text(encoding="utf-8"))
            props += len(t["propositions"])
            qs += len(t["questions"])
    print(f"\nTổng mệnh đề (truth_v0.2): {props}; tổng câu hỏi: {qs}")

    for w in warnings:
        print("CẢNH BÁO:", w)
    if errors:
        print("\nLỖI:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("\nHợp lệ: không có lỗi.")


if __name__ == "__main__":
    main()

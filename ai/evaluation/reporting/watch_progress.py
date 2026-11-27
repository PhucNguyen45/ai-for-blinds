#!/usr/bin/env python3
"""Xem tiến độ một lần chạy benchmark: đọc file JSONL mà runner đang ghi (chỉ đọc, không gọi model).

  python3 evaluation/reporting/watch_progress.py evaluation/records_openvivqa_dev__gemma_img_only.jsonl --total 300

Tự cập nhật mỗi 2 giây, thoát khi đủ số ca hoặc khi bấm Ctrl+C. Tỉ lệ đúng hiển thị là tạm tính.
"""

import argparse
import json
import time
from pathlib import Path


def read_rows(path: Path) -> list[dict]:
    rows = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:  # dòng cuối đang được ghi dở
                continue
            rows[r["sha16"]] = r
    return list(rows.values())


def render(rows: list[dict], total: int) -> str:
    done = len(rows)
    filled = int(40 * min(done / total, 1))
    errors = sum(r["status"] == "error" for r in rows)
    scored = [r for r in rows if r["status"] != "error"]
    key = "contains" if rows and "contains" in rows[0] else "hit"
    good = sum(bool(r.get(key)) for r in scored)
    lat = [r["latency_s"] for r in rows if r.get("latency_s")]
    mean = sum(lat) / len(lat) if lat else 0
    eta = int((total - done) * mean)
    label = "Chứa đáp án" if key == "contains" else "Đúng"
    out = [f"[{'█' * filled}{'░' * (40 - filled)}] {done}/{total} ({done / total:.0%})",
           f"{label} (tạm tính): {good}/{len(scored)}" + (f" = {good / len(scored):.1%}" if scored else ""),
           f"Lỗi: {errors} | {mean:.1f} s/ca | còn khoảng {eta // 60} phút {eta % 60:02d} giây"]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", type=Path)
    ap.add_argument("--total", type=int, required=True)
    ap.add_argument("--once", action="store_true", help="in một lần rồi thoát")
    args = ap.parse_args()
    if args.total <= 0:
        raise SystemExit("--total phải lớn hơn 0.")
    try:
        while True:
            rows = read_rows(args.jsonl)
            if not args.once:
                print("\033[2J\033[H", end="")  # xóa màn hình
            print(args.jsonl.name)
            print(render(rows, args.total), flush=True)
            if args.once or len(rows) >= args.total:
                break
            time.sleep(2)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

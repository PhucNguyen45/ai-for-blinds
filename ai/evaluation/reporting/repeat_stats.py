#!/usr/bin/env python3
"""Thống kê độ dao động giữa các lần chạy lặp (records_<...>__reps) — dùng chỉ số từ khóa thô.

Chạy từ thư mục ai/:
    uv run python evaluation/reporting/repeat_stats.py evaluation/records_b0e__lmstudio__qwen-qwen3-vl-4b__reps
    (thêm --compare <thư mục bản ghi đơn> để đặt cạnh kết quả một lần chạy trước đó)

Chỉ tính các ảnh có expected_status == "ok". Mỗi lần chạy có tổng số mệnh đề critical phủ được;
báo cáo trung bình, độ lệch chuẩn giữa các lần, và những ảnh dao động mạnh nhất.
"""

import argparse
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import proposition_check as pc  # noqa: E402

AI_ROOT = HERE.parents[1]
BENCH = AI_ROOT.parent / "data" / "benchmark"


def score(record, by_id):
    item = by_id[record["benchmark_id"]]
    truth = json.loads((BENCH / item["ground_truth"]).read_text(encoding="utf-8"))
    crit = [p for p in truth["propositions"] if p["critical"]]
    res = record["result"]
    text = res.get("interpretation_vi", "") if res["status"] in ("ok", "partial") else ""
    return len(pc.count(crit, text)[0]), len(crit), res["status"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--compare", help="thư mục bản ghi đơn (một lần chạy) để so sánh")
    args = ap.parse_args()
    manifest = json.loads((BENCH / "manifest.json").read_text(encoding="utf-8"))
    by_id = {i["id"]: i for i in manifest["items"]}

    per_image = defaultdict(dict)  # id -> rep -> hits
    crit_total = {}
    errors = defaultdict(int)
    for path in sorted([*Path(args.dir).glob("*.json"), *(Path(args.dir) / "_restricted").glob("*.json")]):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if by_id[rec["benchmark_id"]]["expected_status"] != "ok":
            continue
        hits, crit, status = score(rec, by_id)
        per_image[rec["benchmark_id"]][rec["rep"]] = hits
        crit_total[rec["benchmark_id"]] = crit
        if status not in ("ok", "partial"):
            errors[rec["rep"]] += 1

    reps = sorted({r for d in per_image.values() for r in d})
    complete = [i for i, d in per_image.items() if len(d) == len(reps)]
    total_crit = sum(crit_total[i] for i in complete)
    run_totals = [sum(per_image[i][r] for i in complete) for r in reps]

    print(f"Lần lặp: {len(reps)} | ảnh đủ lần: {len(complete)}/{len(per_image)} | mệnh đề critical: {total_crit}")
    print("Tổng theo từng lần chạy:", ", ".join(f"r{r:02d}={t}" for r, t in zip(reps, run_totals)))
    mean = st.mean(run_totals)
    sd = st.stdev(run_totals) if len(run_totals) > 1 else float("nan")
    print(f"Trung bình {mean:.1f}/{total_crit} ({mean / total_crit:.1%}); độ lệch chuẩn giữa các lần {sd:.1f} "
          f"({sd / total_crit:.1%} của tổng)")
    if errors:
        print("Ảnh lỗi (tính 0) theo lần:", dict(errors))

    spread = sorted(((max(per_image[i].values()) - min(per_image[i].values()), i) for i in complete),
                    reverse=True)
    print("\nẢnh dao động mạnh nhất (max - min giữa các lần):")
    for d, i in spread[:6]:
        vals = [per_image[i][r] for r in reps]
        print(f"  {i:<22} {vals}  / {crit_total[i]}")
    print(f"Số ảnh có kết quả ổn định hoàn toàn: {sum(1 for d, _ in spread if d == 0)}/{len(complete)}")

    if args.compare:
        single = 0
        for i in complete:
            p = next((q for q in (Path(args.compare) / f"{i}.json", Path(args.compare) / "_restricted" / f"{i}.json") if q.exists()), None)
            if p:
                single += score(json.loads(p.read_text(encoding="utf-8")), by_id)[0]
        lo, hi = min(run_totals), max(run_totals)
        verdict = "nằm trong" if lo <= single <= hi else "nằm NGOÀI"
        print(f"\nLần chạy đơn trước đó: {single}/{total_crit} — {verdict} khoảng {lo}–{hi} của các lần lặp")


if __name__ == "__main__":
    main()

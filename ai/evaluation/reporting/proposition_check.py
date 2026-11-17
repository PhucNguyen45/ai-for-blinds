#!/usr/bin/env python3
"""Kiểm tra thô (lexical) mức phủ mệnh đề critical của ground truth truth_v0.2.

KHÔNG phải điểm rubric và KHÔNG đo độ đúng/bịa đặt: chỉ kiểm tra xem các số và
tên trong mệnh đề critical có xuất hiện trong câu trả lời hay không. Dùng để
phát hiện nhanh ca lỗi rõ ràng ở tập dev; kết quả cần chấm tay bổ sung.

Chạy từ thư mục ai/:
    uv run python evaluation/reporting/proposition_check.py --session <session_id>
    uv run python evaluation/reporting/proposition_check.py --runs <run_id> ...
"""

import argparse
import json
import re
import unicodedata
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[2]
BENCH = AI_ROOT.parent / "data" / "benchmark"
RUNS = AI_ROOT / "evaluation" / "runs"
SESSIONS = AI_ROOT / "evaluation" / "sessions"


STRIP_ACCENTS = False


def norm(text):
    text = unicodedata.normalize("NFC", text).lower().replace(",", ".")
    if STRIP_ACCENTS:
        text = text.replace("đ", "d")
        text = "".join(c for c in unicodedata.normalize("NFD", text)
                       if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text)


def numbers(text):
    return re.findall(r"\d+(?:\.\d+)?", norm(text))


def hit(prop, answer):
    obj, subj = norm(prop["object"]), norm(prop["subject"])
    nums_obj = numbers(prop["object"])
    ans = norm(answer)
    ans_nums = set(re.findall(r"\d+(?:\.\d+)?", ans))
    if prop["kind"] == "value":
        # cần số của giá trị VÀ nhãn đối tượng (phần sau 'Cột/Điểm/Phần'…)
        label = re.sub(r"^(cột|cot|điểm|diem|phần|phan|cạnh|canh|góc|goc)\s+", "", subj).split(" – ")[0]
        return all(n in ans_nums for n in nums_obj) and label in ans
    if prop["kind"] in ("relation", "comparison", "structure"):
        # lấy cụm tên/đối tượng đích; yêu cầu cả hai đầu xuất hiện nếu là quan hệ
        needs = [obj] if prop["kind"] != "relation" else [subj, obj]
        return all(n.rstrip("?") in ans for n in needs)
    return False


def load_runs(args):
    if args.session:
        s = json.loads((SESSIONS / f"{args.session}.json").read_text(encoding="utf-8"))
        return [t["run_id"] for t in s["tasks"] if t.get("run_id")]
    return args.runs


def count(crit, answer):
    global STRIP_ACCENTS
    STRIP_ACCENTS = False
    strict = [p for p in crit if hit(p, answer)]
    STRIP_ACCENTS = True
    lenient = [p for p in crit if hit(p, answer)]
    STRIP_ACCENTS = False
    return strict, lenient


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session")
    ap.add_argument("--runs", nargs="*", default=[])
    args = ap.parse_args()
    manifest = json.loads((BENCH / "manifest.json").read_text(encoding="utf-8"))
    by_sha = {i["sha256"]: i for i in manifest["items"]}
    total_hit = total = total_len = 0
    for run_id in load_runs(args):
        run = json.loads((RUNS / f"{run_id}.json").read_text(encoding="utf-8"))
        item = by_sha[run["image_sha256"]]
        if item.get("truth_schema") != "truth_v0.2":
            continue
        truth = json.loads((BENCH / item["ground_truth"]).read_text(encoding="utf-8"))
        answer = run["response"]["choices"][0]["message"]["content"] or ""
        crit = [p for p in truth["propositions"] if p["critical"]]
        hits, lenient = count(crit, answer)
        misses = [p for p in crit if p not in hits]
        total_hit, total = total_hit + len(hits), total + len(crit)
        total_len += len(lenient)
        extra = f"  (bỏ qua dấu: {len(lenient)})" if len(lenient) != len(hits) else ""
        print(f"{item['id']:<22}{len(hits):>3}/{len(crit):<3} critical phủ được"
              f"  [{item['difficulty']}]{extra}")
        for p in misses[:6]:
            print(f"    thiếu: {p['subject']} | {p['predicate']} | {p['object']}")
    if total:
        print(f"\nTổng: {total_hit}/{total} = {total_hit / total:.0%} chặt; "
              f"{total_len}/{total} = {total_len / total:.0%} khi bỏ qua dấu "
              "(chỉ số thô, chưa phải điểm rubric)")


if __name__ == "__main__":
    main()

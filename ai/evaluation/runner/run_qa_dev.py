#!/usr/bin/env python3
"""Đo hỏi đáp theo hình trên các câu hỏi của tập DEV (truth_v0.2: lookup, comparison, computation, relation, refusal).

Hai điều kiện: chỉ ảnh (`--description none`) hoặc ảnh kèm lời mô tả đã sinh trước đó (`--description <thư mục bản ghi>`,
ví dụ `records_survey__baseline_q4_ctx16k_p1/scale_1`, lấy lần lặp 1). Chấm thô bằng từ khóa (`reporting/qa_score.py`).

  uv run python evaluation/runner/run_qa_dev.py --tag qa_img_only --description none            # dry run
  uv run python evaluation/runner/run_qa_dev.py --tag qa_img_only --description none --execute
"""

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AI_ROOT))

from evaluation.reporting.qa_score import score_answer  # noqa: E402
from vlm.ask import ask_about_image  # noqa: E402
from vlm.providers import find_lmstudio_url, lmstudio_loaded_config  # noqa: E402

BENCH = AI_ROOT.parent / "data" / "benchmark"
SAFE = re.compile(r"^[a-z0-9_.-]+$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--model", default="qwen/qwen3-vl-4b")
    ap.add_argument("--description", default="none",
                    help="'none' hoặc thư mục bản ghi (chứa <id>__r01.json) để lấy lời mô tả đã sinh")
    ap.add_argument("--max-requests", type=int, default=120)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    if not SAFE.match(args.tag):
        raise SystemExit("--tag chỉ gồm a-z, 0-9, _ . -")
    desc_dir = None if args.description == "none" else (AI_ROOT / args.description).resolve()
    if desc_dir and not desc_dir.is_relative_to(AI_ROOT / "evaluation"):
        raise SystemExit("--description phải nằm trong ai/evaluation/.")

    manifest = json.loads((BENCH / "manifest.json").read_text(encoding="utf-8"))
    jobs = []
    for it in manifest["items"]:
        if it["split"] != "dev" or it.get("restricted") or it.get("expected_status") != "ok":
            continue
        truth = json.loads((BENCH / it["ground_truth"]).read_text(encoding="utf-8"))
        for q in truth.get("questions", []):
            jobs.append((it, q))
    out_dir = AI_ROOT / "evaluation" / f"records_qa__{args.tag}"
    todo = [(it, q) for it, q in jobs if not (out_dir / f"{it['id']}__{q['id']}.json").exists()]
    print(f"Câu hỏi dev: {len(jobs)} | cần chạy: {len(todo)} | mô tả: {args.description} | "
          f"{'EXECUTE' if args.execute else 'DRY RUN'}")
    if len(todo) > args.max_requests:
        raise SystemExit(f"Vượt --max-requests ({len(todo)} > {args.max_requests}).")
    if args.execute:
        base = find_lmstudio_url()
        cfg = lmstudio_loaded_config(base.removesuffix("/v1"), args.model) if base else None
        if not cfg:
            raise SystemExit(f"Model {args.model} chưa được nạp trong LM Studio.")
        out_dir.mkdir(exist_ok=True)
        meta_path = out_dir / "qa_meta.json"
        if not meta_path.exists():
            meta_path.write_text(json.dumps({"tag": args.tag, "model": args.model, "description": args.description,
                                             "lmstudio_loaded_config": cfg}, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
        for n, (it, q) in enumerate(todo, 1):
            image = (BENCH / it["image"]).resolve()
            if hashlib.sha256(image.read_bytes()).hexdigest() != it["sha256"]:
                raise SystemExit(f"Sai hash ảnh: {it['id']}")
            description = ""
            if desc_dir:
                rec = json.loads((desc_dir / f"{it['id']}__r01.json").read_text(encoding="utf-8"))
                description = rec["result"].get("interpretation_vi", "")
            r = ask_about_image(image, q["question"], description=description, image_id=it["id"],
                                model=args.model, provider="lmstudio")
            hit = score_answer(q["answer"], q["type"], r.answer_vi) if r.status != "error" else None
            rec = {"benchmark_id": it["id"], "qid": q["id"], "type": q["type"], "question": q["question"],
                   "expected": q["answer"], "hit": hit, "result": r.model_dump(mode="json", exclude_none=True)}
            (out_dir / f"{it['id']}__{q['id']}.json").write_text(
                json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"[{n}/{len(todo)}] {it['id']:<20} {q['id']:<4} {q['type']:<12} {r.status:<7} hit={hit}", flush=True)

    # tóm tắt (cả khi dry run nếu đã có bản ghi)
    stat = defaultdict(lambda: [0, 0, 0])  # type -> [đúng, tổng hợp lệ, lỗi]
    lat = []
    for p in sorted(out_dir.glob("*__*.json")) if out_dir.exists() else []:
        rec = json.loads(p.read_text(encoding="utf-8"))
        s = stat[rec["type"]]
        if rec["hit"] is None:
            s[2] += 1
            continue
        s[0] += bool(rec["hit"])
        s[1] += 1
        lat.append((rec["result"].get("meta") or {}).get("latency_seconds") or 0)
    if stat:
        print("\nLoại câu hỏi        đúng/tổng (lỗi)")
        for t, (h, n, e) in sorted(stat.items()):
            print(f"  {t:<14} {h}/{n} ({e})")
        h = sum(v[0] for v in stat.values()); n = sum(v[1] for v in stat.values())
        print(f"  {'TỔNG':<14} {h}/{n} = {h / n:.1%}" + (f" | thời gian TB {sum(lat) / len(lat):.1f}s" if lat else ""))


if __name__ == "__main__":
    main()

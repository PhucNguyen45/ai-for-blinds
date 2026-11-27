#!/usr/bin/env python3
"""Đo hỏi đáp trắc nghiệm trên VMMU, tập val hoặc test của lớp phủ (`data/external/_reports/splits_overlay.csv`).

Mặc định là val. Tập test chỉ chạy khi gõ rõ `--split test`, với cấu hình đã chốt trên val. Không dùng tập train.
Mỗi ảnh duy nhất (theo SHA-256) được hỏi một lần, với đúng `vn_prompt` của bộ dữ liệu làm câu hỏi.
Ảnh chỉ được ghi tạm (thư mục tạm của hệ thống, `TMPDIR`) và tự xóa, không để lại trong `data/`.

Đầu ra, mỗi lần chạy chỉ hai file (không tạo file rời cho từng ca):
- `evaluation/records_vmmu_<split>__<tag>.jsonl`: một dòng cho mỗi ảnh (đáp án gốc, đáp án đã tách, đúng/sai, nguyên văn trả lời).
- `evaluation/records_vmmu_<split>__<tag>__tom_tat.md`: tổng hợp theo môn và danh sách các ca cần kiểm tay.

Chấm thô: lấy đáp án trong {X} hoặc sau cụm "đáp án (đúng) là X"; không khớp thì tính là sai. Không phải rubric.
Chạy lại là tiếp tục từ chỗ dừng. Bản ghi cũ (một file JSON mỗi ca) được gộp vào JSONL rồi xóa.

  uv run --with pyarrow python evaluation/runner/run_vmmu_val.py --tag gemma_img_only            # dry run
  uv run --with pyarrow python evaluation/runner/run_vmmu_val.py --tag gemma_img_only --execute
"""

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[2]
ROOT = AI_ROOT.parent
sys.path.insert(0, str(AI_ROOT))

from vlm.ask import ask_about_image  # noqa: E402
from vlm.providers import find_lmstudio_url, lmstudio_loaded_config  # noqa: E402

DATASET = "anvo25/vmmu"
PARQUET_DIR = ROOT / "data" / "external" / "1_hoc_tap" / "anvo25__vmmu" / "data"
OVERLAY = ROOT / "data" / "external" / "_reports" / "splits_overlay.csv"
EVAL_DIR = AI_ROOT / "evaluation"
SAFE = re.compile(r"^[a-z0-9_.-]+$")


def load_items(split: str):
    """Ảnh duy nhất của split theo SHA-256, kèm đáp án và câu hỏi của bộ dữ liệu."""
    import pyarrow.parquet as pq

    split_rows = [r for r in csv.DictReader(OVERLAY.open(encoding="utf-8"))
                if r["dataset"] == DATASET and r["role"] == split]
    if not split_rows:
        raise SystemExit(f"Không có dòng {split} nào của VMMU trong lớp phủ.")
    want = {r["image_sha256"] for r in split_rows}
    items = {}
    for fname in sorted({r["sample_id"].split("#")[0] for r in split_rows}):
        table = pq.read_table(PARQUET_DIR / fname, columns=["image", "ID", "ground_truth", "subject", "vn_prompt"])
        for i, row in enumerate(table.to_pylist()):
            data = row["image"]["bytes"]
            sha = hashlib.sha256(data).hexdigest()
            if sha in want and sha not in items:
                items[sha] = {"sha256": sha, "source": f"{fname}#{i}", "ID": row["ID"],
                              "gt": str(row["ground_truth"]).strip(), "subject": row["subject"],
                              "question": row["vn_prompt"], "bytes": data}
    missing = want - items.keys()
    if missing:
        raise SystemExit(f"Không khớp {len(missing)} ảnh {split} với file parquet.")
    return sorted(items.values(), key=lambda x: x["sha256"])


def extract_answer(text: str) -> str | None:
    """Đáp án từ câu trả lời: {X} trước, rồi 'đáp án (đúng) là X'. Không đoán: không khớp thì None (tính là sai)."""
    text = text or ""
    m = re.search(r"\{\s*([^{}]+?)\s*\}", text)
    if m:
        return m.group(1).strip().upper()
    m = re.search(r"đáp\s+án[^.\n:]{0,40}?\b(?:là|:)\s*\(?\s*([A-Ea-e]|\d+)\b(?![\w'])", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return None


def is_hit(gt: str, pred: str | None) -> bool:
    if pred is None:
        return False
    if gt.isdigit():
        return pred == gt
    gt_letters = set(re.findall(r"[A-E]", gt.upper()))
    pred_letters = set(re.findall(r"[A-E]", pred.upper()))
    return bool(gt_letters) and gt_letters == pred_letters


def load_rows(jsonl: Path) -> dict:
    if not jsonl.exists():
        return {}
    rows = {}
    for line in jsonl.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            rows[r["sha16"]] = r
    return rows


def write_rows(jsonl: Path, rows: dict):
    tmp = jsonl.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for r in sorted(rows.values(), key=lambda x: x["sha16"]):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(jsonl)


def migrate_legacy_dir(legacy: Path, rows: dict) -> int:
    """Gộp bản ghi cũ (một file JSON mỗi ca) vào JSONL, rồi xóa thư mục cũ nếu số ca khớp."""
    if not legacy.is_dir():
        return 0
    files = [p for p in legacy.glob("*.json") if p.name != "run_meta.json"]
    added = 0
    for p in files:
        rec = json.loads(p.read_text(encoding="utf-8"))
        key = rec["sha256"][:16]
        if key not in rows:
            rows[key] = {"sha16": key, "ID": rec["ID"], "subject": rec["subject"], "gt": rec["gt"],
                         "pred": rec["pred"], "hit": rec["hit"], "status": rec["result"].get("status"),
                         "answer_vi": rec["result"].get("answer_vi", ""),
                         "latency_s": (rec["result"].get("meta") or {}).get("latency_seconds")}
            added += 1
    if all(json.loads(p.read_text(encoding="utf-8"))["sha256"][:16] in rows for p in files):
        shutil.rmtree(legacy)
    return added


def rescore(rows: dict):
    for r in rows.values():
        if r["status"] == "error":
            continue
        r["pred"] = extract_answer(r["answer_vi"])
        r["hit"] = is_hit(r["gt"], r["pred"])


def write_summary(rows: dict, path: Path, tag: str, model: str, split: str):
    by_subj = defaultdict(lambda: {"hit": 0, "n": 0, "err": 0, "none": 0})
    tot = {"hit": 0, "n": 0, "err": 0, "none": 0}
    for r in rows.values():
        for b in (by_subj[r["subject"]], tot):
            if r["status"] == "error":
                b["err"] += 1
                continue
            b["n"] += 1
            b["hit"] += bool(r["hit"])
            b["none"] += r["pred"] is None
    lines = [f"# VMMU {split} (overlay) — {tag}", "",
             f"- Model: `{model}` (LM Studio, reasoning tắt)",
             f"- Ngày tạo tóm tắt: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
             f"- Ảnh: {len(rows)} (tập {split} của lớp phủ)",
             "- Chấm thô: đáp án trong {X} hoặc sau 'đáp án là X'; không tách được = sai.", "",
             "## Tổng", "",
             f"- Đúng: **{tot['hit']}/{tot['n']}** = {tot['hit'] / tot['n']:.1%}" if tot["n"] else "- Chưa có kết quả",
             f"- Không tách được đáp án (model từ chối hoặc không chọn): {tot['none']}",
             f"- Lỗi vận hành (không tính điểm): {tot['err']}", "",
             "## Theo môn", "", "| Môn | Đúng/tổng | Tỉ lệ | Không tách được | Lỗi |", "|---|---|---|---|---|"]
    for s, b in sorted(by_subj.items()):
        rate = f"{b['hit'] / b['n']:.1%}" if b["n"] else "–"
        lines.append(f"| {s} | {b['hit']}/{b['n']} | {rate} | {b['none']} | {b['err']} |")
    review = [r for r in rows.values() if r["status"] == "error" or r["pred"] is None or not r["hit"]]
    lines += ["", "## Ca cần kiểm tay", "",
              "Các ca sai, không tách được đáp án, hoặc lỗi. Đọc câu trả lời để phân biệt model sai với bộ tách sai.", "",
              "| ID | Môn | Đáp án đúng | Đã tách | Trạng thái | Câu trả lời (rút gọn) |", "|---|---|---|---|---|---|"]
    for r in sorted(review, key=lambda x: (x["subject"], x["ID"])):
        snippet = (r["answer_vi"] or "").replace("|", "/").replace("\n", " ")[:160]
        lines.append(f"| `{r['ID']}` | {r['subject']} | {r['gt']} | {r['pred'] or '–'} | {r['status']} | {snippet} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--split", choices=["val", "test"], default="val")
    ap.add_argument("--model", default="google/gemma-4-e4b")
    ap.add_argument("--max-requests", type=int, default=200)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    if not SAFE.match(args.tag):
        raise SystemExit("--tag chỉ gồm a-z, 0-9, _ . -")

    items = load_items(args.split)
    jsonl = EVAL_DIR / f"records_vmmu_{args.split}__{args.tag}.jsonl"
    summary = EVAL_DIR / f"records_vmmu_{args.split}__{args.tag}__tom_tat.md"
    rows = load_rows(jsonl)
    migrated = migrate_legacy_dir(EVAL_DIR / f"records_vmmu_{args.split}__{args.tag}", rows)
    rescore(rows)  # chấm lại từ văn bản đã lưu, để mọi bản ghi dùng cùng một bộ tách đáp án
    write_rows(jsonl, rows)
    if migrated:
        print(f"Đã gộp {migrated} bản ghi cũ vào {jsonl.name} và xóa thư mục cũ.", flush=True)

    todo = [it for it in items if it["sha256"][:16] not in rows]
    print(f"Ảnh {args.split} VMMU (duy nhất): {len(items)} | đã có: {len(rows)} | cần chạy: {len(todo)} | "
          f"{'EXECUTE' if args.execute else 'DRY RUN'}", flush=True)
    if len(todo) > args.max_requests:
        raise SystemExit(f"Vượt --max-requests ({len(todo)} > {args.max_requests}).")
    if not args.execute:
        if rows:
            write_summary(rows, summary, args.tag, args.model, args.split)
        return

    base = find_lmstudio_url()
    cfg = lmstudio_loaded_config(base.removesuffix("/v1"), args.model) if base else None
    if not cfg:
        raise SystemExit(f"Model {args.model} chưa được nạp trong LM Studio.")
    # Gemma 4 mặc định bật suy nghĩ; ép tắt để không hết token trước khi trả lời (xem nhật ký 26/11).
    os.environ["LMSTUDIO_REASONING_EFFORT"] = "none"

    for n, it in enumerate(todo, 1):
        with tempfile.TemporaryDirectory(prefix="vmmu_") as tmp:  # tự xóa sau mỗi ca
            path = Path(tmp) / f"{it['sha256']}.png"
            path.write_bytes(it["bytes"])
            r = ask_about_image(path, it["question"], image_id=it["sha256"][:16], model=args.model,
                                provider="lmstudio")
        err = r.status == "error"
        pred = None if err else extract_answer(r.answer_vi)
        row = {"sha16": it["sha256"][:16], "ID": it["ID"], "subject": it["subject"], "gt": it["gt"],
               "pred": pred, "hit": None if err else is_hit(it["gt"], pred), "status": r.status,
               "prompt_id": r.meta.prompt_id if r.meta else None,
               "error": r.error.model_dump(mode="json", exclude_none=True) if r.error else None,
               "answer_vi": r.answer_vi or "",
               "latency_s": (r.meta.latency_seconds if r.meta else None)}
        rows[row["sha16"]] = row
        with jsonl.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"[{n}/{len(todo)}] {it['subject']:<10} gt={it['gt']:<4} pred={str(pred):<4} "
              f"{r.status:<7} hit={row['hit']}", flush=True)

    write_rows(jsonl, rows)  # gọn lại file, bỏ dòng trùng nếu có
    write_summary(rows, summary, args.tag, args.model, args.split)
    print(f"Tóm tắt: {summary}", flush=True)


if __name__ == "__main__":
    main()

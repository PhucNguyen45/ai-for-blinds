#!/usr/bin/env python3
"""Đo hỏi đáp mở trên OpenViVQA, tập DEV (val của lớp phủ `data/external/_reports/splits_overlay.csv`).

File test của bộ dữ liệu không có đáp án (mọi câu ghi "your answer"), nên không chấm được trên máy.
Mẫu cố định: `--sample` ảnh dev (mặc định 300), chọn theo thứ tự SHA-256, mỗi ảnh một câu hỏi (cũng chọn bằng băm).
Tăng `--sample` rồi chạy lại là mở rộng mẫu cũ, không đo lại ca đã có.

Cách chấm (chốt trước khi xem câu trả lời; thô, không phải rubric):
- `chua`: đáp án chuẩn xuất hiện nguyên cụm trong câu trả lời (số được chấp nhận cả dạng chữ số lẫn đọc bằng chữ).
  Câu trả lời của model thường dài hơn đáp án, nên tiêu chí này rộng tay.
- `phu_tu`: tỉ lệ từ của đáp án chuẩn có trong câu trả lời (trung bình trên các ca).
- Đáp án "có"/"không" được báo riêng, vì hai từ này xuất hiện trong hầu hết câu tiếng Việt.

Ảnh chỉ được ghi tạm (`TMPDIR`) rồi tự xóa. Đầu ra: hai file `evaluation/records_openvivqa_dev__<tag>.jsonl` và `...__tom_tat.md`.

  uv run python evaluation/runner/run_openvivqa_dev.py --tag gemma_img_only            # dry run
  uv run python evaluation/runner/run_openvivqa_dev.py --tag gemma_img_only --execute
"""

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[2]
ROOT = AI_ROOT.parent
sys.path.insert(0, str(AI_ROOT))

from evaluation.reporting.qa_score import _number_forms  # noqa: E402
from evaluation.runner.run_vmmu_val import SAFE, load_rows, write_rows  # noqa: E402
from vlm.ask import ask_about_image  # noqa: E402
from vlm.providers import find_lmstudio_url, lmstudio_loaded_config  # noqa: E402

DATASET = "uitnlp/OpenViVQA-dataset"
DATA = ROOT / "data" / "external" / "2_cuoc_song" / "uitnlp__OpenViVQA-dataset"
OVERLAY = ROOT / "data" / "external" / "_reports" / "splits_overlay.csv"
EVAL_DIR = AI_ROOT / "evaluation"
YES_NO = {"có", "không"}


def tokens(text: str) -> list[str]:
    return re.findall(r"\w+", unicodedata.normalize("NFC", text or "").lower())


def has_phrase(answer: list[str], phrase: list[str]) -> bool:
    n = len(phrase)
    return n > 0 and any(answer[i:i + n] == phrase for i in range(len(answer) - n + 1))


def variants(gold: str) -> list[list[str]]:
    """Đáp án chuẩn, cộng các biến thể trong đó mỗi số được đọc bằng chữ."""
    out = [tokens(gold)]
    for num in re.findall(r"\d+", gold):
        for form in _number_forms(num):
            alt = tokens(re.sub(rf"(?<!\d){num}(?!\d)", f" {form} ", gold))
            if alt not in out:
                out.append(alt)
    return out


def score(gold: str, answer: str) -> tuple[bool, float]:
    ans = tokens(answer)
    forms = variants(gold)
    contains = any(has_phrase(ans, f) for f in forms)
    recall = max((sum(t in ans for t in f) / len(f) for f in forms if f), default=0.0)
    return contains, recall


def load_items(sample: int) -> list[dict]:
    val_rows = [r for r in csv.DictReader(OVERLAY.open(encoding="utf-8"))
                if r["dataset"] == DATASET and r["role"] == "val"]
    ann = json.loads((DATA / "vlsp2023_dev_data.json").read_text(encoding="utf-8"))
    id_by_name = {name: int(i) for i, name in ann["images"].items()}
    questions = {}
    for qid, a in ann["annotations"].items():
        questions.setdefault(a["image_id"], []).append((qid, a))
    items = []
    for r in sorted(val_rows, key=lambda x: x["image_sha256"]):
        member = r["sample_id"].split(":", 1)[1]
        qs = questions.get(id_by_name.get(Path(member).name))
        if not qs:
            continue
        qid, a = min(qs, key=lambda x: hashlib.sha256(f"openvivqa-v1:{x[0]}".encode()).hexdigest())
        items.append({"sha256": r["image_sha256"], "member": member, "qid": qid,
                      "question": a["question"], "gold": a["answer"]})
        if len(items) == sample:
            break
    return items


def write_summary(rows: dict, path: Path, tag: str, model: str):
    ok = [r for r in rows.values() if r["status"] != "error"]
    errors = len(rows) - len(ok)
    yn = [r for r in ok if " ".join(tokens(r["gold"])) in YES_NO]
    other = [r for r in ok if r not in yn]

    def line(name, group):
        if not group:
            return f"| {name} | 0 | – | – |"
        c = sum(r["contains"] for r in group)
        rec = sum(r["recall"] for r in group) / len(group)
        return f"| {name} | {len(group)} | {c}/{len(group)} = {c / len(group):.1%} | {rec:.1%} |"

    lat = [r["latency_s"] for r in ok if r.get("latency_s")]
    lines = [f"# OpenViVQA dev (overlay val) — {tag}", "",
             f"- Model: `{model}` (LM Studio, reasoning tắt), `ask_calc_v1`, dự phòng `ask_v1` (calc=True), chỉ ảnh",
             f"- Ngày tạo tóm tắt: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
             f"- Số ca: {len(rows)} (mỗi ảnh một câu); lỗi vận hành: {errors}"
             + (f"; thời gian trung bình {sum(lat) / len(lat):.1f} s mỗi ca" if lat else ""),
             "- Chấm thô theo từ khóa. `chứa đáp án` rộng tay vì câu trả lời dài hơn đáp án chuẩn.", "",
             "| Nhóm | Số ca | Chứa đáp án | Phủ từ trung bình |", "|---|---|---|---|",
             line("Tất cả", ok), line("Không tính có/không", other), line("Chỉ có/không (kém tin cậy)", yn), "",
             "## Ca cần kiểm tay (không chứa đáp án, hoặc lỗi)", "",
             "| Ảnh | Câu hỏi | Đáp án chuẩn | Trạng thái | Câu trả lời (rút gọn) |", "|---|---|---|---|---|"]

    def cell(text, limit):
        return (text or "").replace("|", "/").replace("\n", " ")[:limit]

    for r in sorted(rows.values(), key=lambda x: x["sha16"]):
        if r["status"] == "error" or not r["contains"]:
            lines.append(f"| {Path(r['member']).name} | {cell(r['question'], 120)} | {cell(r['gold'], 80)} | "
                         f"{r['status']} | {cell(r['answer_vi'], 160)} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--model", default="google/gemma-4-e4b")
    ap.add_argument("--sample", type=int, default=300)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    if not SAFE.match(args.tag):
        raise SystemExit("--tag chỉ gồm a-z, 0-9, _ . -")

    items = load_items(args.sample)
    jsonl = EVAL_DIR / f"records_openvivqa_dev__{args.tag}.jsonl"
    summary = EVAL_DIR / f"records_openvivqa_dev__{args.tag}__tom_tat.md"
    rows = load_rows(jsonl)
    todo = [it for it in items if it["sha256"][:16] not in rows]
    print(f"OpenViVQA dev: mẫu {len(items)} | đã có: {len(rows)} | cần chạy: {len(todo)} | "
          f"{'EXECUTE' if args.execute else 'DRY RUN'}", flush=True)
    if not args.execute:
        return

    base = find_lmstudio_url()
    cfg = lmstudio_loaded_config(base.removesuffix("/v1"), args.model) if base else None
    if not cfg:
        raise SystemExit(f"Model {args.model} chưa được nạp trong LM Studio.")
    os.environ["LMSTUDIO_REASONING_EFFORT"] = "none"

    with zipfile.ZipFile(DATA / "dev-images.zip") as images:
        for n, it in enumerate(todo, 1):
            data = images.read(it["member"])
            if hashlib.sha256(data).hexdigest() != it["sha256"]:
                raise SystemExit(f"Sai hash ảnh: {it['member']}")
            with tempfile.TemporaryDirectory(prefix="openvivqa_") as tmp:  # tự xóa sau mỗi ca
                path = Path(tmp) / Path(it["member"]).name
                path.write_bytes(data)
                r = ask_about_image(path, it["question"], image_id=it["sha256"][:16], model=args.model,
                                    provider="lmstudio")
            err = r.status == "error"
            contains, recall = (None, None) if err else score(it["gold"], r.answer_vi)
            row = {"sha16": it["sha256"][:16], "member": it["member"], "qid": it["qid"],
                   "question": it["question"], "gold": it["gold"], "contains": contains, "recall": recall,
                   "status": r.status, "prompt_id": r.meta.prompt_id if r.meta else None, "answer_vi": r.answer_vi or "",
                   "error": r.error.model_dump(mode="json", exclude_none=True) if r.error else None,
                   "latency_s": (r.meta.latency_seconds if r.meta else None)}
            rows[row["sha16"]] = row
            with jsonl.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"[{n}/{len(todo)}] {r.status:<7} contains={contains}", flush=True)

    write_rows(jsonl, rows)
    write_summary(rows, summary, args.tag, args.model)
    print(summary.read_text(encoding="utf-8").split("## Ca cần")[0])
    print(f"Tóm tắt: {summary}", flush=True)


if __name__ == "__main__":
    main()

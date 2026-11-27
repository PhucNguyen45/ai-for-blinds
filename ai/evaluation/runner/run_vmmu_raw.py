#!/usr/bin/env python3
"""Đo VLM GỐC trên VMMU val: gọi thẳng API, không qua `ask_about_image` (không system prompt, không JSON, không tính hộ).

Request chỉ gồm ảnh và `vn_prompt` nguyên văn của bộ dữ liệu; temperature 0, tắt suy nghĩ.
Chỉ chạy tập val. Mẫu: `--sample` ca đầu theo thứ tự SHA-256 (cố định, không phụ thuộc kết quả).

Tách đáp án (câu trả lời gốc có LaTeX dùng `{}`, nên khác bộ tách của `run_vmmu_val.py`):
lấy `{X}` hoặc `\\boxed{X}` CUỐI CÙNG với X là chữ A–E (hoặc số, nếu đề hỏi bằng số) và không phải đối số LaTeX;
nếu không có và câu trả lời không bị cắt thì lấy 'đáp án ... là X' cuối cùng; còn lại tính là chưa chọn.

  uv run --with pyarrow python evaluation/runner/run_vmmu_raw.py --tag gemma_raw30            # dry run
  uv run --with pyarrow python evaluation/runner/run_vmmu_raw.py --tag gemma_raw30 --execute
"""

import argparse
import json
import re
import sys
import tempfile
import time
from pathlib import Path

import httpx

AI_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AI_ROOT))

from evaluation.runner.run_vmmu_val import SAFE, is_hit, load_items, load_rows  # noqa: E402
from vlm.client import file_to_data_url  # noqa: E402
from vlm.providers import find_lmstudio_url, lmstudio_loaded_config  # noqa: E402

EVAL_DIR = AI_ROOT / "evaluation"


def extract_raw(text: str, gt: str, truncated: bool) -> str | None:
    option = r"\d" if gt.isdigit() else r"[A-E](?:\s*,?\s*[A-E])*"
    braces = re.compile(rf"(?:\\boxed|(?<![A-Za-z^_}}]))\\?\{{\s*(?:\\text\{{)?\**({option})\**\}}?\s*\\?\}}")
    found = braces.findall(text)
    if found:
        return found[-1].upper()
    if truncated:
        return None
    plain = text.replace("*", "")
    found = re.findall(rf"(?i:đáp\s+án)[^.\n:]{{0,40}}?(?:(?i:là)|:)\s*\(?\s*({option})(?![\w'])", plain)
    return found[-1].upper() if found else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--model", default="google/gemma-4-e4b")
    ap.add_argument("--sample", type=int, default=30)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    if not SAFE.match(args.tag):
        raise SystemExit("--tag chỉ gồm a-z, 0-9, _ . -")

    items = load_items("val")[:args.sample]
    jsonl = EVAL_DIR / f"records_vmmu_val_raw__{args.tag}.jsonl"
    rows = load_rows(jsonl)
    todo = [it for it in items if it["sha256"][:16] not in rows]
    print(f"VMMU val (gốc): mẫu {len(items)} | đã có: {len(rows)} | cần chạy: {len(todo)} | "
          f"{'EXECUTE' if args.execute else 'DRY RUN'}", flush=True)
    if not args.execute:
        return
    base = find_lmstudio_url()
    cfg = lmstudio_loaded_config(base.removesuffix("/v1"), args.model) if base else None
    if not cfg:
        raise SystemExit(f"Model {args.model} chưa được nạp trong LM Studio.")

    for n, it in enumerate(todo, 1):
        row = {"sha16": it["sha256"][:16], "ID": it["ID"], "subject": it["subject"], "gt": it["gt"],
               "max_tokens": args.max_tokens}
        with tempfile.TemporaryDirectory(prefix="vmmu_raw_") as tmp:  # tự xóa sau mỗi ca
            path = Path(tmp) / "page.png"
            path.write_bytes(it["bytes"])
            payload = {"model": args.model, "temperature": 0, "max_tokens": args.max_tokens,
                       "reasoning_effort": "none",
                       "messages": [{"role": "user", "content": [
                           {"type": "text", "text": it["question"]},
                           {"type": "image_url", "image_url": {"url": file_to_data_url(path)}}]}]}
            start = time.time()
            try:
                response = httpx.post(base + "/chat/completions", json=payload, timeout=900)
                response.raise_for_status()
                body = response.json()
                choice = body["choices"][0]
                text = choice["message"].get("content") or ""
                finish = choice.get("finish_reason")
                pred = extract_raw(text, it["gt"], finish == "length")
                row.update(status="ok" if text else "error", answer_vi=text, finish_reason=finish, pred=pred,
                           hit=is_hit(it["gt"], pred) if text else None,
                           completion_tokens=(body.get("usage") or {}).get("completion_tokens"))
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                row.update(status="error", answer_vi="", finish_reason=None, pred=None, hit=None,
                           error=f"{type(exc).__name__}: {exc}"[:300])
            row["latency_s"] = round(time.time() - start, 2)
        with jsonl.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"[{n}/{len(todo)}] {row['subject']:<11} gt={row['gt']:<3} pred={str(row['pred']):<3} "
              f"{row['finish_reason']} {row['latency_s']:.0f}s hit={row['hit']}", flush=True)
    print("XONG", flush=True)


if __name__ == "__main__":
    main()

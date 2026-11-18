#!/usr/bin/env python3
"""Khảo sát một model đang nạp trong LM Studio trên tập DEV (phần khảo sát model của đề tài).

Mỗi điều kiện = một hệ số phóng ảnh (scale). scale 1.0 dùng ảnh gốc; scale khác resize bằng LANCZOS (bản
resize chỉ lưu tạm, không ghi vào benchmark). Mặc định prompt b0e_v1 (đổi bằng --prompt), temperature mặc định của mã.

Ghi lại để truy vết: cấu hình model đang nạp (đọc từ API LM Studio: context, parallel, flash attention...),
số token vào/ra, thời gian, finish_reason và VRAM sau mỗi request. Bản ghi tương thích `repeat_stats.py`.

  uv run python evaluation/runner/survey_lmstudio.py --tag baseline --scales 0.5 1.0 1.5 --reps 2            # dry run
  uv run python evaluation/runner/survey_lmstudio.py --tag baseline --scales 0.5 1.0 1.5 --reps 2 --execute

Đầu ra: evaluation/records_survey__<tag>/scale_<s>/<id>__rNN.json + survey_meta.json
Báo cáo: uv run python evaluation/reporting/survey_report.py evaluation/records_survey__<tag>
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

AI_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AI_ROOT))

from vlm.describer import describe_image  # noqa: E402
from vlm.providers import find_lmstudio_url, lmstudio_loaded_config  # noqa: E402

BENCH = AI_ROOT.parent / "data" / "benchmark"
SAFE = re.compile(r"^[a-z0-9_.-]+$")


def vram_mib():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total",
                              "--format=csv,noheader,nounits"], capture_output=True, text=True,
                             timeout=10).stdout.split(",")
        return int(out[0]), int(out[1])
    except (OSError, ValueError, subprocess.SubprocessError, IndexError):
        return None, None


def git_head():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=AI_ROOT, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True, help="tên đợt khảo sát (a-z, 0-9, _ . -)")
    ap.add_argument("--model", default="qwen/qwen3-vl-4b")
    ap.add_argument("--prompt", default="b0e_v1", help="mã prompt trong ai/prompts (vd b0e_v1, b0g_v1)")
    ap.add_argument("--scales", nargs="+", type=float, default=[1.0])
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--max-requests", type=int, default=200)
    ap.add_argument("--note", default="", help="ghi chú cấu hình giao diện mà API không cho thấy")
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    if not SAFE.match(args.tag):
        raise SystemExit("--tag chỉ gồm a-z, 0-9, _ . -")
    if not 1 <= args.reps <= 10 or any(not 0.2 <= s <= 3.0 for s in args.scales):
        raise SystemExit("--reps 1..10; --scales trong 0.2..3.0")

    manifest = json.loads((BENCH / "manifest.json").read_text(encoding="utf-8"))
    items = [i for i in manifest["items"] if i["split"] == "dev"
             and i.get("truth_schema") == "truth_v0.2" and not i.get("restricted")]
    out_root = AI_ROOT / "evaluation" / f"records_survey__{args.tag}"

    def path_for(item, scale, rep):
        return out_root / f"scale_{scale:g}" / f"{item['id']}__r{rep:02d}.json"

    todo = [(rep, s, i) for rep in range(1, args.reps + 1) for s in args.scales for i in items
            if not path_for(i, s, rep).exists()]
    print(f"Benchmark v{manifest['version']} | mẫu dev (không hạn chế): {len(items)} | scales {args.scales} | "
          f"reps {args.reps} | cần chạy: {len(todo)} request | {'EXECUTE' if args.execute else 'DRY RUN'}")
    print("Thư mục:", out_root.relative_to(AI_ROOT.parent))
    if len(todo) > args.max_requests:
        raise SystemExit(f"Vượt --max-requests ({len(todo)} > {args.max_requests}).")
    if not args.execute:
        return

    base = find_lmstudio_url()
    if not base:
        raise SystemExit("Không kết nối được LM Studio.")
    root = base.removesuffix("/v1")
    cfg = lmstudio_loaded_config(root, args.model)
    if not cfg:
        raise SystemExit(f"Model {args.model} chưa được nạp trong LM Studio (nạp trước rồi chạy lại).")
    used, total = vram_mib()
    meta = {"tag": args.tag, "model": args.model, "scales": args.scales, "reps": args.reps,
            "method": f"B0 ({args.prompt})", "prompt_id": args.prompt, "started_utc": datetime.now(timezone.utc).isoformat(),
            "git_head": git_head(), "benchmark_version": manifest["version"],
            "lmstudio_loaded_config": cfg, "vram_mib_before": used, "vram_total_mib": total,
            "note": args.note}
    out_root.mkdir(exist_ok=True)
    meta_path = out_root / "survey_meta.json"
    if meta_path.exists():
        old = json.loads(meta_path.read_text(encoding="utf-8"))
        if old.get("lmstudio_loaded_config") != cfg:
            raise SystemExit("Cấu hình model đang nạp KHÁC với lần chạy trước của thẻ này; dùng --tag mới để "
                             "không trộn hai cấu hình.")
    else:
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    consecutive = 0
    with tempfile.TemporaryDirectory() as tmp:
        for n, (rep, scale, item) in enumerate(todo, 1):
            image = (BENCH / item["image"]).resolve()
            if not image.is_relative_to(BENCH.resolve()):
                raise SystemExit("Đường dẫn ảnh không an toàn.")
            if hashlib.sha256(image.read_bytes()).hexdigest() != item["sha256"]:
                raise SystemExit(f"Sai hash ảnh: {item['id']}")
            send, size = image, None
            with Image.open(image) as im:
                size = im.size
                if scale != 1.0:
                    resized = im.convert("RGB").resize(
                        (round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
                    send = Path(tmp) / f"{item['id']}_{scale:g}.png"
                    resized.save(send)
                    size = resized.size
            result = describe_image(send, image_id=item["id"], prompt_id=args.prompt, model=args.model,
                                    provider="lmstudio")
            used, _ = vram_mib()
            record = {"method": "B0", "prompt_id": args.prompt, "benchmark_id": item["id"], "rep": rep, "scale": scale,
                      "image_size": list(size), "image_sha256": item["sha256"],
                      "benchmark_version": manifest["version"],
                      "result": result.model_dump(mode="json", exclude_none=True),
                      "trace": {"vram_mib_after": used}}
            p = path_for(item, scale, rep)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            code = result.error.code if result.error else ""
            usage = result.meta.usage if result.meta and result.meta.usage else None
            print(f"[{n}/{len(todo)}] r{rep:02d} x{scale:g} {item['id']:<22} {result.status:<11} {code} "
                  f"in={usage.prompt_tokens if usage else '-'} out={usage.completion_tokens if usage else '-'}",
                  flush=True)
            consecutive = consecutive + 1 if code in ("timeout", "http_error", "config_error") else 0
            if consecutive >= 3:
                raise SystemExit("Dừng: 3 lỗi hạ tầng liên tiếp.")
    meta["finished_utc"] = datetime.now(timezone.utc).isoformat()
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

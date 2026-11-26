#!/usr/bin/env python3
"""Chạy B0e hoặc B1 trên tập DEV của benchmark.

Chốt an toàn: mặc định chỉ liệt kê (dry run); cần --execute để gọi API; chỉ nhận mẫu split=dev
có ground truth truth_v0.2; giới hạn số request; không tự thử lại (trừ khi bật --retry-429 và chỉ
với HTTP 429). Mỗi lần chạy lưu một bản ghi (kể cả khi lỗi); bản ghi đã có sẽ được bỏ qua.

  --method b0e|b1       b0e: B0 + dòng "nêu đủ giá trị"; b1: 2 bước (trích xuất -> diễn giải)
  --provider/--model    ghi đè nhà cung cấp/model; bản ghi lưu riêng theo (nhà cung cấp, model)
  --reps N              lặp mỗi ảnh N lần (lưu ở records_<...>__reps/<id>__rNN.json) để ước lượng nhiễu

Chạy từ thư mục ai/:
    uv run python evaluation/runner/run_b1_dev.py --method b0e --provider lmstudio            # dry run
    uv run python evaluation/runner/run_b1_dev.py --method b0e --provider lmstudio --reps 3 --execute
"""

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AI_ROOT))

from vlm.b1 import describe_image_b1  # noqa: E402
from vlm.describer import describe_image  # noqa: E402

BENCH = AI_ROOT.parent / "data" / "benchmark"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--max-requests", type=int, default=50)
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--method", choices=["b1", "b0e"], default="b1")
    ap.add_argument("--provider", choices=["openrouter", "google", "lmstudio"],
                    help="nhà cung cấp (mặc định VLM_PROVIDER hoặc openrouter)")
    ap.add_argument("--model", help="ghi đè model (mặc định lấy từ .env hoặc LM Studio)")
    ap.add_argument("--reps", type=int, default=1, help="số lần lặp mỗi ảnh (1 = bản ghi đơn)")
    ap.add_argument("--sleep", type=float, default=0.0, help="giây chờ giữa các request")
    ap.add_argument("--max-tokens", type=int, default=600,
                    help="giới hạn token đầu ra của B0e (mặc định 600; reasoning bật cần lớn hơn)")
    ap.add_argument("--retry-429", type=int, default=0,
                    help="số lần thử lại CHỈ khi gặp HTTP 429 (chờ 20s, 40s, ...)")
    args = ap.parse_args()
    if not 1 <= args.reps <= 20:
        raise SystemExit("--reps phải trong khoảng 1..20.")

    slug = lambda t: re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")  # noqa: E731
    suffix = "".join("__" + slug(x) for x in (args.provider, args.model) if x)
    base_dir = AI_ROOT / "evaluation" / f"records_{args.method}{suffix}"
    out_dir = base_dir if args.reps == 1 else base_dir.with_name(base_dir.name + "__reps")
    per_image = 2 if args.method == "b1" else 1

    manifest = json.loads((BENCH / "manifest.json").read_text(encoding="utf-8"))
    items = [i for i in manifest["items"]
             if i["split"] == "dev" and i.get("truth_schema") == "truth_v0.2"]
    if args.ids:
        unknown = set(args.ids) - {i["id"] for i in items}
        if unknown:
            raise SystemExit(f"Không phải mẫu dev hợp lệ: {sorted(unknown)}")
        items = [i for i in items if i["id"] in set(args.ids)]

    def path_for(item, rep):
        # mẫu hạn chế phân phối (SGK): bản ghi đi vào _restricted/ để KHÔNG bị commit lên repo công khai
        name = f"{item['id']}.json" if args.reps == 1 else f"{item['id']}__r{rep:02d}.json"
        return out_dir / ("_restricted" if item.get("restricted") else "") / name

    # lặp ngoài cùng theo rep để kết quả dở dang vẫn cân bằng giữa các ảnh
    todo = [(rep, i) for rep in range(1, args.reps + 1) for i in items
            if not path_for(i, rep).exists()]

    if len(todo) * per_image > args.max_requests:
        raise SystemExit(f"Cần tối đa {len(todo) * per_image} request, vượt giới hạn "
                         f"{args.max_requests} (dùng --max-requests để nâng).")
    print(f"Benchmark v{manifest['version']} | mẫu dev: {len(items)} | lần chạy cần thực hiện: "
          f"{len(todo)} | request tối đa: {len(todo) * per_image} | chế độ: "
          f"{'EXECUTE' if args.execute else 'DRY RUN'}")
    print("Thư mục bản ghi:", out_dir.relative_to(AI_ROOT.parent))
    if not args.execute:
        return

    out_dir.mkdir(exist_ok=True)
    consecutive_infra = 0
    for n, (rep, item) in enumerate(todo, 1):
        image = (BENCH / item["image"]).resolve()
        if not image.is_relative_to(BENCH.resolve()):
            raise SystemExit("Đường dẫn ảnh không an toàn.")
        if hashlib.sha256(image.read_bytes()).hexdigest() != item["sha256"]:
            raise SystemExit(f"Sai hash ảnh: {item['id']}")
        attempts = 0
        while True:
            attempts += 1
            trace = {}
            if args.method == "b1":
                result = describe_image_b1(image, image_id=item["id"], trace=trace,
                                           model=args.model, provider=args.provider)
            else:
                result = describe_image(image, image_id=item["id"], prompt_id="b0e_v1",
                                        model=args.model, provider=args.provider,
                                        max_tokens=args.max_tokens)
            rate_limited = bool(result.error and result.error.http_status == 429)
            if not (rate_limited and attempts <= args.retry_429):
                break
            wait = 20 * attempts
            print(f"    429 ở {item['id']}, chờ {wait}s rồi thử lại ({attempts}/{args.retry_429})",
                  flush=True)
            time.sleep(wait)
        trace["attempts"] = attempts
        record = {"method": args.method.upper(), "benchmark_id": item["id"], "rep": rep,
                  "image_sha256": item["sha256"], "benchmark_version": manifest["version"],
                  "result": result.model_dump(mode="json", exclude_none=True), "trace": trace}
        path_for(item, rep).parent.mkdir(parents=True, exist_ok=True)
        path_for(item, rep).write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        code = result.error.code if result.error else ""
        print(f"[{n}/{len(todo)}] r{rep:02d} {item['id']:<22} {result.status:<11} {code}",
              flush=True)
        consecutive_infra = (consecutive_infra + 1
                             if code in ("timeout", "http_error", "config_error") else 0)
        if consecutive_infra >= 3:
            raise SystemExit("Dừng: 3 lỗi hạ tầng liên tiếp.")
        if args.sleep and n < len(todo):
            time.sleep(args.sleep)


if __name__ == "__main__":
    main()

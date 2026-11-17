#!/usr/bin/env python3
"""Chạy phương pháp B1 (trích xuất dữ kiện -> diễn giải) trên tập DEV của benchmark.

Chốt an toàn: mặc định chỉ liệt kê (dry run); cần --execute để gọi API; chỉ nhận mẫu split=dev
có ground truth truth_v0.2; giới hạn số request (mỗi ảnh tối đa 2 request); không tự thử lại.
Mỗi ảnh lưu một bản ghi tại ai/evaluation/records_<method>/<benchmark_id>.json (kể cả khi lỗi);
ảnh đã có bản ghi sẽ được bỏ qua (chạy lại bằng cách xóa bản ghi thủ công).

Chạy từ thư mục ai/:
    uv run python evaluation/runner/run_b1_dev.py            # dry run
    uv run python evaluation/runner/run_b1_dev.py --execute
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AI_ROOT))

from vlm.describer import describe_image, describe_image_b1  # noqa: E402

BENCH = AI_ROOT.parent / "data" / "benchmark"



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--max-requests", type=int, default=50)
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--method", choices=["b1", "b0e"], default="b1",
                    help="b1: 2 bước (trích xuất -> diễn giải); b0e: B0 + dòng yêu cầu nêu đủ giá trị")
    ap.add_argument("--provider", choices=["openrouter", "google"],
                    help="nhà cung cấp (mặc định VLM_PROVIDER hoặc openrouter)")
    ap.add_argument("--model", help="ghi đè model (mặc định lấy từ .env); bản ghi lưu riêng theo model")
    args = ap.parse_args()
    slug = lambda t: re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")  # noqa: E731
    suffix = "".join("__" + slug(x) for x in (args.provider, args.model) if x)
    out_dir = AI_ROOT / "evaluation" / f"records_{args.method}{suffix}"
    per_image = 2 if args.method == "b1" else 1

    manifest = json.loads((BENCH / "manifest.json").read_text(encoding="utf-8"))
    items = [i for i in manifest["items"]
             if i["split"] == "dev" and i.get("truth_schema") == "truth_v0.2"]
    if args.ids:
        unknown = set(args.ids) - {i["id"] for i in items}
        if unknown:
            raise SystemExit(f"Không phải mẫu dev hợp lệ: {sorted(unknown)}")
        items = [i for i in items if i["id"] in set(args.ids)]
    todo = [i for i in items if not (out_dir / f"{i['id']}.json").exists()]

    if len(todo) * per_image > args.max_requests:
        raise SystemExit(f"Cần tối đa {len(todo) * per_image} request, vượt giới hạn {args.max_requests}.")
    print(f"Benchmark v{manifest['version']} | mẫu dev: {len(items)} | cần chạy: {len(todo)} "
          f"| request tối đa: {len(todo) * per_image} | chế độ: {'EXECUTE' if args.execute else 'DRY RUN'}")
    if not args.execute:
        for i in todo:
            print(" ", i["id"])
        return

    out_dir.mkdir(exist_ok=True)
    consecutive_infra = 0
    for n, item in enumerate(todo, 1):
        image = (BENCH / item["image"]).resolve()
        if not image.is_relative_to(BENCH.resolve()):
            raise SystemExit("Đường dẫn ảnh không an toàn.")
        if hashlib.sha256(image.read_bytes()).hexdigest() != item["sha256"]:
            raise SystemExit(f"Sai hash ảnh: {item['id']}")
        trace = {}
        if args.method == "b1":
            result = describe_image_b1(image, image_id=item["id"], trace=trace, model=args.model,
                                       provider=args.provider)
        else:
            result = describe_image(image, image_id=item["id"], prompt_id="b0e_v1",
                                    model=args.model, provider=args.provider)
        record = {"method": args.method.upper(), "benchmark_id": item["id"],
                  "image_sha256": item["sha256"], "benchmark_version": manifest["version"],
                  "result": result.model_dump(mode="json", exclude_none=True), "trace": trace}
        (out_dir / f"{item['id']}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        code = result.error.code if result.error else ""
        print(f"[{n}/{len(todo)}] {item['id']:<22} {result.status:<11} {code}", flush=True)
        consecutive_infra = (consecutive_infra + 1
                             if code in ("timeout", "http_error", "config_error") else 0)
        if consecutive_infra >= 3:
            raise SystemExit("Dừng: 3 lỗi hạ tầng liên tiếp.")


if __name__ == "__main__":
    main()

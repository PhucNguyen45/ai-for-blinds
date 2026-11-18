#!/usr/bin/env python3
"""Đo cổng kiểm tra chất lượng ảnh (`capture/quality.py`) trên tập huấn luyện TỔNG HỢP cục bộ.

Nhãn thật lấy từ `capture_issue` (dark, blur, glare, cropped_*) hoặc "ok" (degradation none/mild).
Báo cáo: tỉ lệ bắt đúng theo từng loại lỗi, tỉ lệ báo nhầm trên ảnh đạt, nhầm lẫn giữa các loại.

  uv run python evaluation/reporting/capture_gate_eval.py --data ../data/train/v1 [--out báo_cáo.md]

Giới hạn: ảnh tổng hợp, lỗi do bộ sinh tạo ra rất rõ rệt; kết quả không đại diện cho ảnh chụp thật bằng điện thoại.
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AI_ROOT))

from capture.quality import Thresholds, check_image  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    data = Path(args.data)
    th = Thresholds()
    conf = defaultdict(Counter)  # nhãn thật -> kết quả cổng
    for p in sorted(data.glob("tr_*.json")):
        item = json.loads(p.read_text(encoding="utf-8"))
        truth = item["capture_issue"] or ("ok_mild" if item["degradation"] == "mild" else "ok")
        report = check_image(data / item["image"], th)
        conf[truth][report.issues[0] if report.issues else "ok"] += 1

    lines = ["# Cổng kiểm tra chất lượng ảnh — đo trên tập huấn luyện tổng hợp", ""]
    lines.append(f"- Ngưỡng: {th}")
    lines.append(f"- Tập: `{data.name}`, {sum(sum(c.values()) for c in conf.values())} ảnh (tổng hợp, cục bộ)")
    lines += ["", "| Nhãn thật | Số ảnh | Cổng báo `dark` | `blur` | `glare` | Cho qua (`ok`) | Bắt đúng |", "|---|---|---|---|---|---|---|"]
    for truth in sorted(conf, key=lambda k: (k.startswith("ok"), k)):
        c, n = conf[truth], sum(conf[truth].values())
        right = c["ok"] if truth.startswith("ok") else c[truth]
        lines.append(f"| {truth} | {n} | {c['dark']} | {c['blur']} | {c['glare']} | {c['ok']} | "
                     f"{right}/{n} ({right / n:.0%}) |")
    ok_n = sum(sum(conf[k].values()) for k in conf if k.startswith("ok"))
    ok_flagged = sum(sum(v for kk, v in conf[k].items() if kk != "ok") for k in conf if k.startswith("ok"))
    lines += ["", f"**Báo nhầm trên ảnh đạt:** {ok_flagged}/{ok_n} ({ok_flagged / ok_n:.1%}).", "",
              "Các loại `cropped_*` và phần lớn `glare` cổng KHÔNG bắt (0% ở cột Bắt đúng là đúng thiết kế, không phải lỗi): lỗi cắt mép phụ thuộc "
              "nội dung nên giao cho VLM (prompt `b0g_v1`).", "",
              "Giới hạn: ảnh tổng hợp với lỗi rõ rệt; ngưỡng cần hiệu chỉnh lại trên ảnh chụp thật."]
    text = "\n".join(lines) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

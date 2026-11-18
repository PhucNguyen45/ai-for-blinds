#!/usr/bin/env python3
"""Tổng hợp một đợt khảo sát (records_survey__<tag>) thành báo cáo Markdown.

Chỉ số chính: mức phủ mệnh đề critical (từ khóa thô, xem proposition_check.py; KHÔNG phải điểm rubric) —
theo từng scale, từng loại hình; kèm token, thời gian, finish_reason, lỗi, VRAM. Mẫu expected_status != ok
(ảnh không đọc được) được tách riêng: kiểm tra model có báo "unreadable" hay không.

  uv run python evaluation/reporting/survey_report.py evaluation/records_survey__<tag> [--out báo_cáo.md]
"""

import argparse
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import proposition_check as pc  # noqa: E402

AI_ROOT = HERE.parents[1]
BENCH = AI_ROOT.parent / "data" / "benchmark"


def pct(x, n):
    return f"{x / n:.1%}" if n else "-"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--out")
    ap.add_argument("--compare", help="thư mục đợt khảo sát khác để so khớp cùng ảnh (chỉ lần lặp 1)")
    args = ap.parse_args()
    root = Path(args.dir)
    meta = json.loads((root / "survey_meta.json").read_text(encoding="utf-8"))
    manifest = json.loads((BENCH / "manifest.json").read_text(encoding="utf-8"))
    by_id = {i["id"]: i for i in manifest["items"]}
    crit_of = {}
    for iid, it in by_id.items():
        t = json.loads((BENCH / it["ground_truth"]).read_text(encoding="utf-8"))
        crit_of[iid] = [p for p in t.get("propositions", []) if p["critical"]]

    lines = []
    w = lines.append
    cfg = meta["lmstudio_loaded_config"]
    inst = cfg["instance"]["config"]
    w(f"# Khảo sát model `{meta['model']}` — đợt `{meta['tag']}`")
    w("")
    w(f"- Phương pháp: {meta['method']}; benchmark v{meta['benchmark_version']} (tập dev); mã git `{meta['git_head']}`")
    w(f"- Bắt đầu {meta['started_utc']}; scales {meta['scales']}; số lần lặp {meta['reps']}")
    w(f"- Model: {cfg['params']} {cfg['quantization']['name']}, {cfg['size_bytes'] / 1e9:.2f} GB, "
      f"context tối đa {cfg['max_context_length']}")
    w("- Cấu hình đang nạp (API LM Studio): " + ", ".join(
        f"{k}={inst[k]}" for k in ("context_length", "parallel", "flash_attention", "eval_batch_size",
                                  "physical_batch_size", "offload_kv_cache_to_gpu") if k in inst))
    w(f"- VRAM trước khi chạy: {meta.get('vram_mib_before')}/{meta.get('vram_total_mib')} MiB")
    if meta.get("note"):
        w(f"- Ghi chú: {meta['note']}")
    w("")

    scales = sorted(d for d in root.glob("scale_*") if d.is_dir())
    summary = []
    cat_table = defaultdict(dict)  # category -> scale -> (hit,total)
    detail = {}
    for sd in scales:
        scale = float(sd.name.split("_")[1])
        per_rep = defaultdict(lambda: [0, 0])  # rep -> [hit,total] cho ảnh ok
        per_img = defaultdict(dict)
        toks_in, toks_out, lat, vram = [], [], [], []
        fin, err, unread = Counter(), Counter(), Counter()
        sizes = set()
        for p in sorted(sd.glob("*.json")):
            rec = json.loads(p.read_text(encoding="utf-8"))
            iid, res = rec["benchmark_id"], rec["result"]
            it = by_id[iid]
            sizes.add(tuple(rec["image_size"]))
            m = res.get("meta") or {}
            if m.get("usage"):
                toks_in.append(m["usage"]["prompt_tokens"])
                toks_out.append(m["usage"]["completion_tokens"])
            if m.get("latency_seconds") is not None:
                lat.append(m["latency_seconds"])
            fin[m.get("finish_reason") or "-"] += 1
            if rec["trace"].get("vram_mib_after"):
                vram.append(rec["trace"]["vram_mib_after"])
            if res["status"] == "error":
                err[res["error"]["code"]] += 1
                continue  # lỗi hạ tầng: không tính vào độ phủ (chỉ đếm ở cột Lỗi)
            if it["expected_status"] != "ok":
                unread["flagged" if res["status"] == "unreadable" else "missed"] += 1
                continue
            text = res.get("interpretation_vi", "") if res["status"] in ("ok", "partial") else ""
            hits = len(pc.count(crit_of[iid], text)[0])
            per_rep[rec["rep"]][0] += hits
            per_rep[rec["rep"]][1] += len(crit_of[iid])
            per_img[iid][rec["rep"]] = hits
            c = cat_table[it["category"]].setdefault(scale, [0, 0])
            c[0] += hits
            c[1] += len(crit_of[iid])
        summary.append((scale, sorted(sizes), per_rep, toks_in, toks_out, lat, fin, err, unread, vram))
        detail[scale] = per_img

    w("## 1. Mức phủ mệnh đề critical theo độ phóng ảnh")
    w("")
    w("| Scale | Cỡ ảnh | Phủ trung bình | Từng lần lặp | Token vào (TB) | Token ra (TB) | Thời gian TB / p95 (s) | Lỗi |")
    w("|---|---|---|---|---|---|---|---|")
    for scale, sizes, per_rep, ti, to, lat, fin, err, unread, vram in summary:
        reps = sorted(per_rep)
        runs = [per_rep[r][0] for r in reps]
        total = st.mean(per_rep[r][1] for r in reps) if reps else 0
        mean = st.mean(runs) if runs else 0
        lat_p95 = sorted(lat)[int(0.95 * (len(lat) - 1))] if lat else 0
        sz = f"{sizes[0][0]}×{sizes[0][1]}" if len(sizes) == 1 else f"{len(sizes)} cỡ"
        w(f"| x{scale:g} | {sz} | {mean:.1f}/{total} ({pct(mean, total)}) | "
          f"{', '.join(f'r{r:02d}={per_rep[r][0]}/{per_rep[r][1]}' for r in reps)} | "
          f"{st.mean(ti) if ti else 0:.0f} | {st.mean(to) if to else 0:.0f} | "
          f"{st.mean(lat) if lat else 0:.1f} / {lat_p95:.1f} | {sum(err.values())} |")
    w("")
    w("Chỉ số từ khóa thô, chạm trần và không đo độ bịa; chênh lệch nhỏ giữa các hàng không có ý nghĩa nếu nằm "
      "trong độ lệch giữa các lần lặp của cùng một hàng.")
    w("")

    w("## 2. Theo loại hình (phủ trung bình, cộng dồn các lần lặp)")
    w("")
    w("| Loại hình | " + " | ".join(f"x{s[0]:g}" for s in summary) + " |")
    w("|---|" + "---|" * len(summary))
    for cat in sorted(cat_table):
        cells = []
        for s in summary:
            h = cat_table[cat].get(s[0])
            cells.append(f"{h[0]}/{h[1]} ({pct(h[0], h[1])})" if h else "-")
        w(f"| {cat} | " + " | ".join(cells) + " |")
    w("")

    w("## 3. Ổn định, kết thúc, VRAM, ảnh không đọc được")
    w("")
    w("| Scale | finish_reason | Lỗi theo mã | Ảnh không đọc được (báo / bỏ sót) | VRAM tối đa (MiB) |")
    w("|---|---|---|---|---|")
    for scale, sizes, per_rep, ti, to, lat, fin, err, unread, vram in summary:
        w(f"| x{scale:g} | {dict(fin)} | {dict(err) or '-'} | {unread.get('flagged', 0)} / {unread.get('missed', 0)} | "
          f"{max(vram) if vram else '-'} |")
    w("")

    w("## 4. Ảnh dao động hoặc khác nhau nhiều giữa các scale")
    w("")
    base = {iid: st.mean(d.values()) for iid, d in detail[summary[0][0]].items()}
    rows = []
    for iid in base:
        means = [st.mean(detail[s[0]][iid].values()) for s in summary if iid in detail[s[0]]]
        if len(means) == len(summary) and max(means) - min(means) > 0:
            rows.append((max(means) - min(means), iid, means))
    for d, iid, means in sorted(rows, reverse=True)[:10]:
        w(f"- `{iid}` ({by_id[iid]['category']}, {len(crit_of[iid])} mệnh đề): " +
          ", ".join(f"x{s[0]:g}={m:.1f}" for s, m in zip(summary, means)))
    if not rows:
        w("- Không có ảnh nào khác nhau giữa các scale theo chỉ số này.")
    w("")
    if args.compare:
        other = Path(args.compare)
        om = json.loads((other / "survey_meta.json").read_text(encoding="utf-8"))

        def rep1(d):
            out = {}
            for p in d.glob("scale_*/*__r01.json"):
                rec = json.loads(p.read_text(encoding="utf-8"))
                res, iid = rec["result"], rec["benchmark_id"]
                if res["status"] == "error" or by_id[iid]["expected_status"] != "ok":
                    continue
                text = res.get("interpretation_vi", "") if res["status"] in ("ok", "partial") else ""
                out[(rec["scale"], iid)] = len(pc.count(crit_of[iid], text)[0])
            return out

        a, b = rep1(root), rep1(other)
        w(f"## So khớp cùng ảnh: `{meta['tag']}` ({meta['model']}) và `{om['tag']}` ({om['model']}), chỉ lần lặp 1")
        w("")
        w("Chỉ tính ảnh có kết quả hợp lệ ở cả hai đợt (loại bản ghi lỗi). Một lần lặp: không thấy được dao động.")
        w("")
        w(f"| Scale | Số ảnh | Mệnh đề | {meta['model']} | {om['model']} | Ảnh khác nhau (đợt này vs đợt so sánh) |")
        w("|---|---|---|---|---|---|")
        for sc in sorted({k[0] for k in a} | {k[0] for k in b}):
            ids = sorted(i for (s_, i) in a if s_ == sc and (sc, i) in b)
            ta = sum(a[(sc, i)] for i in ids)
            tb = sum(b[(sc, i)] for i in ids)
            tot = sum(len(crit_of[i]) for i in ids)
            diff = ", ".join(f"`{i}` {a[(sc, i)]} vs {b[(sc, i)]}" for i in ids if a[(sc, i)] != b[(sc, i)])
            w(f"| x{sc:g} | {len(ids)} | {tot} | {ta} | {tb} | {diff or '-'} |")
        w("")
    w("## 5. Giới hạn")
    w("")
    w("- Phóng to bằng nội suy (LANCZOS) không thêm chi tiết thật; nó chỉ tăng số token thị giác. Ảnh chụp thật ở "
      "độ phân giải cao có thể cho kết quả khác. Muốn tách hai yếu tố cần render lại benchmark ở độ phân giải cao.")
    w("- Số lần lặp nhỏ, một model, tập dev tổng hợp: kết quả thăm dò, không khái quát.")
    w("- Temperature 0 không cho kết quả giống hệt giữa hai lần (đã quan sát), nên mọi so sánh cần khoảng dao động.")
    text = "\n".join(lines) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print("Đã ghi", args.out)
    else:
        print(text)


if __name__ == "__main__":
    main()

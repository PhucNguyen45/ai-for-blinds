#!/usr/bin/env python3
"""Sinh tập HUẤN LUYỆN tổng hợp cho fine-tune VLM (tách hoàn toàn khỏi benchmark dev/test).

Mỗi mẫu gồm: ảnh JPEG (giống đường ống backend: JPEG), ground truth dạng mệnh đề (truth_v0.2), lời diễn giải
MỤC TIÊU bằng văn nói tiếng Việt (số đọc bằng chữ, ý chính trước, kết thúc bằng câu gợi ý), các cặp hỏi đáp có trả lời
nói, và nhãn lỗi chụp (mờ, tối, chói, cắt mất một phần) kèm lời hướng dẫn chụp lại. Lời diễn giải sinh từ chính dữ
liệu vẽ ảnh nên đúng tuyệt đối (không bịa).

  uv run python finetune/train_gen.py generate --n 1200 --seed 1 --out ../data/train/v1
  uv run python finetune/train_gen.py check    --train ../data/train/v1     # không trùng benchmark
  uv run python finetune/train_gen.py stats    --train ../data/train/v1

Lưu ý phương pháp: chỉ huấn luyện trên ảnh tổng hợp sạch dễ khiến mô hình học "kiểu vẽ" của bộ sinh; luôn đánh giá
trên ảnh thật (benchmark dev/test, ảnh SGK) và không bao giờ đưa dev/test vào tập huấn luyện.
"""

import argparse
import hashlib
import io
import json
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

AI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_ROOT))

from evaluation.generators import generate_benchmark_v02 as gb  # noqa: E402
from finetune import themes as T  # noqa: E402
from finetune.vn_numbers import sn, su  # noqa: E402

W, H = gb.W, gb.H
DEFAULT_BENCH = AI_ROOT.parent / "data" / "benchmark"
SCHEMA = "train_v0.1"
PALETTE_BAR = ["#3679b5", "#2a9d8f", "#e76f51", "#6a4c93", "#7a8b00", "#c1121f", "#457b9d"]
SUBTITLES = ["Dữ liệu minh họa", "Số liệu điều tra", None, "Đơn vị: theo bảng chú thích"]
ENDINGS = ["Bạn có muốn nghe thêm chi tiết không?", "Bạn muốn nghe thêm phần nào nữa?",
           "Bạn có muốn mình đọc tiếp không?"]
CATEGORY_WEIGHTS = {"bar_chart": 16, "line_chart": 12, "pie_chart": 10, "table": 14, "flow_diagram": 14,
                    "cycle_diagram": 10, "geometry": 14, "schematic_map": 10}
PAGE_TYPE = {"bar_chart": "chart", "line_chart": "chart", "pie_chart": "chart", "table": "table",
             "schematic_map": "map", "flow_diagram": "figure", "cycle_diagram": "figure",
             "geometry": "figure"}


# --------------------------------------------------------------------------- tiện ích

def lf(s):
    return s[:1].lower() + s[1:]


def join_vi(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " và " + items[-1]


def pick_cats(rng, key, k):
    pool = T.CATSETS[key]
    k = min(k, len(pool))
    if key in T.SEQUENTIAL:
        i = rng.randint(0, len(pool) - k)
        return pool[i:i + k]
    return rng.sample(pool, k)


def fmt(v):
    return gb.vn(f"{v:.1f}") if isinstance(v, float) else str(v)


def sample(category, img, truth, description, qa):
    return {"category": category, "page_type": PAGE_TYPE[category], "img": img, "truth": truth,
            "description": description, "qa": qa}


def add_qa(t, qa, question, answer, spoken, qtype):
    t.qa(question, answer, qtype)
    qa.append({"question": question, "answer_spoken": spoken, "type": qtype})


def grid_axes(d, left, top, right, bottom, ymax, ylabel):
    for tick in range(0, ymax + 1, 5):
        y = bottom - tick / ymax * (bottom - top)
        d.line((left, y, right, y), fill="#dddddd", width=2)
        d.text((left - 20, y), str(tick), font=gb.font(22), fill="black", anchor="rm")
    d.text((left - 90, top - 40), ylabel, font=gb.font(23), fill="black", anchor="lm")


# --------------------------------------------------------------------------- biểu đồ cột

def gen_bar(rng):
    title, ylabel, unit, key, lo, hi = rng.choice(T.BAR_THEMES)
    labeled = rng.random() < 0.5
    k = min(rng.randint(3, 6), len(T.CATSETS[key]))
    cats = pick_cats(rng, key, k)
    if labeled:
        values = rng.sample(range(lo, hi + 1), k)
    else:
        mult = [v for v in range(5, hi + 1, 5) if v >= max(5, lo - 2)]
        k = min(k, len(mult))
        cats = cats[:k]
        values = rng.sample(mult, k)
    ymax = math.ceil((max(values) + 2) / 5) * 5
    img, d = gb.canvas(title, rng.choice(SUBTITLES))
    left, top, right, bottom = 150, 180, 1020, 620
    grid_axes(d, left, top, right, bottom, ymax, ylabel)
    slot = (right - left) / k
    color = rng.choice(PALETTE_BAR)
    ratio = rng.uniform(0.45, 0.7)
    for i, (name, v) in enumerate(zip(cats, values)):
        cx = left + slot * (i + 0.5)
        y = bottom - v / ymax * (bottom - top)
        d.rectangle((cx - slot * ratio / 2, y, cx + slot * ratio / 2, bottom), fill=color)
        if labeled:
            d.text((cx, y - 20), str(v), font=gb.font(27), fill="black", anchor="mm")
        d.text((cx, bottom + 28), name, font=gb.font(25), fill="black", anchor="mm")
    t = gb.Truth("", "bar_chart", title)
    t.d["data"] = {"values": dict(zip(cats, values)), "unit": unit, "y_axis_step": 5,
                   "has_value_labels": labeled}
    for name, v in zip(cats, values):
        t.prop("value", f"Cột {name}", "có giá trị", f"{v} {unit}")
    hi_c, lo_c = cats[values.index(max(values))], cats[values.index(min(values))]
    t.prop("comparison", "Giá trị lớn nhất", "thuộc về", hi_c)
    t.prop("comparison", "Giá trị nhỏ nhất", "thuộc về", lo_c)
    t.prop("inference", "Chênh lệch giữa cột lớn nhất và nhỏ nhất", "bằng",
           f"{max(values) - min(values)} {unit}", critical=False)
    t.prop("inference", "Tổng các cột", "bằng", f"{sum(values)} {unit}", critical=False)
    listing = "; ".join(f"{c}: {su(v, unit)}" for c, v in zip(cats, values))
    lead = ("Số ghi trên các cột lần lượt là: " if labeled else
            "Trên biểu đồ không ghi số, các giá trị dưới đây được đọc theo vạch chia ở trục đứng: ")
    desc = " ".join([
        f"Trang có một biểu đồ cột về {lf(title)}.",
        f"Biểu đồ có {sn(k)} cột: {join_vi(cats)}.",
        rng.choice([f"Cột {hi_c} cao nhất, {su(max(values), unit)}.",
                    f"Cao nhất là cột {hi_c}, với {su(max(values), unit)}."]),
        rng.choice([f"Cột {lo_c} thấp nhất, {su(min(values), unit)}.",
                    f"Thấp nhất là cột {lo_c}, chỉ có {su(min(values), unit)}."]),
        lead + listing + ".", rng.choice(ENDINGS)])
    qa = []
    add_qa(t, qa, "Cột nào có giá trị lớn nhất?", hi_c,
           f"Cột {hi_c} có giá trị lớn nhất, {su(max(values), unit)}.", "comparison")
    add_qa(t, qa, f"Cột {cats[0]} có giá trị là bao nhiêu?", f"{values[0]} {unit}",
           f"Cột {cats[0]} là {su(values[0], unit)}.", "lookup")
    add_qa(t, qa, "Tổng giá trị của tất cả các cột là bao nhiêu?", f"{sum(values)} {unit}",
           f"Tổng các cột là {su(sum(values), unit)}.", "computation")
    add_qa(t, qa, "Chênh lệch giữa cột lớn nhất và nhỏ nhất là bao nhiêu?",
           f"{max(values) - min(values)} {unit}",
           f"Chênh lệch là {su(max(values) - min(values), unit)}.", "computation")
    return sample("bar_chart", img, t, desc, qa)


# --------------------------------------------------------------------------- biểu đồ đường

def gen_line(rng):
    title, ylabel, unit, key, lo, hi = rng.choice(T.LINE_THEMES)
    labeled = rng.random() < 0.5
    cats = pick_cats(rng, key, rng.randint(4, 6))
    k = len(cats)
    mult = [v for v in range(5, hi + 1, 5) if v >= max(5, lo - 2)]
    while True:
        values = [rng.choice(mult) for _ in range(k)]
        diffs = [values[i + 1] - values[i] for i in range(k - 1)]
        if (values.count(max(values)) == 1 and values.count(min(values)) == 1
                and max(diffs) > 0 and diffs.count(max(diffs)) == 1):
            break
    ymax = math.ceil((max(values) + 2) / 5) * 5
    img, d = gb.canvas(title, rng.choice(SUBTITLES))
    left, top, right, bottom = 150, 180, 1020, 620
    grid_axes(d, left, top, right, bottom, ymax, ylabel)
    pts = []
    for i, v in enumerate(values):
        x = left + 60 + i * (right - left - 120) / (k - 1)
        pts.append((x, bottom - v / ymax * (bottom - top)))
        d.text((x, bottom + 28), cats[i], font=gb.font(24), fill="black", anchor="mm")
    color = rng.choice(PALETTE_BAR)
    d.line(pts, fill=color, width=rng.choice([4, 5, 6]), joint="curve")
    for (x, y), v in zip(pts, values):
        d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=color, outline="white", width=2)
        if labeled:
            d.text((x, y - 26), str(v), font=gb.font(26), fill="black", anchor="mm")
    t = gb.Truth("", "line_chart", title)
    t.d["data"] = {"points": dict(zip(cats, values)), "unit": unit, "y_axis_step": 5,
                   "has_value_labels": labeled}
    for c, v in zip(cats, values):
        t.prop("value", f"Điểm {c}", "có giá trị", f"{v} {unit}")
    hi_c, lo_c = cats[values.index(max(values))], cats[values.index(min(values))]
    trend = "tăng" if values[-1] > values[0] else "giảm" if values[-1] < values[0] else "không đổi"
    j = diffs.index(max(diffs))
    t.prop("comparison", "Giá trị cao nhất", "xuất hiện tại", hi_c)
    t.prop("comparison", "Giá trị thấp nhất", "xuất hiện tại", lo_c)
    t.prop("comparison", f"Từ {cats[0]} đến {cats[-1]}", "xu hướng chung là", trend)
    t.prop("comparison", "Mức tăng lớn nhất giữa hai điểm liên tiếp", "xảy ra từ",
           f"{cats[j]} đến {cats[j + 1]} (tăng {max(diffs)} {unit})")
    listing = "; ".join(f"{c}: {su(v, unit)}" for c, v in zip(cats, values))
    lead = ("Số ghi tại các điểm lần lượt là: " if labeled else
            "Trên biểu đồ không ghi số, các giá trị dưới đây được đọc theo vạch chia ở trục đứng: ")
    trend_s = {"tăng": "Nhìn chung, giá trị tăng", "giảm": "Nhìn chung, giá trị giảm",
               "không đổi": "Nhìn chung, giá trị gần như không đổi"}[trend]
    desc = " ".join([
        f"Trang có một biểu đồ đường về {lf(title)}.",
        f"Đường đi qua {sn(k)} mốc: {join_vi(cats)}.",
        f"{trend_s} từ {cats[0]} đến {cats[-1]}.",
        f"Cao nhất ở {hi_c}, {su(max(values), unit)}. Thấp nhất ở {lo_c}, {su(min(values), unit)}.",
        f"Từ {cats[j]} sang {cats[j + 1]}, giá trị tăng nhiều nhất, thêm {su(max(diffs), unit)}.",
        lead + listing + ".", rng.choice(ENDINGS)])
    qa = []
    add_qa(t, qa, "Giá trị cao nhất xuất hiện ở đâu?", hi_c,
           f"Cao nhất ở {hi_c}, {su(max(values), unit)}.", "comparison")
    add_qa(t, qa, f"Giá trị tại {cats[0]} là bao nhiêu?", f"{values[0]} {unit}",
           f"Tại {cats[0]} là {su(values[0], unit)}.", "lookup")
    add_qa(t, qa, "Giữa hai điểm liên tiếp nào giá trị tăng nhiều nhất?", f"{cats[j]} đến {cats[j + 1]}",
           f"Từ {cats[j]} sang {cats[j + 1]}, tăng {su(max(diffs), unit)}.", "comparison")
    return sample("line_chart", img, t, desc, qa)


# --------------------------------------------------------------------------- biểu đồ tròn

def gen_pie(rng):
    title, names = rng.choice(T.PIE_THEMES)
    names = rng.sample(names, rng.randint(3, len(names)))
    k = len(names)
    while True:
        units = [2] * k
        for _ in range(20 - 2 * k):
            units[rng.randrange(k)] += 1
        if units.count(max(units)) == 1 and units.count(min(units)) == 1:
            break
    pct = [u * 5 for u in units]
    img, d = gb.canvas(title, rng.choice(SUBTITLES))
    cx, cy, r = 360, 420, 230
    start = -90.0
    colors = rng.sample(gb.PALETTE, k) if k <= len(gb.PALETTE) else gb.PALETTE
    for i, p in enumerate(pct):
        end = start + p * 3.6
        d.pieslice((cx - r, cy - r, cx + r, cy + r), start, end, fill=colors[i % len(colors)],
                   outline="#444444", width=3)
        mid = math.radians((start + end) / 2)
        d.text((cx + r * 0.65 * math.cos(mid), cy + r * 0.65 * math.sin(mid)), f"{p}%",
               font=gb.font(28, True), fill="black", anchor="mm")
        start = end
    for i, name in enumerate(names):
        y = 250 + i * 72
        d.rectangle((690, y - 20, 730, y + 20), fill=colors[i % len(colors)], outline="#444444", width=2)
        d.text((750, y), name, font=gb.font(29), fill="black", anchor="lm")
    t = gb.Truth("", "pie_chart", title)
    t.d["data"] = {"percentages": dict(zip(names, pct)), "slice_order":
                   "bắt đầu từ đỉnh (12 giờ), theo chiều kim đồng hồ, cùng thứ tự chú thích"}
    for n, p in zip(names, pct):
        t.prop("value", f"Phần {n}", "chiếm", f"{p}%")
    hi_c, lo_c = names[pct.index(max(pct))], names[pct.index(min(pct))]
    t.prop("comparison", "Phần lớn nhất", "là", hi_c)
    t.prop("comparison", "Phần nhỏ nhất", "là", lo_c)
    t.prop("structure", "Tổng các phần", "bằng", "100%", critical=False)
    listing = "; ".join(f"{n}: {su(p, '%')}" for n, p in zip(names, pct))
    desc = " ".join([
        f"Trang có một biểu đồ tròn về {lf(title)}.",
        f"Biểu đồ chia thành {sn(k)} phần: {join_vi(names)}.",
        f"Phần {hi_c} chiếm nhiều nhất, {su(max(pct), '%')}. Phần {lo_c} chiếm ít nhất, {su(min(pct), '%')}.",
        f"Các phần lần lượt là: {listing}. Tổng các phần là một trăm phần trăm.", rng.choice(ENDINGS)])
    top2 = sorted(zip(pct, names), reverse=True)[:2]
    qa = []
    add_qa(t, qa, "Phần nào chiếm tỉ lệ lớn nhất?", hi_c, f"Phần {hi_c} lớn nhất, {su(max(pct), '%')}.",
           "comparison")
    add_qa(t, qa, f"Phần {names[0]} chiếm bao nhiêu phần trăm?", f"{pct[0]}%",
           f"Phần {names[0]} chiếm {su(pct[0], '%')}.", "lookup")
    add_qa(t, qa, f"Hai phần {top2[0][1]} và {top2[1][1]} cộng lại chiếm bao nhiêu phần trăm?",
           f"{top2[0][0] + top2[1][0]}%", f"Cộng lại là {su(top2[0][0] + top2[1][0], '%')}.", "computation")
    return sample("pie_chart", img, t, desc, qa)


# --------------------------------------------------------------------------- bảng số liệu

def gen_table(rng):
    title, corner, rkey, cols, kind, lo, hi, unit = rng.choice(T.TABLE_SCHEMAS)
    rows = pick_cats(rng, rkey, rng.randint(3, 5))
    ncols = rng.randint(min(2, len(cols)), len(cols))
    cols = sorted(rng.sample(cols, ncols), key=cols.index)
    if kind == "dec":
        cell = lambda: rng.choice([x / 2 for x in range(int(lo * 2), int(hi * 2) + 1)])  # noqa: E731
    else:
        cell = lambda: rng.randint(lo, hi)  # noqa: E731
    data = [[cell() for _ in cols] for _ in rows]
    img, d = gb.canvas(title, None)
    first_w = 230
    col_w = min(190, (900 - first_w) / len(cols))
    x0, y0, rh = (W - (first_w + col_w * len(cols))) / 2, 150, 72
    for r in range(len(rows) + 1):
        for c in range(len(cols) + 1):
            xa = x0 + (0 if c == 0 else first_w + col_w * (c - 1))
            xb = x0 + first_w + col_w * c
            ya, yb = y0 + r * rh, y0 + (r + 1) * rh
            d.rectangle((xa, ya, xb, yb), fill="#e6e6e6" if (r == 0 or c == 0) else "white",
                        outline="#333333", width=3)
            label = (corner if (r == 0 and c == 0) else cols[c - 1] if r == 0 else rows[r - 1] if c == 0
                     else fmt(data[r - 1][c - 1]))
            gb.text_in_box(d, (xa + xb) / 2, (ya + yb) / 2, label, (xb - xa) - 14, 26, bold=(r == 0 or c == 0))
    t = gb.Truth("", "table", title)
    t.d["data"] = {"row_labels": rows, "column_labels": cols, "rows": data}
    for rname, rvals in zip(rows, data):
        for cname, v in zip(cols, rvals):
            t.prop("value", f"{rname} – {cname}", "có giá trị", fmt(v))
    uniq_max = []
    for ci, cname in enumerate(cols):
        colv = [r[ci] for r in data]
        if colv.count(max(colv)) == 1:
            uniq_max.append((ci, cname, rows[colv.index(max(colv))], max(colv)))
            t.prop("comparison", f"Giá trị lớn nhất của cột {cname}", "thuộc về", rows[colv.index(max(colv))])
    stmts = [f"Ở cột {cn}, giá trị lớn nhất là {su(v, unit)} ở hàng {rn}." for _, cn, rn, v in uniq_max[:2]]
    desc = " ".join([
        f"Trang có một bảng số liệu về {lf(title)}.",
        f"Bảng có {sn(len(rows))} hàng và {sn(len(cols) + 1)} cột.",
        f"Cột đầu ghi {lf(corner)}, gồm: {join_vi(rows)}.",
        f"Các cột còn lại là: {join_vi(cols)}.", *stmts, "Bạn muốn nghe số liệu hàng nào?"])
    qa = []
    for _ in range(3):
        ri, ci = rng.randrange(len(rows)), rng.randrange(len(cols))
        add_qa(t, qa, f"{rows[ri]} – {cols[ci]} có giá trị là bao nhiêu?", fmt(data[ri][ci]),
               f"{rows[ri]}, {cols[ci]}: {su(data[ri][ci], unit)}.", "lookup")
    if uniq_max:
        ci, cn, rn, _v = uniq_max[-1]
        add_qa(t, qa, f"Ở cột {cn}, hàng nào có giá trị lớn nhất?", rn, f"Hàng {rn}.", "comparison")
    total = round(sum(data[0]), 1)
    add_qa(t, qa, f"Tổng các giá trị của hàng {rows[0]} là bao nhiêu?", fmt(total),
           f"Tổng là {su(total, unit)}.", "computation")
    return sample("table", img, t, desc, qa)


# --------------------------------------------------------------------------- sơ đồ khối

def render_flow(title, nodes, edges, extra, questions):
    img, d = gb.canvas(title, None)
    byid = {n["id"]: n for n in nodes}
    for n in nodes:
        gb.draw_node(d, n)
    t = gb.Truth("", "flow_diagram", title)
    t.d["data"] = {"nodes": [n["text"] for n in nodes],
                   "edges": [{"from": byid[e[0]]["text"], "to": byid[e[1]]["text"],
                              "label": e[2] if len(e) > 2 else None} for e in edges]}
    for e in edges:
        src, dst = byid[e[0]], byid[e[1]]
        label = e[2] if len(e) > 2 else None
        via = e[3] if len(e) > 3 else None
        pts = ([gb.boundary_point(src, via[0]), *via, gb.boundary_point(dst, via[-1])] if via
               else [gb.boundary_point(src, dst["pos"]), gb.boundary_point(dst, src["pos"])])
        gb.polyline_arrow(d, pts)
        t.prop("relation", src["text"], "dẫn đến" if not label else f"dẫn đến khi câu trả lời là '{label}'",
               dst["text"])
        if label:
            (x0, y0), (x1, y1) = pts[0], pts[1]
            ln = math.hypot(x1 - x0, y1 - y0) or 1
            d.text(((x0 + x1) / 2 + (y1 - y0) / ln * 26, (y0 + y1) / 2 - (x1 - x0) / ln * 26), label,
                   font=gb.font(25, True), fill="#8a1c1c", anchor="mm")
    for kind, s, p, o in extra:
        t.prop(kind, s, p, o)
    qa = []
    for q, a, ty, sp in questions:
        add_qa(t, qa, q, a, sp, ty)
    return img, t, qa


def gen_flow(rng):
    layout = rng.choice(["chain_h", "chain_v", "branch", "side", "loop"])
    proc = rng.random() < 0.6  # sinh theo thủ tục để không gian nội dung đủ lớn
    N = gb.N
    if layout in ("chain_h", "chain_v"):
        title, steps = T.proc_chain(rng) if proc else rng.choice(T.CHAINS)
        n = len(steps)
        if layout == "chain_h":
            w = 150 if n >= 5 else 170
            nodes = [N(str(i), s, "box", (110 + i * 880 / (n - 1), 360), (w, 90)) for i, s in enumerate(steps)]
            how, order = "từ trái sang phải", "trái sang phải"
        else:
            nodes = [N(str(i), s, "box", (550, 170 + i * 430 / (n - 1)), (320, 70)) for i, s in enumerate(steps)]
            how, order = "từ trên xuống dưới", "trên xuống dưới"
        edges = [(str(i), str(i + 1)) for i in range(n - 1)]
        extra = [("structure", "Sơ đồ", "đi theo hướng", order), ("structure", "Bước đầu tiên", "là", steps[0]),
                 ("structure", "Bước cuối cùng", "là", steps[-1])]
        questions = [(f"Sau bước {steps[1]} là bước nào?", steps[2], "relation",
                      f"Sau {steps[1]} là {steps[2]}."),
                     ("Quy trình có tất cả bao nhiêu bước?", str(n), "lookup", f"Có {sn(n)} bước.")]
        mid = ", ".join(f"rồi {s}" for s in steps[1:-1])
        desc = " ".join([f"Trang có một sơ đồ về {lf(title)}.", f"Sơ đồ có {sn(n)} bước, đi {how}.",
                         f"Bước đầu là {steps[0]}, {mid}.", f"Bước cuối cùng là {steps[-1]}.", rng.choice(ENDINGS)])
    elif layout == "branch":
        title, start, q, yes, no, end = T.proc_branch(rng) if proc else rng.choice(T.BRANCHES)
        nodes = [N("s", start, "oval", (550, 160), (170, 70)), N("q", q, "diamond", (550, 310), (260, 130)),
                 N("y", yes, "box", (230, 490), (200, 80)), N("n", no, "box", (870, 490), (200, 80)),
                 N("e", end, "oval", (550, 640), (170, 70))]
        edges = [("s", "q"), ("q", "y", "Có"), ("q", "n", "Không"), ("y", "e"), ("n", "e")]
        extra = [("structure", "Sơ đồ", "có", f"một điểm rẽ nhánh tại '{q}'")]
        questions = [(f"Nếu câu trả lời là có thì làm gì?", yes, "relation", f"Thì {lf(yes)}."),
                     (f"Nếu câu trả lời là không thì làm gì?", no, "relation", f"Thì {lf(no)}."),
                     ("Hai nhánh gặp lại nhau ở bước nào?", end, "relation", f"Ở bước {lf(end)}.")]
        desc = " ".join([f"Trang có một sơ đồ về {lf(title)}.", f"Sơ đồ mở đầu bằng ô {start}, rồi tới câu hỏi: {q}",
                         f"Nếu có thì {lf(yes)}. Nếu không thì {lf(no)}.",
                         f"Cả hai nhánh đều dẫn tới bước cuối là {lf(end)}.", rng.choice(ENDINGS)])
    elif layout == "side":
        title, start, common, q, yes, no = T.proc_side(rng) if proc else rng.choice(T.SIDES)
        nodes = [N("s", start, "oval", (550, 150), (170, 64)), N("m", common, "box", (550, 270), (220, 70)),
                 N("q", q, "diamond", (550, 440), (340, 150)), N("y", yes, "box", (900, 440), (200, 80)),
                 N("n", no, "box", (550, 630), (200, 70))]
        edges = [("s", "m"), ("m", "q"), ("q", "y", "Có"), ("q", "n", "Không")]
        extra = [("structure", "Sơ đồ", "có", f"một điểm rẽ nhánh tại '{q}'")]
        questions = [("Nếu câu trả lời là có thì làm gì?", yes, "relation", f"Thì {lf(yes)}."),
                     ("Nếu câu trả lời là không thì làm gì?", no, "relation", f"Thì {lf(no)}.")]
        desc = " ".join([f"Trang có một sơ đồ về {lf(title)}.", f"Sơ đồ mở đầu bằng ô {start}, rồi bước {lf(common)}.",
                         f"Sau đó có câu hỏi: {q}", f"Nếu có thì {lf(yes)}, ở nhánh bên phải.",
                         f"Nếu không thì {lf(no)}, ở nhánh bên dưới.", rng.choice(ENDINGS)])
    else:
        title, a, b, q, c = T.proc_loop(rng) if proc else rng.choice(T.LOOPS)
        nodes = [N("a", a, "box", (130, 330), (160, 90)), N("b", b, "box", (390, 330), (160, 90)),
                 N("q", q, "diamond", (680, 330), (220, 130)), N("c", c, "box", (960, 330), (160, 90))]
        edges = [("a", "b"), ("b", "q"), ("q", "c", "Có"), ("q", "b", "Không", [(680, 520), (390, 520)])]
        extra = [("structure", "Sơ đồ", "có", f"một vòng lặp: nếu chưa thì quay lại bước '{b}'")]
        questions = [(f"Nếu câu trả lời là không thì quay lại bước nào?", b, "relation", f"Quay lại bước {lf(b)}."),
                     (f"Nếu câu trả lời là có thì làm gì tiếp theo?", c, "relation", f"Thì {lf(c)}.")]
        desc = " ".join([f"Trang có một sơ đồ về {lf(title)}.", f"Sơ đồ có hai bước đầu là {lf(a)} và {lf(b)}.",
                         f"Sau đó có câu hỏi: {q}", f"Nếu có thì {lf(c)}.",
                         f"Nếu không thì quay lại bước {lf(b)}, tạo thành một vòng lặp.", rng.choice(ENDINGS)])
    img, t, qa = render_flow(title, nodes, edges, extra, questions)
    return sample("flow_diagram", img, t, desc, qa)


# --------------------------------------------------------------------------- sơ đồ vòng

def gen_cycle(rng):
    title, stages = T.proc_cycle(rng) if rng.random() < 0.6 else rng.choice(T.CYCLES)
    k = len(stages)
    clockwise = rng.random() < 0.6
    img, d = gb.canvas(title, None)
    cx, cy, rx, ry = 550, 405, 340, 225
    sign = 1 if clockwise else -1
    nodes = []
    for i, text in enumerate(stages):
        ang = math.radians(-90 + sign * i * 360 / k)
        nodes.append({"text": text, "shape": "box", "pos": (cx + rx * math.cos(ang), cy + ry * math.sin(ang)),
                      "size": (250, 104)})
    for i in range(k):
        a, b = nodes[i], nodes[(i + 1) % k]
        gb.arrow(d, gb.boundary_point(a, b["pos"]), gb.boundary_point(b, a["pos"]), width=5, head=20)
    for nd in nodes:
        gb.draw_node(d, nd)
    direction = "cùng chiều kim đồng hồ" if clockwise else "ngược chiều kim đồng hồ"
    t = gb.Truth("", "cycle_diagram", title)
    t.d["data"] = {"stages_in_order": stages, "arrow_direction": direction}
    for i in range(k):
        t.prop("relation", stages[i], "dẫn đến", stages[(i + 1) % k])
    t.prop("structure", "Chiều các mũi tên", "là", direction)
    t.prop("structure", "Sơ đồ", "là", "một chu trình khép kín, không có điểm kết thúc")
    desc = " ".join([
        f"Trang có một sơ đồ vòng về {lf(title)}.",
        f"Sơ đồ có {sn(k)} giai đoạn nối thành một vòng khép kín, các mũi tên đi {direction}.",
        f"Bắt đầu từ giai đoạn {lf(stages[0])}" + "".join(f", rồi {lf(s)}" for s in stages[1:]) +
        f", cuối cùng quay lại giai đoạn {lf(stages[0])}.", rng.choice(ENDINGS)])
    qa = []
    add_qa(t, qa, f"Sau '{stages[0]}' là giai đoạn nào?", stages[1], f"Sau đó là {lf(stages[1])}.", "relation")
    add_qa(t, qa, f"Sau '{stages[-1]}' là giai đoạn nào?", stages[0], f"Quay lại {lf(stages[0])}.", "relation")
    add_qa(t, qa, "Các mũi tên đi theo chiều nào?", direction, f"Các mũi tên đi {direction}.", "relation")
    return sample("cycle_diagram", img, t, desc, qa)


# --------------------------------------------------------------------------- hình học

TRIPLES = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (9, 12, 15), (7, 24, 25), (12, 16, 20)]
TRI_LETTERS = [("M", "N", "P"), ("D", "E", "F"), ("X", "Y", "Z"), ("H", "K", "L"), ("A", "B", "C")]
RECT_LETTERS = ["MNPQ", "EFGH", "KLMN", "ABCD"]


def gen_geometry(rng):
    kind = rng.choice(["right", "rect", "square", "circle", "angles"])
    qa = []
    if kind == "right":
        a, b, c = rng.choice(TRIPLES)
        if rng.random() < 0.5:
            a, b = b, a
        P, Q, R = rng.choice(TRI_LETTERS)  # P là đỉnh góc vuông
        title = f"Tam giác {P}{Q}{R} vuông tại {P}"
        img, d = gb.canvas(title, None)
        mirror = rng.random() < 0.5
        s = 380 / max(a, b)
        px, py = (780, 590) if mirror else (330, 590)
        A_, B_ = (px, py), (px, py - a * s)
        C_ = (px - b * s, py) if mirror else (px + b * s, py)
        d.polygon([A_, B_, C_], fill="#eaf3fb", outline="#2b5d8a")
        d.line([A_, B_, C_, A_], fill="#2b5d8a", width=5)
        m = 30
        d.rectangle((px - m, py - m, px, py) if mirror else (px, py - m, px + m, py), outline="#2b5d8a", width=4)
        cen = ((A_[0] + B_[0] + C_[0]) / 3, (A_[1] + B_[1] + C_[1]) / 3)
        for p, tx in ((A_, P), (B_, Q), (C_, R)):
            gb.vertex_label(d, p, cen, tx)
        gb.side_label(d, A_, B_, cen, f"{P}{Q} = {a} cm")
        gb.side_label(d, A_, C_, cen, f"{P}{R} = {b} cm")
        t = gb.Truth("", "geometry", title)
        t.d["data"] = {"AB_cm": a, "AC_cm": b, "BC_cm": c, "right_angle_at": P, "BC_shown_in_image": False}
        t.prop("structure", f"Tam giác {P}{Q}{R}", "là tam giác", f"vuông tại {P}")
        t.prop("value", f"Cạnh {P}{Q}", "dài", f"{a} cm")
        t.prop("value", f"Cạnh {P}{R}", "dài", f"{b} cm")
        t.prop("inference", f"Cạnh huyền {Q}{R}", "dài", f"{c} cm", critical=False)
        t.prop("inference", f"Diện tích tam giác {P}{Q}{R}", "bằng", f"{a * b // 2} cm²", critical=False)
        desc = " ".join([f"Trang có một hình tam giác {P} {Q} {R} vuông tại đỉnh {P}, có ô vuông nhỏ ở góc vuông.",
                         f"Cạnh {P} {Q} dài {su(a, 'cm')}. Cạnh {P} {R} dài {su(b, 'cm')}.",
                         f"Cạnh huyền {Q} {R} không ghi số trên hình, tính được là {su(c, 'cm')}.",
                         rng.choice(ENDINGS)])
        add_qa(t, qa, f"Tam giác {P}{Q}{R} vuông tại đỉnh nào?", P, f"Vuông tại đỉnh {P}.", "lookup")
        add_qa(t, qa, f"Cạnh huyền {Q}{R} dài bao nhiêu xăng-ti-mét?", f"{c} cm",
               f"Cạnh huyền dài {su(c, 'cm')}.", "computation")
        add_qa(t, qa, f"Diện tích tam giác {P}{Q}{R} là bao nhiêu?", f"{a * b // 2} cm²",
               f"Diện tích là {su(a * b // 2, 'cm²')}.", "computation")
    elif kind in ("rect", "square"):
        L = rng.choice(RECT_LETTERS)
        w_, h_ = (rng.randint(3, 12), rng.randint(2, 9)) if kind == "rect" else (lambda v: (v, v))(rng.randint(3, 9))
        if kind == "rect" and w_ == h_:
            h_ -= 1
        what = "chữ nhật" if kind == "rect" else "vuông"
        title = f"Hình {what} {L}"
        img, d = gb.canvas(title, None)
        s = min(55, 420 / w_, 300 / h_)
        x0, y0 = 550 - w_ * s / 2, 400 - h_ * s / 2
        Aa, Bb = (x0, y0 + h_ * s), (x0 + w_ * s, y0 + h_ * s)
        Cc, Dd = (x0 + w_ * s, y0), (x0, y0)
        d.rectangle((Dd[0], Dd[1], Bb[0], Bb[1]), fill="#eaf3fb", outline="#2b5d8a", width=5)
        m = 24
        for (px, py, sx, sy) in ((Aa[0], Aa[1], 1, -1), (Bb[0], Bb[1], -1, -1), (Cc[0], Cc[1], -1, 1),
                                 (Dd[0], Dd[1], 1, 1)):
            d.rectangle((min(px, px + sx * m), min(py, py + sy * m), max(px, px + sx * m), max(py, py + sy * m)),
                        outline="#2b5d8a", width=3)
        cen = (550, 400)
        for p, tx in ((Aa, L[0]), (Bb, L[1]), (Cc, L[2]), (Dd, L[3])):
            gb.vertex_label(d, p, cen, tx)
        gb.side_label(d, Aa, Bb, cen, f"{L[0]}{L[1]} = {w_} cm")
        if kind == "rect":
            gb.side_label(d, Bb, Cc, cen, f"{L[1]}{L[2]} = {h_} cm")
        t = gb.Truth("", "geometry", title)
        t.d["data"] = {"AB_cm": w_, "BC_cm": h_}
        t.prop("structure", f"Tứ giác {L}", "là", f"hình {what} (bốn góc vuông)")
        t.prop("value", f"Cạnh {L[0]}{L[1]}", "dài", f"{w_} cm")
        if kind == "rect":
            t.prop("value", f"Cạnh {L[1]}{L[2]}", "dài", f"{h_} cm")
        t.prop("inference", f"Diện tích hình {what} {L}", "bằng", f"{w_ * h_} cm²", critical=False)
        t.prop("inference", f"Chu vi hình {what} {L}", "bằng", f"{2 * (w_ + h_)} cm", critical=False)
        extra = (f"Cạnh {L[1]} {L[2]} dài {su(h_, 'cm')}." if kind == "rect"
                 else "Bốn cạnh bằng nhau.")
        desc = " ".join([f"Trang có một hình {what} {' '.join(L)} với bốn góc vuông.",
                         f"Cạnh {L[0]} {L[1]} dài {su(w_, 'cm')}.", extra, rng.choice(ENDINGS)])
        add_qa(t, qa, f"Diện tích hình {what} {L} là bao nhiêu?", f"{w_ * h_} cm²",
               f"Diện tích là {su(w_ * h_, 'cm²')}.", "computation")
        add_qa(t, qa, f"Chu vi hình {what} {L} là bao nhiêu?", f"{2 * (w_ + h_)} cm",
               f"Chu vi là {su(2 * (w_ + h_), 'cm')}.", "computation")
    elif kind == "circle":
        r_cm = rng.randint(2, 12)
        O = rng.choice(["O", "I", "K"])
        title = f"Đường tròn tâm {O}"
        img, d = gb.canvas(title, None)
        cx, cy, rp = 550, 410, 100 + 10 * r_cm
        d.ellipse((cx - rp, cy - rp, cx + rp, cy + rp), fill="#eaf3fb", outline="#2b5d8a", width=5)
        ang = math.radians(rng.choice([-30, -60, 20, 150, 210]))
        P_ = (cx + rp * math.cos(ang), cy + rp * math.sin(ang))
        d.line([(cx, cy), P_], fill="#8a1c1c", width=5)
        d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill="black")
        d.text((cx - 26, cy + 24), O, font=gb.font(30, True), fill="black", anchor="mm")
        d.text((cx + rp * 0.5 * math.cos(ang) - 10, cy + rp * 0.5 * math.sin(ang) - 36), f"r = {r_cm} cm",
               font=gb.font(28), fill="#8a1c1c", anchor="mm")
        t = gb.Truth("", "geometry", title)
        t.d["data"] = {"radius_cm": r_cm}
        t.prop("structure", f"Điểm {O}", "là", "tâm của đường tròn")
        t.prop("value", "Bán kính của đường tròn", "bằng", f"{r_cm} cm")
        t.prop("inference", "Đường kính của đường tròn", "bằng", f"{2 * r_cm} cm", critical=False)
        desc = " ".join([f"Trang có một hình tròn tâm {O}.", f"Bán kính ghi trên hình là {su(r_cm, 'cm')}.",
                         f"Đường kính gấp đôi bán kính, tức là {su(2 * r_cm, 'cm')}.", rng.choice(ENDINGS)])
        add_qa(t, qa, "Bán kính của đường tròn là bao nhiêu?", f"{r_cm} cm", f"Bán kính là {su(r_cm, 'cm')}.", "lookup")
        add_qa(t, qa, "Đường kính của đường tròn là bao nhiêu?", f"{2 * r_cm} cm",
               f"Đường kính là {su(2 * r_cm, 'cm')}.", "computation")
    else:
        while True:
            alpha, beta = rng.randint(30, 80), rng.randint(30, 80)
            gamma = 180 - alpha - beta
            if 30 <= gamma <= 100:
                break
        P, Q, R = rng.choice(TRI_LETTERS)
        title = f"Tam giác {P}{Q}{R} với hai góc cho trước"
        img, d = gb.canvas(title, None)
        Lb = 440
        A_ = (330, 590)
        B_ = (A_[0] + Lb, A_[1])
        AC = Lb * math.sin(math.radians(beta)) / math.sin(math.radians(gamma))
        C_ = (A_[0] + AC * math.cos(math.radians(alpha)), A_[1] - AC * math.sin(math.radians(alpha)))
        d.polygon([A_, B_, C_], fill="#eaf3fb")
        d.line([A_, B_, C_, A_], fill="#2b5d8a", width=5)
        cen = ((A_[0] + B_[0] + C_[0]) / 3, (A_[1] + B_[1] + C_[1]) / 3)
        for p, tx in ((A_, P), (B_, Q), (C_, R)):
            gb.vertex_label(d, p, cen, tx)
        for p, tx in ((A_, f"{alpha}°"), (B_, f"{beta}°"), (C_, "?")):
            d.text((p[0] + (cen[0] - p[0]) * 0.3, p[1] + (cen[1] - p[1]) * 0.3), tx, font=gb.font(30, True),
                   fill="#8a1c1c", anchor="mm")
        t = gb.Truth("", "geometry", title)
        t.d["data"] = {"angle_A": alpha, "angle_B": beta, "angle_C": gamma}
        t.prop("value", f"Góc {P}", "có số đo", f"{alpha}°")
        t.prop("value", f"Góc {Q}", "có số đo", f"{beta}°")
        t.prop("structure", f"Góc {R}", "chưa biết số đo (đánh dấu '?')", "cần tính")
        t.prop("inference", f"Góc {R}", "có số đo", f"{gamma}°", critical=False)
        desc = " ".join([f"Trang có một hình tam giác {P} {Q} {R}.", f"Góc {P} là {su(alpha, '°')}. Góc {Q} là {su(beta, '°')}.",
                         f"Góc {R} chưa biết, hình đánh dấu một dấu hỏi. Tổng ba góc là một trăm tám mươi độ, "
                         f"nên góc {R} là {su(gamma, '°')}.", rng.choice(ENDINGS)])
        add_qa(t, qa, f"Góc {P} có số đo bao nhiêu độ?", f"{alpha}°", f"Góc {P} là {su(alpha, '°')}.", "lookup")
        add_qa(t, qa, f"Góc {R} có số đo bao nhiêu độ?", f"{gamma}°", f"Góc {R} là {su(gamma, '°')}.", "computation")
    return sample("geometry", img, t, desc, qa)


# --------------------------------------------------------------------------- sơ đồ bản đồ

def gen_map(rng):
    title = rng.choice(T.MAP_TITLES)
    places = rng.sample(T.MAP_PLACES, 5)
    cells = rng.sample(range(9), 5)
    ref = places[0]
    img, d = gb.canvas(title, "Hướng Bắc ở phía trên của sơ đồ")
    for y in (310, 490):
        d.line((110, y, 990, y), fill="#d4d4d4", width=22)
    for x in (400, 700):
        d.line((x, 140, x, 660), fill="#d4d4d4", width=22)
    pos = {}
    for name, cell in zip(places, cells):
        r, c = divmod(cell, 3)
        pos[name] = (r, c)
        px, py = gb.CELL_X[c], gb.CELL_Y[r]
        d.rounded_rectangle((px - 100, py - 36, px + 100, py + 36), radius=12,
                            fill="#ffe9b8" if name == ref else "#e8f1fb", outline="#2b5d8a", width=3)
        gb.text_in_box(d, px, py, name, 180, 25, True)
    gb.arrow(d, (1020, 215), (1020, 135), width=5, head=20)
    d.text((1020, 112), "Bắc", font=gb.font(26, True), fill="black", anchor="mm")
    t = gb.Truth("", "schematic_map", title)
    t.d["data"] = {"north_is_up": True, "grid_cell_(row,col)": {k: list(v) for k, v in pos.items()}}
    t.prop("structure", "Hướng Bắc", "nằm ở", "phía trên của sơ đồ")
    t.prop("structure", "Số địa điểm được đánh dấu", "là", "5")
    qa, rel = [], []
    for name in places[1:]:
        dr, dc = pos[name][0] - pos[ref][0], pos[name][1] - pos[ref][1]
        dirn = gb.direction(dr, dc)
        t.prop("relation", name, "nằm ở", f"phía {dirn} của {ref}")
        rel.append(f"{name} ở phía {dirn.lower()}")
        add_qa(t, qa, f"{name} nằm ở hướng nào so với {ref}?", dirn, f"Ở phía {dirn.lower()}.", "relation")
    what = re.sub(r"^[Ss]ơ đồ ", "", title)
    desc = " ".join([f"Trang có một sơ đồ {what}. Hướng Bắc ở phía trên.",
                     f"Sơ đồ có {sn(5)} địa điểm: {join_vi(places)}.",
                     f"Lấy {ref} làm mốc: " + "; ".join(rel) + ".", rng.choice(ENDINGS)])
    return sample("schematic_map", img, t, desc, qa)


GENERATORS = {"bar_chart": gen_bar, "line_chart": gen_line, "pie_chart": gen_pie, "table": gen_table,
              "flow_diagram": gen_flow, "cycle_diagram": gen_cycle, "geometry": gen_geometry,
              "schematic_map": gen_map}


# --------------------------------------------------------------------------- nhiễu ảnh chụp

def _noise(img, rng, amount):
    n = Image.frombytes("L", img.size, rng.randbytes(img.size[0] * img.size[1])).convert("RGB")
    return Image.blend(img, n, amount)


def mild_augment(img, rng):
    if rng.random() < 0.5:
        s = rng.uniform(0.82, 0.96)
        bg = tuple(rng.randint(205, 245) for _ in range(3))
        small = img.resize((int(W * s), int(H * s)), Image.BICUBIC)
        canvas = Image.new("RGB", (W, H), bg)
        canvas.paste(small, (rng.randint(0, W - small.width), rng.randint(0, H - small.height)))
        img = canvas
    img = img.rotate(rng.uniform(-6, 6), resample=Image.BICUBIC, fillcolor=(235, 235, 235))
    px, py = rng.uniform(-2e-4, 2e-4), rng.uniform(-2e-4, 2e-4)
    sx, sy = rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04)
    img = img.transform(img.size, Image.PERSPECTIVE, (1, sx, 0, sy, 1, 0, px, py), Image.BILINEAR,
                        fillcolor=(235, 235, 235))
    img = ImageEnhance.Brightness(img).enhance(rng.uniform(0.65, 1.1))
    img = ImageEnhance.Contrast(img).enhance(rng.uniform(0.8, 1.05))
    img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0, 1.2)))
    return _noise(img, rng, rng.uniform(0, 0.1))


ISSUES = ["blur", "dark", "glare", "cropped_left", "cropped_right", "cropped_top", "cropped_bottom"]


def issue_augment(img, rng, kind):
    if kind == "blur":
        f = rng.randint(28, 40)
        img = img.resize((W // f, H // f), Image.BILINEAR).resize((W, H), Image.BILINEAR)
        return ImageEnhance.Brightness(img.filter(ImageFilter.GaussianBlur(6))).enhance(0.55)
    if kind == "dark":
        return _noise(ImageEnhance.Brightness(img).enhance(rng.uniform(0.012, 0.03)), rng, 0.10)
    if kind == "glare":
        mask = Image.new("L", (W, H), 0)
        cx, cy = rng.randint(350, 750), rng.randint(260, 460)
        rx, ry = rng.randint(380, 520), rng.randint(260, 360)
        ImageDraw.Draw(mask).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(45)).point(lambda v: min(255, int(v * 1.25)))
        return Image.composite(Image.new("RGB", (W, H), (255, 255, 250)), img, mask)
    frac = rng.uniform(0.4, 0.5)
    box = {"cropped_left": (int(W * frac), 0, W, H), "cropped_right": (0, 0, int(W * (1 - frac)), H),
           "cropped_top": (0, int(H * frac), W, H), "cropped_bottom": (0, 0, W, int(H * (1 - frac)))}[kind]
    return img.crop(box)


def finalize_jpeg(img, rng):
    """Vòng JPEG như đường ống backend (chuyển sang JPEG, cạnh dài tối đa 1600)."""
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=rng.randint(82, 95))
    return buf.getvalue()


# --------------------------------------------------------------------------- tạo mẫu

def signature(category, title, data):
    return f"{category}|{title}|{json.dumps(data, ensure_ascii=False, sort_keys=True)}"


def load_bench_index(bench_dir):
    """Tiêu đề, chữ ký dữ liệu và hash ảnh của benchmark cục bộ (nếu có) để đảm bảo không trùng."""
    titles, sigs, hashes = set(T.FORBIDDEN_TITLES), set(), set()
    bench_dir = Path(bench_dir)
    for tp in list((bench_dir / "synthetic").glob("*_truth.json")) + list((bench_dir / "textbook" / "truth").glob("*_truth.json")):
        try:
            tr = json.loads(tp.read_text(encoding="utf-8"))
        except ValueError:
            continue
        titles.add(tr.get("title", ""))
        sigs.add(signature(tr.get("category", ""), tr.get("title", ""), tr.get("data", {})))
    for ip in list((bench_dir / "synthetic").glob("*.png")) + list((bench_dir / "textbook" / "images").glob("*")):
        hashes.add(hashlib.sha256(ip.read_bytes()).hexdigest())
    return titles, sigs, hashes


def make_sample(i, seed, rng_cat, bench, seen, issue_rate):
    titles, sigs, _ = bench
    for attempt in range(50):
        rng = random.Random(f"train-{seed}-{i}-{attempt}")
        category = rng_cat
        s = GENERATORS[category](rng)
        title = s["truth"].d["title"]
        sig = signature(category, title, s["truth"].d["data"])
        if title in titles or sig in sigs or sig in seen:
            continue
        seen.add(sig)
        break
    else:
        raise RuntimeError(f"Không tạo được mẫu {category} không trùng sau 50 lần thử.")

    r = rng.random()
    if r < issue_rate:
        issue = rng.choice(ISSUES)
        img = issue_augment(s["img"], rng, issue)
        degradation, unreadable = "issue", True
        description = rng.choice(T.CAPTURE_GUIDANCE[issue])
        page_type = "mixed"  # không đoán được loại trang từ ảnh hỏng
        s["truth"].d["expected_status"] = "unreadable"
        s["truth"].d["capture_issue"] = issue
    elif r < issue_rate + 0.30:
        img, degradation, unreadable, issue = mild_augment(s["img"], rng), "mild", False, None
        description, page_type = s["description"], s["page_type"]
    else:
        img, degradation, unreadable, issue = s["img"], "none", False, None
        description, page_type = s["description"], s["page_type"]
    jpeg = finalize_jpeg(img, rng)
    item_id = f"tr_{i:05d}"
    truth = s["truth"].d
    truth["id"], truth["source"] = item_id, "synthetic-train"
    return {
        "schema": SCHEMA, "id": item_id, "category": s["category"], "page_type": page_type,
        "split": "val" if i % 20 == 0 else "train", "seed": f"train-{seed}-{i}",
        "degradation": degradation, "capture_issue": issue,
        "target": {"page_type": page_type, "unreadable": unreadable, "description": description},
        "description_words": len(description.split()),
        "qa": [] if unreadable else s["qa"],
        "truth": truth,
    }, jpeg


def generate(n, seed, out_dir, bench_dir, issue_rate):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    bench = load_bench_index(bench_dir)
    rng = random.Random(f"mix-{seed}")
    cats = rng.choices(list(CATEGORY_WEIGHTS), weights=list(CATEGORY_WEIGHTS.values()), k=n)
    seen, index = set(), []
    for i, cat in enumerate(cats):
        item, jpeg = make_sample(i, seed, cat, bench, seen, issue_rate)
        (out / f"{item['id']}.jpg").write_bytes(jpeg)
        item["image"] = f"{item['id']}.jpg"
        item["image_sha256"] = hashlib.sha256(jpeg).hexdigest()
        (out / f"{item['id']}.json").write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n",
                                                encoding="utf-8")
        index.append({k: item[k] for k in ("id", "category", "page_type", "split", "degradation",
                                           "capture_issue", "image", "image_sha256")})
    (out / "index.json").write_text(json.dumps({"schema": SCHEMA, "seed": seed, "count": n, "items": index},
                                               ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index


def check(train_dir, bench_dir):
    """Đối chiếu tập huấn luyện với benchmark: tiêu đề, chữ ký dữ liệu, hash ảnh không được trùng."""
    titles, sigs, hashes = load_bench_index(bench_dir)
    problems = []
    for p in sorted(Path(train_dir).glob("tr_*.json")):
        it = json.loads(p.read_text(encoding="utf-8"))
        tr = it["truth"]
        if tr["title"] in titles:
            problems.append(f"{it['id']}: tiêu đề trùng benchmark: {tr['title']}")
        if signature(tr["category"], tr["title"], tr["data"]) in sigs:
            problems.append(f"{it['id']}: dữ liệu trùng benchmark")
        if it["image_sha256"] in hashes:
            problems.append(f"{it['id']}: ảnh trùng benchmark")
    return problems


def stats(train_dir):
    items = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(train_dir).glob("tr_*.json"))]
    words = [i["description_words"] for i in items if not i["target"]["unreadable"]]
    print(f"Số mẫu: {len(items)} | train {sum(i['split'] == 'train' for i in items)} / val "
          f"{sum(i['split'] == 'val' for i in items)}")
    print("Theo loại:", dict(Counter(i["category"] for i in items)))
    print("Nhiễu:", dict(Counter(i["degradation"] for i in items)),
          "| lỗi chụp:", dict(Counter(i["capture_issue"] for i in items if i["capture_issue"])))
    if words:
        print(f"Độ dài lời diễn giải (từ): nhỏ nhất {min(words)}, trung vị {sorted(words)[len(words) // 2]}, "
              f"lớn nhất {max(words)}")
    print("Số cặp hỏi đáp:", sum(len(i["qa"]) for i in items))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--n", type=int, default=1200)
    g.add_argument("--seed", type=int, default=1)
    g.add_argument("--out", default=str(AI_ROOT.parent / "data" / "train" / "v1"))
    g.add_argument("--bench", default=str(DEFAULT_BENCH))
    g.add_argument("--issue-rate", type=float, default=0.12, help="tỉ lệ ảnh lỗi chụp (kỳ vọng hướng dẫn chụp lại)")
    c = sub.add_parser("check")
    c.add_argument("--train", required=True)
    c.add_argument("--bench", default=str(DEFAULT_BENCH))
    s = sub.add_parser("stats")
    s.add_argument("--train", required=True)
    args = ap.parse_args()
    if args.cmd == "generate":
        if not 0 <= args.issue_rate <= 0.5:
            raise SystemExit("--issue-rate phải trong khoảng 0..0.5")
        idx = generate(args.n, args.seed, args.out, args.bench, args.issue_rate)
        print(f"Đã sinh {len(idx)} mẫu vào {args.out}")
        problems = check(args.out, args.bench)
        print("Kiểm tra trùng benchmark:", "ĐẠT" if not problems else f"{len(problems)} VẤN ĐỀ")
        for p in problems[:10]:
            print("  ", p)
        if problems:
            raise SystemExit(1)
    elif args.cmd == "check":
        problems = check(args.train, args.bench)
        for p in problems[:20]:
            print(p)
        print("ĐẠT: không trùng benchmark" if not problems else f"{len(problems)} vấn đề")
        raise SystemExit(1 if problems else 0)
    else:
        stats(args.train)


if __name__ == "__main__":
    main()

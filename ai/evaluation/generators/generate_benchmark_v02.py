#!/usr/bin/env python3
"""Sinh bộ mẫu tổng hợp cho benchmark v0.2 (xác định, có seed).

Mỗi mẫu gồm ảnh PNG + ground truth JSON (schema truth_v0.2: mệnh đề
subject/predicate/object, câu hỏi, trạng thái kỳ vọng). Ground truth được
tạo từ dữ liệu dùng để vẽ ảnh nên chính xác tuyệt đối.

Chạy từ thư mục ai/:
    uv run python evaluation/generators/generate_benchmark_v02.py

Script ghi đè các mẫu do chính nó sinh ra và giữ nguyên các mục "legacy"
(v0.1) trong data/benchmark/manifest.json.
"""

import hashlib
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[3]
BENCH = ROOT / "data" / "benchmark"
OUT = BENCH / "synthetic"
MANIFEST = BENCH / "manifest.json"
GENERATOR = "generate_benchmark_v02.py"
VERSION = "0.2.0"
LICENSE = "CC0-1.0 (tự sinh bằng mã, không dùng tư liệu bên ngoài)"

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FONT_REG = FONT_DIR / "DejaVuSans.ttf"
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
if not FONT_REG.exists() or not FONT_BOLD.exists():
    raise SystemExit("Chưa tìm thấy font DejaVu Sans (regular + bold).")

W, H = 1100, 720
BLUE = "#3679b5"
PALETTE = ["#8ecae6", "#ffb703", "#b7e4c7", "#f4a6a6", "#cdb4db", "#e9c46a"]


# --------------------------------------------------------------------------
# Tiện ích
# --------------------------------------------------------------------------

def font(size, bold=False):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REG), size)


def vn(x):
    """Số theo kiểu Việt Nam (dấu phẩy thập phân)."""
    return str(x).replace(".", ",")


def canvas(title, subtitle="Dữ liệu minh họa"):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    size = 36
    f = font(size, True)
    while d.textlength(title, font=f) > 1020 and size > 22:
        size -= 2
        f = font(size, True)
    d.text((W // 2, 48), title, font=f, fill="black", anchor="mm")
    if subtitle:
        d.text((W // 2, 95), subtitle, font=font(22), fill="#666666", anchor="mm")
    return img, d


def wrap(d, text, f, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def text_in_box(d, cx, cy, text, max_w, size=24, bold=False, fill="black"):
    f = font(size, bold)
    lines = wrap(d, text, f, max_w)
    while max(d.textlength(t, font=f) for t in lines) > max_w and size > 14:
        size -= 1
        f = font(size, bold)
        lines = wrap(d, text, f, max_w)
    lh = size * 1.25
    y0 = cy - lh * (len(lines) - 1) / 2
    for i, line in enumerate(lines):
        d.text((cx, y0 + i * lh), line, font=f, fill=fill, anchor="mm")


def arrow(d, p0, p1, width=4, head=17, fill="#222222"):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy) or 1
    ux, uy = dx / length, dy / length
    base = (p1[0] - ux * head, p1[1] - uy * head)
    d.line([p0, base], fill=fill, width=width)
    px, py = -uy, ux
    d.polygon(
        [p1,
         (base[0] + px * head * 0.5, base[1] + py * head * 0.5),
         (base[0] - px * head * 0.5, base[1] - py * head * 0.5)],
        fill=fill,
    )


def polyline_arrow(d, pts, **kw):
    if len(pts) > 2:
        d.line(pts[:-1], fill=kw.get("fill", "#222222"), width=kw.get("width", 4))
    arrow(d, pts[-2], pts[-1], **kw)


def boundary_point(node, toward):
    cx, cy = node["pos"]
    a, b = node["size"][0] / 2, node["size"][1] / 2
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return (cx, cy)
    if node["shape"] == "diamond":
        t = 1 / (abs(dx) / a + abs(dy) / b)
    elif node["shape"] == "oval":
        t = 1 / math.hypot(dx / a, dy / b)
    else:
        tx = a / abs(dx) if dx else float("inf")
        ty = b / abs(dy) if dy else float("inf")
        t = min(tx, ty)
    return (cx + dx * t, cy + dy * t)


class Truth:
    def __init__(self, item_id, category, title):
        self.d = {
            "schema": "truth_v0.2",
            "id": item_id,
            "category": category,
            "synthetic": True,
            "language": "vi",
            "title": title,
            "expected_status": "ok",
            "data": {},
            "propositions": [],
            "questions": [],
        }

    def prop(self, kind, subject, predicate, obj, critical=True):
        n = len(self.d["propositions"]) + 1
        self.d["propositions"].append({
            "id": f"P{n}", "kind": kind, "subject": subject,
            "predicate": predicate, "object": str(obj), "critical": critical,
        })

    def qa(self, question, answer, qtype):
        n = len(self.d["questions"]) + 1
        self.d["questions"].append({
            "id": f"Q{n}", "type": qtype,
            "question": question, "answer": str(answer),
        })


def item(item_id, category, group, difficulty, img, truth, **extra):
    truth.d["id"] = item_id
    return {"id": item_id, "category": category, "group": group,
            "difficulty": difficulty, "image": img, "truth": truth, **extra}


# --------------------------------------------------------------------------
# Biểu đồ cột
# --------------------------------------------------------------------------

BAR_THEMES = [
    ("Số sách thư viện cho mượn trong tuần", "Số quyển", "quyển",
     ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6"]),
    ("Lượng mưa trung bình các tháng mùa mưa", "Lượng mưa (mm)", "mm",
     ["Tháng 6", "Tháng 7", "Tháng 8", "Tháng 9"]),
    ("Số học sinh tham gia các câu lạc bộ", "Số học sinh", "học sinh",
     ["Bóng đá", "Cờ vua", "Vẽ", "Âm nhạc", "Tin học"]),
    ("Số quả cam thu hoạch của các tổ", "Số quả", "quả",
     ["Tổ 1", "Tổ 2", "Tổ 3", "Tổ 4"]),
    ("Số huy chương của các đội", "Số huy chương", "huy chương",
     ["Đội A", "Đội B", "Đội C", "Đội D", "Đội E"]),
    ("Số thùng rác phân loại ở các khu", "Số thùng", "thùng",
     ["Khu A", "Khu B", "Khu C", "Khu D"]),
]


def gen_bar(n):
    labeled = n % 2 == 0
    rng = random.Random(f"bar-{n}")
    title, ylabel, unit, cats = BAR_THEMES[n]
    k = len(cats)
    step = 5
    values = (rng.sample(range(5, 41), k) if labeled
              else [v * 5 for v in rng.sample(range(1, 9), k)])
    ymax = math.ceil((max(values) + 2) / step) * step
    img, d = canvas(title)
    left, top, right, bottom = 150, 180, 1020, 620
    for tick in range(0, ymax + 1, step):
        y = bottom - tick / ymax * (bottom - top)
        d.line((left, y, right, y), fill="#dddddd", width=2)
        d.text((left - 20, y), str(tick), font=font(22), fill="black", anchor="rm")
    d.text((left - 90, top - 40), ylabel, font=font(23), fill="black", anchor="lm")
    slot = (right - left) / k
    for i, (name, v) in enumerate(zip(cats, values)):
        cx = left + slot * (i + 0.5)
        bw = slot * 0.55
        y = bottom - v / ymax * (bottom - top)
        d.rectangle((cx - bw / 2, y, cx + bw / 2, bottom), fill=BLUE)
        if labeled:
            d.text((cx, y - 20), str(v), font=font(27), fill="black", anchor="mm")
        d.text((cx, bottom + 28), name, font=font(25), fill="black", anchor="mm")
    t = Truth("", "bar_chart", title)
    t.d["data"] = {"values": dict(zip(cats, values)), "unit": unit,
                   "y_axis_step": step, "has_value_labels": labeled}
    for name, v in zip(cats, values):
        t.prop("value", f"Cột {name}", "có giá trị", f"{v} {unit}")
    hi = cats[values.index(max(values))]
    lo = cats[values.index(min(values))]
    t.prop("comparison", "Giá trị lớn nhất", "thuộc về", hi)
    t.prop("comparison", "Giá trị nhỏ nhất", "thuộc về", lo)
    t.prop("inference", "Chênh lệch giữa cột lớn nhất và nhỏ nhất", "bằng",
           f"{max(values) - min(values)} {unit}", critical=False)
    t.prop("inference", "Tổng các cột", "bằng", f"{sum(values)} {unit}", critical=False)
    t.qa("Cột nào có giá trị lớn nhất?", hi, "comparison")
    t.qa(f"Cột {cats[0]} có giá trị là bao nhiêu?", f"{values[0]} {unit}", "lookup")
    t.qa("Tổng giá trị của tất cả các cột là bao nhiêu?", f"{sum(values)} {unit}",
         "computation")
    return item(f"bar_{n + 1:02d}", "bar_chart", "chart",
                "easy" if labeled else "medium", img, t,
                has_value_labels=labeled)


# --------------------------------------------------------------------------
# Biểu đồ đường
# --------------------------------------------------------------------------

LINE_THEMES = [
    ("Nhiệt độ trung bình các tháng đầu năm", "Nhiệt độ (°C)", "°C",
     ["Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6"]),
    ("Số học sinh đến thư viện mỗi ngày", "Số học sinh", "học sinh",
     ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6"]),
    ("Số cuốn sách đọc được qua các tuần", "Số cuốn", "cuốn",
     ["Tuần 1", "Tuần 2", "Tuần 3", "Tuần 4", "Tuần 5"]),
    ("Số cây xanh của trường qua các năm", "Số cây", "cây",
     ["2021", "2022", "2023", "2024", "2025"]),
    ("Chiều cao của cây đậu theo ngày", "Chiều cao (cm)", "cm",
     ["Ngày 1", "Ngày 3", "Ngày 5", "Ngày 7", "Ngày 9"]),
]


def gen_line(n):
    labeled = n % 2 == 0
    rng = random.Random(f"line-{n}")
    title, ylabel, unit, xs = LINE_THEMES[n]
    k = len(xs)
    while True:
        values = [rng.randint(1, 8) * 5 for _ in range(k)]
        diffs = [values[i + 1] - values[i] for i in range(k - 1)]
        if (values.count(max(values)) == 1 and values.count(min(values)) == 1
                and max(diffs) > 0 and diffs.count(max(diffs)) == 1):
            break
    ymax = math.ceil((max(values) + 2) / 5) * 5
    img, d = canvas(title)
    left, top, right, bottom = 150, 180, 1020, 620
    for tick in range(0, ymax + 1, 5):
        y = bottom - tick / ymax * (bottom - top)
        d.line((left, y, right, y), fill="#dddddd", width=2)
        d.text((left - 20, y), str(tick), font=font(22), fill="black", anchor="rm")
    d.text((left - 90, top - 40), ylabel, font=font(23), fill="black", anchor="lm")
    pts = []
    for i, v in enumerate(values):
        x = left + 60 + i * (right - left - 120) / (k - 1)
        y = bottom - v / ymax * (bottom - top)
        pts.append((x, y))
        d.text((x, bottom + 28), xs[i], font=font(24), fill="black", anchor="mm")
    d.line(pts, fill=BLUE, width=5, joint="curve")
    for (x, y), v in zip(pts, values):
        d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=BLUE, outline="white", width=2)
        if labeled:
            d.text((x, y - 26), str(v), font=font(26), fill="black", anchor="mm")
    t = Truth("", "line_chart", title)
    t.d["data"] = {"points": dict(zip(xs, values)), "unit": unit,
                   "y_axis_step": 5, "has_value_labels": labeled}
    for x, v in zip(xs, values):
        t.prop("value", f"Điểm {x}", "có giá trị", f"{v} {unit}")
    hi, lo = xs[values.index(max(values))], xs[values.index(min(values))]
    t.prop("comparison", "Giá trị cao nhất", "xuất hiện tại", hi)
    t.prop("comparison", "Giá trị thấp nhất", "xuất hiện tại", lo)
    trend = ("tăng" if values[-1] > values[0]
             else "giảm" if values[-1] < values[0] else "không đổi")
    t.prop("comparison", f"Từ {xs[0]} đến {xs[-1]}", "xu hướng chung là", trend)
    j = diffs.index(max(diffs))
    t.prop("comparison", "Mức tăng lớn nhất giữa hai điểm liên tiếp", "xảy ra từ",
           f"{xs[j]} đến {xs[j + 1]} (tăng {max(diffs)} {unit})")
    t.qa("Giá trị cao nhất xuất hiện ở đâu?", hi, "comparison")
    t.qa(f"Giá trị tại {xs[0]} là bao nhiêu?", f"{values[0]} {unit}", "lookup")
    t.qa("Giữa hai điểm liên tiếp nào giá trị tăng nhiều nhất?",
         f"{xs[j]} đến {xs[j + 1]}", "comparison")
    return item(f"line_{n + 1:02d}", "line_chart", "chart",
                "easy" if labeled else "medium", img, t, has_value_labels=labeled)


# --------------------------------------------------------------------------
# Biểu đồ tròn
# --------------------------------------------------------------------------

PIE_THEMES = [
    ("Phương tiện học sinh đến trường", ["Đi bộ", "Xe đạp", "Xe máy", "Xe buýt"]),
    ("Môn học yêu thích của lớp", ["Toán", "Ngữ văn", "Tiếng Anh", "Thể dục", "Mỹ thuật"]),
    ("Cơ cấu sử dụng đất của xã", ["Trồng lúa", "Rau màu", "Ao hồ", "Đất ở"]),
    ("Nguồn điện của một quốc gia", ["Thủy điện", "Nhiệt điện", "Điện gió",
                                     "Điện mặt trời"]),
]


def gen_pie(n):
    rng = random.Random(f"pie-{n}")
    title, names = PIE_THEMES[n]
    k = len(names)
    while True:
        units = [2] * k
        for _ in range(20 - 2 * k):
            units[rng.randrange(k)] += 1
        if units.count(max(units)) == 1 and units.count(min(units)) == 1:
            break
    pct = [u * 5 for u in units]
    img, d = canvas(title)
    cx, cy, r = 360, 420, 230
    bbox = (cx - r, cy - r, cx + r, cy + r)
    start = -90.0
    for i, p in enumerate(pct):
        end = start + p * 3.6
        d.pieslice(bbox, start, end, fill=PALETTE[i], outline="#444444", width=3)
        mid = math.radians((start + end) / 2)
        d.text((cx + r * 0.65 * math.cos(mid), cy + r * 0.65 * math.sin(mid)),
               f"{p}%", font=font(28, True), fill="black", anchor="mm")
        start = end
    for i, name in enumerate(names):
        y = 250 + i * 72
        d.rectangle((690, y - 20, 730, y + 20), fill=PALETTE[i], outline="#444444", width=2)
        d.text((750, y), name, font=font(29), fill="black", anchor="lm")
    t = Truth("", "pie_chart", title)
    t.d["data"] = {"percentages": dict(zip(names, pct)), "slice_order":
                   "bắt đầu từ đỉnh (12 giờ), theo chiều kim đồng hồ, cùng thứ tự chú thích"}
    for name, p in zip(names, pct):
        t.prop("value", f"Phần {name}", "chiếm", f"{p}%")
    hi, lo = names[pct.index(max(pct))], names[pct.index(min(pct))]
    t.prop("comparison", "Phần lớn nhất", "là", hi)
    t.prop("comparison", "Phần nhỏ nhất", "là", lo)
    t.prop("structure", "Tổng các phần", "bằng", "100%", critical=False)
    top2 = sorted(zip(pct, names), reverse=True)[:2]
    t.qa("Phần nào chiếm tỉ lệ lớn nhất?", hi, "comparison")
    t.qa(f"Phần {names[0]} chiếm bao nhiêu phần trăm?", f"{pct[0]}%", "lookup")
    t.qa(f"Hai phần {top2[0][1]} và {top2[1][1]} cộng lại chiếm bao nhiêu phần trăm?",
         f"{top2[0][0] + top2[1][0]}%", "computation")
    return item(f"pie_{n + 1:02d}", "pie_chart", "chart",
                "easy" if k == 4 else "medium", img, t)


# --------------------------------------------------------------------------
# Bảng số liệu
# --------------------------------------------------------------------------

def table_spec(n, rng):
    def unique_max(cols_idx, rows):
        return all([r[c] for r in rows].count(max(r[c] for r in rows)) == 1
                   for c in cols_idx)

    if n == 0:
        title, rl = "Điểm kiểm tra giữa kì", ["Học sinh A", "Học sinh B", "Học sinh C", "Học sinh D"]
        cols, mx = ["Toán", "Ngữ văn", "Tiếng Anh"], [0, 1, 2]
        while True:
            rows = [[rng.choice([x / 2 for x in range(10, 21)]) for _ in cols] for _ in rl]
            if unique_max(mx, rows):
                return title, "Học sinh", rl, cols, rows, mx, "điểm"
    if n == 1:
        title, rl = "Số sản phẩm bán được theo tuần", ["Tuần 1", "Tuần 2", "Tuần 3", "Tuần 4"]
        cols, mx = ["Bút", "Vở", "Thước"], [0, 1, 2]
        while True:
            rows = [[rng.randint(10, 60) for _ in cols] for _ in rl]
            if unique_max(mx, rows):
                return title, "Tuần", rl, cols, rows, mx, "sản phẩm"
    if n == 2:
        title = "Số ngày có mưa trong tháng"
        rl = ["Tháng 5", "Tháng 6", "Tháng 7", "Tháng 8", "Tháng 9"]
        cols, mx = ["Miền Bắc", "Miền Trung", "Miền Nam"], [0, 1, 2]
        while True:
            rows = [[rng.randint(5, 25) for _ in cols] for _ in rl]
            if unique_max(mx, rows):
                return title, "Tháng", rl, cols, rows, mx, "ngày"
    if n == 3:
        title, rl = "Kết quả thi đấu của các đội", ["Đội A", "Đội B", "Đội C", "Đội D"]
        cols, mx = ["Thắng", "Hòa", "Thua", "Điểm"], [3]
        while True:
            rows = []
            for _ in rl:
                w_, dr, lo = rng.randint(0, 5), rng.randint(0, 3), rng.randint(0, 5)
                rows.append([w_, dr, lo, 3 * w_ + dr])
            if unique_max(mx, rows):
                return title, "Đội", rl, cols, rows, mx, ""
    title, rl = "Khối lượng rác thu gom trong tuần (kg)", ["Thứ 2", "Thứ 4", "Thứ 6"]
    cols, mx = ["Giấy", "Nhựa", "Thủy tinh"], [0, 1, 2]
    while True:
        rows = [[rng.randint(5, 40) for _ in cols] for _ in rl]
        if unique_max(mx, rows):
            return title, "Ngày", rl, cols, rows, mx, "kg"


def gen_table(n):
    rng = random.Random(f"table-{n}")
    title, corner, rl, cols, rows, mx, unit = table_spec(n, rng)
    img, d = canvas(title, None)
    first_w = 230
    col_w = min(190, (900 - first_w) / len(cols))
    tw = first_w + col_w * len(cols)
    x0, y0, rh = (W - tw) / 2, 150, 72
    for r in range(len(rl) + 1):
        for c in range(len(cols) + 1):
            xa = x0 + (0 if c == 0 else first_w + col_w * (c - 1))
            xb = x0 + first_w + col_w * c
            ya, yb = y0 + r * rh, y0 + (r + 1) * rh
            fill = "#e6e6e6" if (r == 0 or c == 0) else "white"
            d.rectangle((xa, ya, xb, yb), fill=fill, outline="#333333", width=3)
            if r == 0 and c == 0:
                label, bold = corner, True
            elif r == 0:
                label, bold = cols[c - 1], True
            elif c == 0:
                label, bold = rl[r - 1], True
            else:
                v = rows[r - 1][c - 1]
                label, bold = (vn(f"{v:.1f}") if isinstance(v, float) else str(v)), False
            text_in_box(d, (xa + xb) / 2, (ya + yb) / 2, label, (xb - xa) - 14, 26, bold)

    def fmt(v):
        return vn(f"{v:.1f}") if isinstance(v, float) else str(v)

    t = Truth("", "table", title)
    t.d["data"] = {"row_labels": rl, "column_labels": cols, "rows": rows}
    for r, name in zip(rows, rl):
        for c, v in zip(cols, r):
            t.prop("value", f"{name} – {c}", "có giá trị", fmt(v))
    for ci in mx:
        col_vals = [r[ci] for r in rows]
        t.prop("comparison", f"Giá trị lớn nhất của cột {cols[ci]}", "thuộc về",
               rl[col_vals.index(max(col_vals))])
    t.qa(f"{rl[1]} – {cols[0]} có giá trị là bao nhiêu?", fmt(rows[1][0]), "lookup")
    ci = mx[-1]
    col_vals = [r[ci] for r in rows]
    t.qa(f"Ở cột {cols[ci]}, hàng nào có giá trị lớn nhất?",
         rl[col_vals.index(max(col_vals))], "comparison")
    if n != 3:
        total = round(sum(rows[0]), 1)
        t.qa(f"Tổng các giá trị của hàng {rl[0]} là bao nhiêu?",
             f"{fmt(total) if isinstance(total, float) else total}", "computation")
    cells = len(rl) * len(cols)
    return item(f"table_{n + 1:02d}", "table", "table",
                "easy" if cells <= 12 else "medium", img, t)


# --------------------------------------------------------------------------
# Sơ đồ khối / lưu đồ
# --------------------------------------------------------------------------

def N(i, text, shape, pos, size=(170, 90)):
    return {"id": i, "text": text, "shape": shape, "pos": pos, "size": size}


FLOWS = [
    {   # chuỗi ngang 5 bước
        "title": "Quy trình xử lý rác tái chế", "difficulty": "easy",
        "nodes": [N("a", "Thu gom rác", "box", (110, 360), (150, 90)),
                  N("b", "Phân loại rác", "box", (320, 360), (150, 90)),
                  N("c", "Làm sạch", "box", (530, 360), (150, 90)),
                  N("d", "Tái chế", "box", (740, 360), (150, 90)),
                  N("e", "Sản phẩm mới", "box", (950, 360), (150, 90))],
        "edges": [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")],
        "extra": [("structure", "Sơ đồ", "đi theo hướng", "từ trái sang phải"),
                  ("structure", "Bước đầu tiên", "là", "Thu gom rác"),
                  ("structure", "Bước cuối cùng", "là", "Sản phẩm mới")],
        "questions": [("Sau bước Phân loại rác là bước nào?", "Làm sạch", "relation"),
                      ("Quy trình có tất cả bao nhiêu bước?", "5", "lookup")],
    },
    {   # rẽ nhánh
        "title": "Chuẩn bị trước khi đi học", "difficulty": "medium",
        "nodes": [N("s", "Bắt đầu", "oval", (550, 160), (170, 70)),
                  N("q", "Trời có mưa?", "diamond", (550, 310), (260, 130)),
                  N("y", "Mang áo mưa", "box", (230, 490), (200, 80)),
                  N("n", "Mang mũ", "box", (870, 490), (200, 80)),
                  N("e", "Đi học", "oval", (550, 640), (170, 70))],
        "edges": [("s", "q"), ("q", "y", "Có"), ("q", "n", "Không"),
                  ("y", "e"), ("n", "e")],
        "extra": [("structure", "Sơ đồ", "có", "một điểm rẽ nhánh tại 'Trời có mưa?'")],
        "questions": [("Nếu trời có mưa thì làm gì?", "Mang áo mưa", "relation"),
                      ("Nếu trời không mưa thì làm gì?", "Mang mũ", "relation"),
                      ("Hai nhánh gặp lại nhau ở bước nào?", "Đi học", "relation")],
    },
    {   # chuỗi dọc
        "title": "Các bước chấm và trả bài kiểm tra", "difficulty": "easy",
        "nodes": [N("a", "Học sinh nộp bài", "box", (550, 170), (320, 70)),
                  N("b", "Giáo viên chấm bài", "box", (550, 300), (320, 70)),
                  N("c", "Nhập điểm vào sổ", "box", (550, 430), (320, 70)),
                  N("d", "Thông báo kết quả", "box", (550, 560), (320, 70))],
        "edges": [("a", "b"), ("b", "c"), ("c", "d")],
        "extra": [("structure", "Sơ đồ", "đi theo hướng", "từ trên xuống dưới"),
                  ("structure", "Bước đầu tiên", "là", "Học sinh nộp bài"),
                  ("structure", "Bước cuối cùng", "là", "Thông báo kết quả")],
        "questions": [("Bước nào diễn ra ngay trước khi nhập điểm vào sổ?",
                       "Giáo viên chấm bài", "relation")],
    },
    {   # vòng lặp
        "title": "Quy trình làm một bài toán", "difficulty": "hard",
        "nodes": [N("a", "Nhận đề bài", "box", (130, 330), (160, 90)),
                  N("b", "Đọc kĩ đề", "box", (390, 330), (160, 90)),
                  N("q", "Đã hiểu đề?", "diamond", (680, 330), (220, 130)),
                  N("c", "Làm bài", "box", (960, 330), (160, 90))],
        "edges": [("a", "b"), ("b", "q"), ("q", "c", "Có"),
                  ("q", "b", "Không", [(680, 520), (390, 520)])],
        "extra": [("structure", "Sơ đồ", "có", "một vòng lặp: nếu chưa hiểu đề thì quay lại bước 'Đọc kĩ đề'")],
        "questions": [("Nếu chưa hiểu đề thì quay lại bước nào?", "Đọc kĩ đề", "relation"),
                      ("Nếu đã hiểu đề thì làm gì tiếp theo?", "Làm bài", "relation")],
    },
    {   # điều kiện, nhánh rẽ ngang/dọc
        "title": "Kiểm tra sức khỏe đầu giờ", "difficulty": "medium",
        "nodes": [N("s", "Bắt đầu", "oval", (550, 150), (170, 64)),
                  N("m", "Đo nhiệt độ", "box", (550, 270), (220, 70)),
                  N("q", "Nhiệt độ trên 37,5°C?", "diamond", (550, 440), (340, 150)),
                  N("y", "Báo giáo viên", "box", (900, 440), (200, 80)),
                  N("n", "Vào lớp", "box", (550, 630), (200, 70))],
        "edges": [("s", "m"), ("m", "q"), ("q", "y", "Có"), ("q", "n", "Không")],
        "extra": [("structure", "Sơ đồ", "có", "một điểm rẽ nhánh tại 'Nhiệt độ trên 37,5°C?'")],
        "questions": [("Nếu nhiệt độ trên 37,5°C thì làm gì?", "Báo giáo viên", "relation"),
                      ("Nếu nhiệt độ không trên 37,5°C thì làm gì?", "Vào lớp", "relation")],
    },
]


def draw_node(d, node):
    cx, cy = node["pos"]
    w, h = node["size"]
    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    if node["shape"] == "diamond":
        d.polygon([(cx, box[1]), (box[2], cy), (cx, box[3]), (box[0], cy)],
                  fill="#fff4d6", outline="#b58900")
        d.line([(cx, box[1]), (box[2], cy), (cx, box[3]), (box[0], cy), (cx, box[1])],
               fill="#b58900", width=3)
        mw = w * 0.58
    elif node["shape"] == "oval":
        d.ellipse(box, fill="#e3f5e1", outline="#2e7d32", width=3)
        mw = w * 0.8
    else:
        d.rounded_rectangle(box, radius=12, fill="#e8f1fb", outline="#2b5d8a", width=3)
        mw = w - 20
    text_in_box(d, cx, cy, node["text"], mw, 25)


def gen_flow(n):
    spec = FLOWS[n]
    img, d = canvas(spec["title"], None)
    nodes = {nd["id"]: nd for nd in spec["nodes"]}
    for nd in nodes.values():
        draw_node(d, nd)
    t = Truth("", "flow_diagram", spec["title"])
    t.d["data"] = {"nodes": [nd["text"] for nd in spec["nodes"]],
                   "edges": [{"from": nodes[e[0]]["text"], "to": nodes[e[1]]["text"],
                              "label": e[2] if len(e) > 2 else None} for e in spec["edges"]]}
    for e in spec["edges"]:
        src, dst = nodes[e[0]], nodes[e[1]]
        label = e[2] if len(e) > 2 else None
        via = e[3] if len(e) > 3 else None
        if via:
            pts = [boundary_point(src, via[0]), *via, boundary_point(dst, via[-1])]
        else:
            pts = [boundary_point(src, dst["pos"]), boundary_point(dst, src["pos"])]
        polyline_arrow(d, pts)
        pred = "dẫn đến" if not label else f"dẫn đến khi câu trả lời là '{label}'"
        t.prop("relation", src["text"], pred, dst["text"])
        if label:
            (x0, y0), (x1, y1) = pts[0], pts[1]
            ln = math.hypot(x1 - x0, y1 - y0) or 1
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            ox, oy = (y1 - y0) / ln * 26, -(x1 - x0) / ln * 26
            d.text((mx + ox, my + oy), label, font=font(25, True), fill="#8a1c1c",
                   anchor="mm")
    for kind, s, p, o in spec["extra"]:
        t.prop(kind, s, p, o, critical=True)
    for q, a, ty in spec["questions"]:
        t.qa(q, a, ty)
    return item(f"flow_{n + 1:02d}", "flow_diagram", "figure", spec["difficulty"], img, t)


# --------------------------------------------------------------------------
# Sơ đồ vòng (chu trình)
# --------------------------------------------------------------------------

CYCLES = [
    ("Vòng tuần hoàn của nước", ["Nước bốc hơi", "Hơi nước ngưng tụ thành mây",
                                 "Mưa rơi xuống", "Nước chảy về sông, biển"], True, "easy"),
    ("Vòng đời của bướm", ["Trứng", "Sâu bướm", "Nhộng", "Bướm trưởng thành"], False, "medium"),
    ("Vòng đời của cây đậu", ["Gieo hạt", "Hạt nảy mầm", "Cây con", "Ra hoa, kết quả",
                              "Hạt mới"], True, "medium"),
]


def gen_cycle(n):
    title, stages, clockwise, diff = CYCLES[n]
    k = len(stages)
    img, d = canvas(title, None)
    cx, cy, rx, ry = 550, 405, 340, 225
    sign = 1 if clockwise else -1
    nodes = []
    for i, text in enumerate(stages):
        ang = math.radians(-90 + sign * i * 360 / k)
        nodes.append({"text": text, "shape": "box",
                      "pos": (cx + rx * math.cos(ang), cy + ry * math.sin(ang)),
                      "size": (250, 104)})
    for i in range(k):
        a, b = nodes[i], nodes[(i + 1) % k]
        arrow(d, boundary_point(a, b["pos"]), boundary_point(b, a["pos"]), width=5, head=20)
    for nd in nodes:
        draw_node(d, nd)
    direction = "cùng chiều kim đồng hồ" if clockwise else "ngược chiều kim đồng hồ"
    t = Truth("", "cycle_diagram", title)
    t.d["data"] = {"stages_in_order": stages, "arrow_direction": direction}
    for i in range(k):
        t.prop("relation", stages[i], "dẫn đến", stages[(i + 1) % k])
    t.prop("structure", "Chiều các mũi tên", "là", direction)
    t.prop("structure", "Sơ đồ", "là", "một chu trình khép kín, không có điểm kết thúc")
    t.qa(f"Sau '{stages[0]}' là giai đoạn nào?", stages[1], "relation")
    t.qa(f"Sau '{stages[-1]}' là giai đoạn nào?", stages[0], "relation")
    t.qa("Các mũi tên đi theo chiều nào?", direction, "relation")
    return item(f"cycle_{n + 1:02d}", "cycle_diagram", "figure", diff, img, t)


# --------------------------------------------------------------------------
# Hình học
# --------------------------------------------------------------------------

def side_label(d, p, q, centroid, text, off=26, size=28):
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    vx, vy = mx - centroid[0], my - centroid[1]
    ln = math.hypot(vx, vy) or 1
    ux, uy = vx / ln, vy / ln
    half_w = d.textlength(text, font=font(size)) / 2
    dist = off + abs(ux) * half_w + abs(uy) * size * 0.6
    d.text((mx + ux * dist, my + uy * dist), text, font=font(size),
           fill="#8a1c1c", anchor="mm")


def vertex_label(d, p, centroid, text, off=26):
    vx, vy = p[0] - centroid[0], p[1] - centroid[1]
    ln = math.hypot(vx, vy) or 1
    d.text((p[0] + vx / ln * off, p[1] + vy / ln * off), text, font=font(30, True),
           fill="black", anchor="mm")


def gen_geometry(n):
    if n in (0, 1):
        a, b, c = [(3, 4, 5), (5, 12, 13)][n]
        mirror = n == 1
        title = "Tam giác ABC vuông tại A"
        img, d = canvas(title, None)
        s = 380 / max(a, b)
        ax, ay = (780, 590) if mirror else (330, 590)
        A = (ax, ay)
        B = (ax, ay - a * s)
        C = (ax - b * s, ay) if mirror else (ax + b * s, ay)
        d.polygon([A, B, C], fill="#eaf3fb", outline="#2b5d8a")
        d.line([A, B, C, A], fill="#2b5d8a", width=5)
        m = 30
        sq = (ax - m, ay - m, ax, ay) if mirror else (ax, ay - m, ax + m, ay)
        d.rectangle(sq, outline="#2b5d8a", width=4)
        cen = ((A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3)
        for p, tx in ((A, "A"), (B, "B"), (C, "C")):
            vertex_label(d, p, cen, tx)
        side_label(d, A, B, cen, f"AB = {a} cm")
        side_label(d, A, C, cen, f"AC = {b} cm")
        t = Truth("", "geometry", title)
        t.d["data"] = {"AB_cm": a, "AC_cm": b, "BC_cm": c, "right_angle_at": "A",
                       "BC_shown_in_image": False}
        t.prop("structure", "Tam giác ABC", "là tam giác", "vuông tại A")
        t.prop("value", "Cạnh AB", "dài", f"{a} cm")
        t.prop("value", "Cạnh AC", "dài", f"{b} cm")
        t.prop("inference", "Cạnh huyền BC", "dài", f"{c} cm", critical=False)
        t.prop("inference", "Diện tích tam giác ABC", "bằng",
               f"{a * b // 2} cm²", critical=False)
        t.qa("Tam giác ABC vuông tại đỉnh nào?", "A", "lookup")
        t.qa("Cạnh huyền BC dài bao nhiêu xăng-ti-mét?", f"{c} cm", "computation")
        t.qa("Diện tích tam giác ABC là bao nhiêu?", f"{a * b // 2} cm²", "computation")
        return item(f"geo_{n + 1:02d}", "geometry", "figure", "medium", img, t)

    if n == 2:
        title = "Hình chữ nhật ABCD"
        img, d = canvas(title, None)
        w_, h_ = 8, 5
        s = 55
        x0, y0 = 550 - w_ * s / 2, 400 - h_ * s / 2
        A, B = (x0, y0 + h_ * s), (x0 + w_ * s, y0 + h_ * s)
        C, D = (x0 + w_ * s, y0), (x0, y0)
        d.rectangle((D[0], D[1], B[0], B[1]), fill="#eaf3fb", outline="#2b5d8a", width=5)
        m = 24
        for (px, py, sx, sy) in ((A[0], A[1], 1, -1), (B[0], B[1], -1, -1),
                                 (C[0], C[1], -1, 1), (D[0], D[1], 1, 1)):
            d.rectangle((min(px, px + sx * m), min(py, py + sy * m),
                         max(px, px + sx * m), max(py, py + sy * m)),
                        outline="#2b5d8a", width=3)
        cen = (550, 400)
        for p, tx in ((A, "A"), (B, "B"), (C, "C"), (D, "D")):
            vertex_label(d, p, cen, tx)
        side_label(d, A, B, cen, f"AB = {w_} cm")
        side_label(d, B, C, cen, f"BC = {h_} cm")
        t = Truth("", "geometry", title)
        t.d["data"] = {"AB_cm": w_, "BC_cm": h_}
        t.prop("structure", "Tứ giác ABCD", "là", "hình chữ nhật (bốn góc vuông)")
        t.prop("value", "Cạnh AB", "dài", f"{w_} cm")
        t.prop("value", "Cạnh BC", "dài", f"{h_} cm")
        t.prop("inference", "Diện tích hình chữ nhật ABCD", "bằng",
               f"{w_ * h_} cm²", critical=False)
        t.prop("inference", "Chu vi hình chữ nhật ABCD", "bằng",
               f"{2 * (w_ + h_)} cm", critical=False)
        t.qa("Diện tích hình chữ nhật ABCD là bao nhiêu?", f"{w_ * h_} cm²", "computation")
        t.qa("Chu vi hình chữ nhật ABCD là bao nhiêu?", f"{2 * (w_ + h_)} cm", "computation")
        return item("geo_03", "geometry", "figure", "easy", img, t)

    if n == 3:
        title = "Đường tròn tâm O"
        img, d = canvas(title, None)
        r_cm, s = 6, 33
        cx, cy, r = 550, 410, 6 * 33
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#eaf3fb", outline="#2b5d8a", width=5)
        ang = math.radians(-30)
        P = (cx + r * math.cos(ang), cy + r * math.sin(ang))
        d.line([(cx, cy), P], fill="#8a1c1c", width=5)
        d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill="black")
        d.text((cx - 26, cy + 24), "O", font=font(30, True), fill="black", anchor="mm")
        d.text((cx + r * 0.5 * math.cos(ang) - 10, cy + r * 0.5 * math.sin(ang) - 36),
               f"r = {r_cm} cm", font=font(28), fill="#8a1c1c", anchor="mm")
        t = Truth("", "geometry", title)
        t.d["data"] = {"radius_cm": r_cm}
        t.prop("structure", "Điểm O", "là", "tâm của đường tròn")
        t.prop("value", "Bán kính của đường tròn", "bằng", f"{r_cm} cm")
        t.prop("inference", "Đường kính của đường tròn", "bằng", f"{2 * r_cm} cm",
               critical=False)
        t.qa("Bán kính của đường tròn là bao nhiêu?", f"{r_cm} cm", "lookup")
        t.qa("Đường kính của đường tròn là bao nhiêu?", f"{2 * r_cm} cm", "computation")
        return item("geo_04", "geometry", "figure", "easy", img, t)

    alpha, beta = [(50, 60), (45, 75)][n - 4]
    gamma = 180 - alpha - beta
    title = "Tam giác ABC với hai góc cho trước"
    img, d = canvas(title, None)
    L = 440
    A = (330, 590)
    B = (A[0] + L, A[1])
    AC = L * math.sin(math.radians(beta)) / math.sin(math.radians(gamma))
    C = (A[0] + AC * math.cos(math.radians(alpha)), A[1] - AC * math.sin(math.radians(alpha)))
    d.polygon([A, B, C], fill="#eaf3fb")
    d.line([A, B, C, A], fill="#2b5d8a", width=5)
    cen = ((A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3)
    for p, tx in ((A, "A"), (B, "B"), (C, "C")):
        vertex_label(d, p, cen, tx)
    for p, tx in ((A, f"{alpha}°"), (B, f"{beta}°"), (C, "?")):
        q = (p[0] + (cen[0] - p[0]) * 0.3, p[1] + (cen[1] - p[1]) * 0.3)
        d.text(q, tx, font=font(30, True), fill="#8a1c1c", anchor="mm")
    t = Truth("", "geometry", title)
    t.d["data"] = {"angle_A": alpha, "angle_B": beta, "angle_C": gamma}
    t.prop("value", "Góc A", "có số đo", f"{alpha}°")
    t.prop("value", "Góc B", "có số đo", f"{beta}°")
    t.prop("structure", "Góc C", "chưa biết số đo (đánh dấu '?')", "cần tính")
    t.prop("inference", "Góc C", "có số đo", f"{gamma}°", critical=False)
    t.qa("Góc A có số đo bao nhiêu độ?", f"{alpha}°", "lookup")
    t.qa("Góc C có số đo bao nhiêu độ?", f"{gamma}°", "computation")
    return item(f"geo_{n + 1:02d}", "geometry", "figure", "medium", img, t)


# --------------------------------------------------------------------------
# Sơ đồ bản đồ đơn giản
# --------------------------------------------------------------------------

PLACES = ["Trường học", "Bệnh viện", "Công viên", "Chợ", "Thư viện", "Bưu điện",
          "Nhà văn hóa", "Sân vận động"]
CELL_X, CELL_Y = [250, 550, 850], [220, 400, 580]


def direction(dr, dc):
    ns = "Bắc" if dr < 0 else "Nam" if dr > 0 else ""
    ew = "Đông" if dc > 0 else "Tây" if dc < 0 else ""
    return f"{ns} {ew}".strip() if not (ns and ew) else f"{ew} {ns}"


def gen_map(n):
    rng = random.Random(f"map-{n}")
    names = ["Trường học"] + rng.sample(PLACES[1:], 4)
    cells = rng.sample(range(9), 5)
    title = "Sơ đồ khu phố"
    img, d = canvas(title, "Hướng Bắc ở phía trên của sơ đồ")
    for y in (310, 490):
        d.line((110, y, 990, y), fill="#d4d4d4", width=22)
    for x in (400, 700):
        d.line((x, 140, x, 660), fill="#d4d4d4", width=22)
    pos = {}
    for name, cell in zip(names, cells):
        r, c = divmod(cell, 3)
        pos[name] = (r, c)
        cx, cy = CELL_X[c], CELL_Y[r]
        d.rounded_rectangle((cx - 100, cy - 36, cx + 100, cy + 36), radius=12,
                            fill="#e8f1fb" if name != "Trường học" else "#ffe9b8",
                            outline="#2b5d8a", width=3)
        text_in_box(d, cx, cy, name, 180, 25, True)
    arrow(d, (1020, 215), (1020, 135), width=5, head=20)
    d.text((1020, 112), "Bắc", font=font(26, True), fill="black", anchor="mm")
    t = Truth("", "schematic_map", title)
    t.d["data"] = {"north_is_up": True,
                   "grid_cell_(row,col)": {k: list(v) for k, v in pos.items()}}
    t.prop("structure", "Hướng Bắc", "nằm ở", "phía trên của sơ đồ")
    t.prop("structure", "Số địa điểm được đánh dấu", "là", "5")
    ref = pos["Trường học"]
    for name in names[1:]:
        dr, dc = pos[name][0] - ref[0], pos[name][1] - ref[1]
        dirn = direction(dr, dc)
        t.prop("relation", name, "nằm ở", f"phía {dirn} của Trường học")
        t.qa(f"{name} nằm ở hướng nào so với Trường học?", dirn, "relation")
    t.qa("Sơ đồ đánh dấu bao nhiêu địa điểm?", "5", "lookup")
    return item(f"map_{n + 1:02d}", "schematic_map", "map", "medium", img, t)


# --------------------------------------------------------------------------
# Biến thể giảm chất lượng
# --------------------------------------------------------------------------

def degrade_hard(img, seed):
    rng = random.Random(seed)
    big = img.rotate(rng.choice([-1, 1]) * 6, resample=Image.BICUBIC, expand=False,
                     fillcolor="white")
    big = ImageEnhance.Brightness(big).enhance(0.65)
    big = ImageEnhance.Contrast(big).enhance(0.85)
    big = big.filter(ImageFilter.GaussianBlur(1.1))
    noise = Image.frombytes("L", big.size, rng.randbytes(big.size[0] * big.size[1]))
    return Image.blend(big, noise.convert("RGB"), 0.12)


def degrade_unreadable(img):
    small = img.resize((W // 36, H // 36), Image.BILINEAR)
    out = small.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
    return ImageEnhance.Brightness(out).enhance(0.55)


def variant_hard(base, suffix="hard"):
    truth = json.loads(json.dumps(base["truth"].d))
    truth["id"] = f"{base['id']}_{suffix}"
    truth["derived_from"] = base["id"]
    truth["degradation"] = "xoay 6°, giảm sáng/tương phản, làm mờ nhẹ, thêm nhiễu hạt"
    t = Truth("", base["category"], truth["title"])
    t.d = truth
    return {"id": truth["id"], "category": base["category"], "group": base["group"],
            "difficulty": "hard", "image": degrade_hard(base["image"], truth["id"]),
            "truth": t, "derived_from": base["id"], "degradation": "noisy_rotated"}


def variant_unreadable(base):
    t = Truth("", base["category"], base["truth"].d["title"])
    t.d["id"] = f"{base['id']}_unreadable"
    t.d["derived_from"] = base["id"]
    t.d["degradation"] = "giảm độ phân giải 36 lần, làm mờ mạnh, tối đi"
    t.d["expected_status"] = "unreadable"
    t.d["refusal_expected"] = True
    t.prop("structure", "Ảnh", "ở trạng thái", "không đọc được, không đủ căn cứ để diễn giải")
    t.qa("Giá trị hoặc nhãn chính trong ảnh là gì?", "không xác định được từ ảnh", "refusal")
    return {"id": t.d["id"], "category": base["category"], "group": base["group"],
            "difficulty": "hard", "image": degrade_unreadable(base["image"]),
            "truth": t, "derived_from": base["id"], "degradation": "unreadable"}


# --------------------------------------------------------------------------
# Điều phối
# --------------------------------------------------------------------------

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    gens = [
        ("bar_chart", gen_bar, len(BAR_THEMES)),
        ("line_chart", gen_line, len(LINE_THEMES)),
        ("pie_chart", gen_pie, len(PIE_THEMES)),
        ("table", gen_table, 5),
        ("flow_diagram", gen_flow, len(FLOWS)),
        ("cycle_diagram", gen_cycle, len(CYCLES)),
        ("geometry", gen_geometry, 6),
        ("schematic_map", gen_map, 4),
    ]
    base_items, splits = [], {}
    for cat, fn, count in gens:
        for i in range(count):
            it = fn(i)
            it["split"] = "dev" if i % 5 in (0, 2) else "test"
            splits[it["id"]] = it["split"]
            base_items.append(it)
    by_id = {it["id"]: it for it in base_items}

    variants = [variant_hard(by_id[i]) for i in ("bar_01", "line_02", "flow_02", "geo_01")]
    variants += [variant_unreadable(by_id[i]) for i in ("line_03", "table_02", "cycle_01")]
    for v in variants:
        v["split"] = splits[v["derived_from"]]  # kế thừa split, tránh rò rỉ dev/test

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    legacy = [it for it in manifest["items"] if "generator" not in it]
    legacy_meta = {"chart_01": ("easy", True), "chart_02_no_labels": ("medium", False)}
    for it in legacy:
        diff, _ = legacy_meta.get(it["id"], ("easy", None))
        it.setdefault("group", "chart")
        it.setdefault("difficulty", diff)
        it.setdefault("split", "dev")  # đã dùng trong thăm dò/chấm thử nên không đưa vào test
        it.setdefault("expected_status", "ok")
        it.setdefault("truth_schema", "legacy_v0.1")
        it.setdefault("license", LICENSE)

    generated = []
    for it in base_items + variants:
        img_path = OUT / f"{it['id']}.png"
        truth_path = OUT / f"{it['id']}_truth.json"
        it["image"].save(img_path)
        truth_path.write_text(
            json.dumps(it["truth"].d, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        entry = {
            "id": it["id"], "category": it["category"], "group": it["group"],
            "source": "synthetic",
            "image": f"synthetic/{it['id']}.png",
            "ground_truth": f"synthetic/{it['id']}_truth.json",
            "sha256": sha256_bytes(img_path.read_bytes()),
            "ground_truth_sha256": sha256_bytes(truth_path.read_bytes()),
            "difficulty": it["difficulty"], "split": it["split"],
            "expected_status": it["truth"].d["expected_status"],
            "truth_schema": "truth_v0.2", "license": LICENSE, "generator": GENERATOR,
        }
        for key in ("has_value_labels", "derived_from", "degradation"):
            if key in it:
                entry[key] = it[key]
        generated.append(entry)

    manifest["version"] = VERSION
    manifest["split_policy"] = (
        "dev: dùng để thiết kế/chỉnh prompt; test: không dùng để chỉnh prompt hay rubric. "
        "Biến thể giảm chất lượng kế thừa split của ảnh gốc.")
    manifest["items"] = legacy + generated
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"Đã sinh {len(generated)} mẫu; tổng manifest: {len(manifest['items'])}")


if __name__ == "__main__":
    main()

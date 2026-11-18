"""Đọc số và đơn vị bằng chữ tiếng Việt (để lời diễn giải mục tiêu đọc được bằng giọng nói).

Quy ước: 4 sau chục đọc "bốn" (hai mươi bốn); 1 sau chục >1 đọc "mốt"; 5 sau chục đọc "lăm";
số lẻ đọc "phẩy" rồi từng chữ số (8,5 -> "tám phẩy năm").
"""

from __future__ import annotations

DIGITS = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
GROUPS = ["", "nghìn", "triệu", "tỷ"]

UNIT_SPOKEN = {
    "°C": "độ C", "°": "độ", "mm": "mi li mét", "cm": "xăng ti mét", "m": "mét", "km": "ki lô mét",
    "kg": "ki lô gam", "g": "gam", "cm²": "xăng ti mét vuông", "m²": "mét vuông", "%": "phần trăm",
}


def _chunk(n: int, full: bool) -> str:
    """Đọc 0..999. full=True khi đã có nhóm cao hơn: phải đọc cả 'không trăm' và 'linh'."""
    h, rest = divmod(n, 100)
    t, u = divmod(rest, 10)
    parts = []
    if h or full:
        parts.append(f"{DIGITS[h]} trăm")
    if t == 0:
        if u:
            parts.append(f"linh {DIGITS[u]}" if (h or full) else DIGITS[u])
    elif t == 1:
        parts.append("mười" if u == 0 else "mười " + ("lăm" if u == 5 else DIGITS[u]))
    else:
        s = f"{DIGITS[t]} mươi"
        if u == 1:
            s += " mốt"
        elif u == 5:
            s += " lăm"
        elif u:
            s += f" {DIGITS[u]}"
        parts.append(s)
    return " ".join(parts)


def words(n: int) -> str:
    """Số nguyên không âm -> chữ."""
    if n < 0:
        return "âm " + words(-n)
    if n == 0:
        return "không"
    chunks = []
    while n:
        n, c = divmod(n, 1000)
        chunks.append(c)
    out = []
    top = len(chunks) - 1
    for g in range(top, -1, -1):
        c = chunks[g]
        if c == 0:
            continue
        out.append(_chunk(c, full=g < top).strip() + (f" {GROUPS[g]}" if GROUPS[g] else ""))
    return " ".join(out)


def sn(x) -> str:
    """Số (int hoặc float, tối đa vài chữ số lẻ) -> chữ."""
    if isinstance(x, float) and not x.is_integer():
        whole, frac = f"{x:.6f}".rstrip("0").split(".")
        return f"{words(int(whole))} phẩy " + " ".join(DIGITS[int(c)] for c in frac)
    return words(int(x))


def unit_words(unit: str) -> str:
    return UNIT_SPOKEN.get(unit, unit)


def su(x, unit: str = "") -> str:
    """Số kèm đơn vị: su(29, '°C') -> 'hai mươi chín độ C'."""
    u = unit_words(unit)
    return f"{sn(x)} {u}".strip()

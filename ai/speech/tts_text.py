"""Chuẩn hóa lời diễn giải để đọc ra giọng nói (TTS), không phụ thuộc engine nào.

Lý do: engine TTS tiếng Việt (Android hoặc cục bộ) hay đọc sai số thập phân, phần trăm, đơn vị và ký hiệu.
Hàm ở đây đổi các thứ đó thành chữ tiếng Việt và cắt văn bản thành các đoạn ngắn để phát dần (người nghe không phải
đợi cả đoạn dài). Chỉ xử lý văn bản; việc phát âm do bên ngoài đảm nhiệm.
"""

from __future__ import annotations

import re
import unicodedata

from speech.vn_numbers import UNIT_SPOKEN, sn, words

_UNITS = sorted((u for u in UNIT_SPOKEN if u != "%"), key=len, reverse=True)
_UNIT_RE = "|".join(re.escape(u) for u in _UNITS)
# số (có thể thập phân, dấu phẩy hoặc chấm) + đơn vị tùy chọn; không nuốt chữ cái ngay sau (tránh "5m" trong "5 mục")
_NUM_RE = re.compile(rf"(?<![\w.,])(\d+(?:[.,]\d+)?)\s*(%|{_UNIT_RE})?(?![\w])")


def _number_to_words(text: str) -> str:
    def repl(m: re.Match) -> str:
        raw, unit = m.group(1), m.group(2)
        # "1.000" kiểu phân tách hàng nghìn của tiếng Việt: ba chữ số sau dấu chấm và không có phần thập phân khác
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", raw):
            spoken = words(int(raw.replace(".", "")))
        elif re.search(r"[.,]", raw):
            spoken = sn(float(raw.replace(",", ".")))
        else:
            spoken = words(int(raw))
        return f"{spoken} {UNIT_SPOKEN[unit]}" if unit else spoken

    return _NUM_RE.sub(repl, text)


def prepare_for_speech(text: str) -> str:
    """Đổi số/đơn vị ra chữ, bỏ ký hiệu trang trí, gộp khoảng trắng."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("->", " → ")
    text = re.sub(r"[*_`#>|~^]+", " ", text)           # ký hiệu định dạng còn sót
    text = re.sub(r"(?m)^\s*[-•]\s+", "", text)           # gạch đầu dòng
    text = _number_to_words(text)
    text = text.replace("&", " và ").replace("→", " rồi ").replace("=", " bằng ")
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def split_for_streaming(text: str, max_chars: int = 220) -> list[str]:
    """Cắt theo câu thành các đoạn không dài quá `max_chars` (câu quá dài cắt ở dấu phẩy rồi ở khoảng trắng)."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?…])\s+", text.strip()) if s.strip()]
    pieces: list[str] = []
    for s in sentences:
        while len(s) > max_chars:
            cut = max(s.rfind(",", 0, max_chars), s.rfind(" ", 0, max_chars))
            cut = cut if cut > 20 else max_chars
            pieces.append(s[:cut + 1].strip())
            s = s[cut + 1:].strip()
        if s:
            pieces.append(s)
    chunks: list[str] = []
    for p in pieces:  # gộp các câu ngắn liền kề để đỡ ngắt quãng
        if chunks and len(chunks[-1]) + 1 + len(p) <= max_chars:
            chunks[-1] += " " + p
        else:
            chunks.append(p)
    return chunks

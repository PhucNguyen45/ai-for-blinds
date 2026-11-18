"""Chấm thô câu trả lời hỏi đáp theo từ khóa (KHÔNG phải điểm rubric, không đo độ bịa ngoài phạm vi đáp án).

Quy tắc: mọi số trong đáp án chuẩn phải có trong câu trả lời (ở dạng chữ số hoặc đọc bằng chữ); mọi cụm tên còn lại
(sau khi bỏ số và đơn vị) phải có mặt. Câu hỏi `refusal` (ảnh không cho biết) đúng khi model nói thẳng là không thấy/không xác định.
"""

import re
import unicodedata

from speech.vn_numbers import sn

UNITS = {"cm", "cm²", "m", "km", "kg", "g", "mm", "°", "°c", "%", "quyển", "độ", "xăng", "ti", "mét", "phần", "trăm",
         "học", "sinh", "quả", "ngày", "điểm", "huy", "chương", "thùng", "rác", "cái", "người", "bạn"}
REFUSAL = re.compile(r"không\s+(thấy|có thông tin|xác định|biết|đọc|nêu|cho biết|rõ|được ghi|có trên)|"
                     r"chưa\s+(thấy|xác định|biết|rõ)|trên trang không", re.I)


def norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower().replace(",", ".")
    return re.sub(r"\s+", " ", text).strip()


def _number_forms(raw: str) -> set[str]:
    value = float(raw)
    forms = {raw, raw.replace(".", ",")}
    if value.is_integer():
        forms.add(str(int(value)))
    forms.add(norm(sn(value if not value.is_integer() else int(value))))
    return forms


def score_answer(expected: str, qtype: str, answer: str) -> bool:
    ans = norm(answer)
    if qtype == "refusal":
        return bool(REFUSAL.search(ans))
    exp = norm(expected)
    numbers = re.findall(r"\d+(?:\.\d+)?", exp)
    for n in numbers:
        if not any(re.search(rf"(?<![\d.]){re.escape(f)}(?![\d])", ans) if f.replace('.', '').replace(',', '').isdigit()
                   else f in ans for f in _number_forms(n)):
            return False
    rest = re.sub(r"\d+(?:\.\d+)?", " ", exp)
    words = [w for w in re.findall(r"[\wÀ-ỹ]+", rest) if w not in UNITS and len(w) > 0]
    if not words:
        return True
    needle = " ".join(words)
    return needle in ans or all(w in ans for w in words)

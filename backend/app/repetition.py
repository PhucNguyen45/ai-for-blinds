"""Chặn lời mô tả / câu trả lời bị lặp trước khi app đọc to.

Mô hình nhỏ giải mã tham lam (greedy, nhiệt độ thấp) đôi khi rơi vào vòng lặp: nhắc lại một câu hay
một cụm cho tới hết giới hạn token. Thẻ mô hình Peppercorn-0.3b (DuyTa, 10/2026) đo được 2,8% trang bị
lặp ở mô hình 0,3 tỷ tham số và chặn bằng cách dò phần đuôi văn bản. Với học sinh khiếm thị, lặp nghĩa
là phải nghe cùng một câu nhiều lần, nên backend cắt trước khi trả về.

Mã ở đây viết riêng cho văn nói tiếng Việt của SgBe (không bảng, không Markdown), không dùng mã của
Peppercorn (giấy phép của họ không cho sao chép). Hai lớp:

1. Theo câu: một khối 1–4 câu giống hệt nhau xuất hiện liền nhau từ 3 lần, hoặc từ 2 lần mà kéo tới hết
   văn bản (dấu hiệu chạm giới hạn token). Giữ bản đầu, bỏ các bản lặp, giữ phần sau nếu mô hình đã thoát
   vòng lặp.
2. Theo ký tự (vòng lặp không có dấu câu, ví dụ "và các số liệu và các số liệu ..."): đuôi văn bản là một
   đoạn p ký tự lặp từ 4 lần, dài từ 120 ký tự. Giữ một bản.

Ngưỡng chọn để không cắt nhầm văn liệt kê bình thường ("cột thứ nhất cao mười, cột thứ hai cao mười")
hay một câu nhắc lại một lần; kiểm bằng tests/test_repetition.py.
"""
from __future__ import annotations

import re
import unicodedata

_SENTENCE = re.compile(r"[^.!?…\n]+(?:[.!?…]+|\n|$)")
MAX_BLOCK = 4           # khối lặp tối đa bao nhiêu câu
MIN_BLOCK_CHARS = 12    # khối quá ngắn ("Có.", "Đúng rồi.") không tính
MIN_REPEATS = 3         # lặp giữa chừng: từ 3 bản
MIN_REPEATS_AT_END = 2  # lặp tới cuối văn bản: từ 2 bản
CHAR_MAX_PERIOD = 200
CHAR_MIN_REPEATS = 4
CHAR_MIN_SPAN = 120


def _key(s: str) -> str:
    s = unicodedata.normalize("NFC", s).lower()
    return re.sub(r"[\s.!?…,;:]+", " ", s).strip()


def _sentences(text: str) -> list[tuple[int, int, str]]:
    out = []
    for m in _SENTENCE.finditer(text):
        k = _key(m.group())
        if k:
            out.append((m.start(), m.end(), k))
    return out


def _cut_sentence_loops(text: str) -> str:
    """Bỏ các bản lặp của khối câu; lặp lại tới khi không còn khối nào lặp."""
    while True:
        sents = _sentences(text)
        n = len(sents)
        cut = None
        for i in range(n):
            for k in range(1, MAX_BLOCK + 1):
                if i + 2 * k > n:
                    break
                block = [s[2] for s in sents[i:i + k]]
                if sum(len(b) for b in block) < MIN_BLOCK_CHARS:
                    continue
                reps = 1
                while i + (reps + 1) * k <= n and [s[2] for s in sents[i + reps * k:i + (reps + 1) * k]] == block:
                    reps += 1
                run_end = i + reps * k  # chỉ số câu đầu tiên sau đoạn lặp
                # bản cuối bị cắt dở (chạm giới hạn token): câu kế tiếp là tiền tố của câu tương ứng trong khối
                tail_partial = run_end == n - 1 and block[0].startswith(sents[-1][2])
                at_end = run_end == n or tail_partial
                if reps >= MIN_REPEATS or (reps >= MIN_REPEATS_AT_END and at_end):
                    keep_until = sents[i + k - 1][1]
                    resume = sents[run_end][0] if run_end < n and not tail_partial else len(text)
                    cut = (keep_until, resume)
                    break
            if cut:
                break
        if not cut:
            return text
        head, rest = text[:cut[0]].rstrip(), text[cut[1]:].strip()
        text = f"{head} {rest}".strip() if rest else head


def _cut_char_loop(text: str) -> str:
    """Đuôi văn bản là một đoạn ký tự lặp liền nhau (cho phép bản cuối bị cắt dở)."""
    n = len(text)
    for p in range(2, min(CHAR_MAX_PERIOD, n // CHAR_MIN_REPEATS) + 1):
        for lag in range(p):  # bản cuối dở dang: bỏ `lag` ký tự cuối rồi so
            end = n - lag
            unit = text[end - p:end]
            if not unit.strip():
                continue
            reps = 1
            while end - (reps + 1) * p >= 0 and text[end - (reps + 1) * p:end - reps * p] == unit:
                reps += 1
            if reps >= CHAR_MIN_REPEATS and reps * p >= CHAR_MIN_SPAN and text[end:] == unit[:lag]:
                return text[:end - (reps - 1) * p].rstrip(" ,;:")
    return text


def cut_repetition(text: str) -> tuple[str, bool]:
    """Trả (văn bản đã bỏ phần lặp, có cắt hay không)."""
    if not text:
        return text, False
    out = _cut_char_loop(_cut_sentence_loops(text))
    return out, out != text

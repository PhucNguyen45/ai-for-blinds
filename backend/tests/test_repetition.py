"""Chặn lặp (app/repetition.py): cắt đúng vòng lặp, không cắt nhầm văn bình thường.

Văn bình thường lấy từ chính repo: kho thư viện data/library, ví dụ hợp đồng ai/contract/examples,
sách mẫu của app. Chạy: cd backend && pytest -q
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import REPO_ROOT  # noqa: E402
from app.repetition import cut_repetition  # noqa: E402

SENT = "Cột thứ Hai cao nhất, bốn mươi quyển."


def test_one_sentence_looping_to_token_limit():
    text = "Biểu đồ cột có năm cột. " + " ".join([SENT] * 12) + " Cột thứ Hai ca"
    out, cut = cut_repetition(text)
    assert cut
    assert out == "Biểu đồ cột có năm cột. " + SENT


def test_block_of_two_sentences_looping():
    block = "Phía bắc là dãy Hoàng Liên Sơn. Phía nam là đồng bằng sông Hồng."
    text = "Lược đồ vùng núi phía Bắc. " + " ".join([block] * 5)
    out, cut = cut_repetition(text)
    assert cut and out == "Lược đồ vùng núi phía Bắc. " + block


def test_loop_in_middle_then_recovers_keeps_the_rest():
    text = "Mở đầu bài học. " + " ".join([SENT] * 4) + " Cột thứ Năm thấp nhất, mười lăm quyển."
    out, cut = cut_repetition(text)
    assert cut
    assert out == f"Mở đầu bài học. {SENT} Cột thứ Năm thấp nhất, mười lăm quyển."


def test_loop_without_punctuation():
    text = "Hình vẽ gồm " + "các bộ phận của cây và " * 15 + "các bộ"
    out, cut = cut_repetition(text)
    assert cut
    assert out.count("các bộ phận của cây") == 1
    assert len(out) < 60


def test_case_and_spacing_differences_still_count_as_repeats():
    text = "Trang có hai hình. " + "Hình một là cây đậu.  hình một là cây đậu. HÌNH MỘT LÀ CÂY ĐẬU. "
    out, cut = cut_repetition(text.strip())
    assert cut and out == "Trang có hai hình. Hình một là cây đậu."


@pytest.mark.parametrize("text", [
    # liệt kê giống nhau về hình thức nhưng khác nội dung
    "Cột thứ nhất cao mười. Cột thứ hai cao mười. Cột thứ ba cao mười. Cột thứ tư cao mười.",
    # một câu nhắc lại đúng một lần ở giữa (không phải vòng lặp)
    f"{SENT} {SENT} Cột thứ Năm thấp nhất, mười lăm quyển.",
    # câu ngắn lặp ("Có.") không tính
    "Có. Có. Có. Trang này có ba hình.",
    # số liệu lặp ngắn trong một câu
    "Ba tháng đầu năm đều có mười, mười, mười ngày mưa.",
    # chuỗi gạch, chấm ngắn
    "Điền vào chỗ trống: Hôm nay em ..........",
    "",
])
def test_normal_text_is_not_cut(text):
    assert cut_repetition(text) == (text, False)


def _real_texts():
    texts = []
    for f in sorted((REPO_ROOT / "data" / "library").glob("*/manifest.json")):
        for p in json.loads(f.read_text(encoding="utf-8"))["pages"]:
            texts.append((f"{f.parent.name}/{p['page']}", p["description"]))
    for f in sorted((REPO_ROOT / "ai" / "contract" / "examples").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for key in ("interpretation_vi", "summary_vi", "answer_vi"):
            if d.get(key):
                texts.append((f"{f.stem}.{key}", d[key]))
    sample = REPO_ROOT / "frontend" / "assets" / "library" / "sach_mau.json"
    if sample.exists():
        for b in json.loads(sample.read_text(encoding="utf-8"))["books"]:
            for p in b["pages"]:
                texts.append((f"{b['id']}/{p['number']}", p["text"]))
    return texts


def test_no_false_cut_on_real_descriptions_in_repo():
    texts = _real_texts()
    assert len(texts) >= 10, "thiếu văn mẫu để kiểm"
    wrongly_cut = [name for name, t in texts if cut_repetition(t)[1]]
    assert wrongly_cut == []

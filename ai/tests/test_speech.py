import pytest

from speech.tts_text import prepare_for_speech, split_for_streaming


@pytest.mark.parametrize("src,expected", [
    ("Cột Thứ Hai là 40 quyển.", "Cột Thứ Hai là bốn mươi quyển."),
    ("Chiếm 35% tổng số.", "Chiếm ba mươi lăm phần trăm tổng số."),
    ("Nhiệt độ 29°C vào tháng 5.", "Nhiệt độ hai mươi chín độ C vào tháng năm."),
    ("Điểm trung bình 8,5.", "Điểm trung bình tám phẩy năm."),
    ("Có 1.250 học sinh.", "Có một nghìn hai trăm năm mươi học sinh."),
    ("Chiều dài 12 cm và 3,5 m.", "Chiều dài mười hai xăng ti mét và ba phẩy năm mét."),
    ("**Chủ đề:** biểu đồ cột", "Chủ đề: biểu đồ cột"),
    ("A -> B -> C", "A rồi B rồi C"),
])
def test_prepare_for_speech(src, expected):
    assert prepare_for_speech(src) == expected


def test_no_digit_or_markup_left():
    out = prepare_for_speech("# Bảng\n- Tháng 5: 21 ngày (30%)\n- Tháng 6: 18 ngày")
    assert not any(c.isdigit() for c in out) and not any(c in out for c in "#*%-")


def test_split_respects_limit_and_keeps_text():
    text = ("Biểu đồ cột cho biết số sách mượn mỗi ngày. " * 12).strip()
    chunks = split_for_streaming(text, max_chars=120)
    assert all(len(c) <= 120 for c in chunks) and len(chunks) > 1
    assert " ".join(chunks).replace("  ", " ") == text


def test_split_long_sentence_without_period():
    text = ", ".join(f"mục số {i}" for i in range(80))
    chunks = split_for_streaming(text, max_chars=100)
    assert all(len(c) <= 100 for c in chunks)
    assert "".join(chunks).replace(" ", "") == text.replace(" ", "")

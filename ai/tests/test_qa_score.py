import pytest

from evaluation.reporting.qa_score import score_answer


@pytest.mark.parametrize("expected,qtype,answer,ok", [
    ("20%", "lookup", "Phần Thủy điện chiếm hai mươi phần trăm.", True),
    ("20%", "lookup", "Chiếm 20 phần trăm.", True),
    ("20%", "lookup", "Chiếm ba mươi phần trăm.", False),
    ("55%", "computation", "Cộng lại là năm mươi lăm phần trăm.", True),
    ("6 cm²", "computation", "Diện tích là sáu xăng ti mét vuông.", True),
    ("8,5", "lookup", "Điểm là tám phẩy năm.", True),
    ("Điện mặt trời", "comparison", "Điện mặt trời chiếm nhiều nhất.", True),
    ("Điện mặt trời", "comparison", "Thủy điện chiếm nhiều nhất.", False),
    ("A", "lookup", "Tam giác vuông tại đỉnh A.", True),
    ("không xác định được từ ảnh", "refusal", "Trên trang không thấy thông tin đó.", True),
    ("không xác định được từ ảnh", "refusal", "Giá trị chính là bốn mươi.", False),
])
def test_score_answer(expected, qtype, answer, ok):
    assert score_answer(expected, qtype, answer) is ok

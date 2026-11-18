import pytest

from vlm.calc import safe_eval, spoken


@pytest.mark.parametrize("expr,value", [
    ("40+35+5+19+6", 105), ("3*4/2", 6), ("(8,5+8+7,5)/3", 8), ("2*(5+8)", 26), ("-3+10", 7), ("12 / 4", 3), ("sqrt(3*3+4*4)", 5), ("3x4", 12), ("sqrt(16)+1", 5),
])
def test_valid_expressions(expr, value):
    assert safe_eval(expr) == pytest.approx(value)


@pytest.mark.parametrize("expr", [
    "", "abc", "__import__('os')", "2**10", "10//3", "1/0", "5%2", "1;2", "(" * 50 + "1" + ")" * 50 + "+" + "1" * 80,
    "lambda: 1", "[1,2]", "True+1", "sqrt(-4)", "sqrt", "sqrt(sqrt)", "xyz",
])
def test_invalid_expressions_are_rejected(expr):
    assert safe_eval(expr) is None


def test_spoken_rounds_and_reads_in_words():
    assert spoken(105.0) == "một trăm linh năm"
    assert spoken(8.5) == "tám phẩy năm"
    assert spoken(2 / 3) == "không phẩy sáu bảy"

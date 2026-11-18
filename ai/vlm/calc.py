"""Tính toán an toàn cho hỏi đáp: model chỉ viết biểu thức, MÃ tính ra kết quả.

Lý do: model 4B hay cộng sai (đã đo: 40 + 35 + 5 + 19 + 6 nói thành 51). Biểu thức chỉ được gồm số, + - * / ngoặc và `sqrt(...)` (căn bậc hai, cần cho cạnh huyền);
mọi thứ khác bị từ chối (không `eval`, không lũy thừa, giới hạn độ dài).
"""

from __future__ import annotations

import ast
import math
import operator
import re

from speech.vn_numbers import sn

MAX_EXPR_CHARS = 80
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def safe_eval(expression: str) -> float | None:
    """Giá trị của biểu thức số học đơn giản; None nếu biểu thức không hợp lệ hoặc không tính được."""
    expr = (expression or "").strip().replace(",", ".").replace("×", "*").replace("÷", "/")
    expr = re.sub(r"(?<=[\d)\s])x(?=[\d(\s])", "*", expr)  # "3x4" -> "3*4" (không đụng tới chữ khác)
    if not expr or len(expr) > MAX_EXPR_CHARS or not re.fullmatch(r"(?:sqrt|[\d\s.+\-*/()])+", expr):
        return None
    try:
        return float(_walk(ast.parse(expr, mode="eval").body))
    except (SyntaxError, ValueError, ZeroDivisionError, RecursionError, OverflowError):
        return None


def _walk(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_walk(node.left), _walk(node.right))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        v = _walk(node.operand)
        return v if isinstance(node.op, ast.UAdd) else -v
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "sqrt"
            and len(node.args) == 1 and not node.keywords):
        return math.sqrt(_walk(node.args[0]))
    raise ValueError("biểu thức không được phép")


def spoken(value: float) -> str:
    """Kết quả đọc bằng chữ tiếng Việt (làm tròn tối đa hai chữ số thập phân)."""
    value = round(value, 2)
    return sn(int(value) if float(value).is_integer() else value)

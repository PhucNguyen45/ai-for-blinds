"""Làm sạch đầu ra của mô hình thành văn nói thuần cho TTS.

Điều kiện Cổng 1: không có ký hiệu markdown trong lời đọc.
"""
import re

_FENCE = re.compile(r"```[a-zA-Z]*\n?|```")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s*", re.M)
_BULLET = re.compile(r"^\s*[-*+•]\s+", re.M)
_QUOTE = re.compile(r"^\s*>\s?", re.M)
_TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", re.M)
_EMPH = re.compile(r"(\*\*|__|\*|`)")
_SPACES = re.compile(r"[ \t]+")
_BLANKS = re.compile(r"\n{3,}")


def clean_for_speech(text: str) -> str:
    if not text:
        return ""
    t = _FENCE.sub("", text)
    t = _LINK.sub(r"\1", t)
    t = _TABLE_RULE.sub("", t)
    t = _HEADING.sub("", t)
    t = _BULLET.sub("", t)
    t = _QUOTE.sub("", t)
    t = _EMPH.sub("", t)
    # dòng bảng "| a | b |" -> "a, b"
    lines = []
    for line in t.split("\n"):
        if "|" in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            line = ", ".join(c for c in cells if c)
        lines.append(line.strip())
    t = "\n".join(lines)
    t = t.replace("#", "")
    t = _SPACES.sub(" ", t)
    t = _BLANKS.sub("\n\n", t)
    return t.strip()

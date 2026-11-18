"""Băm ảnh để phát hiện trùng lặp: SHA-256 (trùng chính xác) và pHash 64 bit (trùng gần: resize, nén lại, quét lại).

pHash: ảnh xám 32×32, DCT 2 chiều, lấy khối 8×8 tần số thấp, so với trung vị (bỏ hệ số DC). Khoảng cách Hamming nhỏ nghĩa là
ảnh giống nhau về bố cục tổng thể. Không bền với ảnh bị cắt (crop) mạnh; hạn chế này được ghi trong báo cáo.
"""

from __future__ import annotations

import hashlib
import io
import re
import unicodedata
from functools import lru_cache

import numpy as np
from PIL import Image

N = 32


@lru_cache(maxsize=1)
def _dct_matrix():
    k = np.arange(N)[:, None]
    n = np.arange(N)[None, :]
    m = np.cos(np.pi * (2 * n + 1) * k / (2 * N)) * np.sqrt(2 / N)
    m[0] /= np.sqrt(2)
    return m


def phash(img: Image.Image) -> int:
    gray = np.asarray(img.convert("L").resize((N, N), Image.LANCZOS), dtype=np.float64)
    d = _dct_matrix()
    low = (d @ gray @ d.T)[:8, :8].flatten()
    med = np.median(low[1:])
    bits = (low > med).astype(np.uint8)
    return int("".join(map(str, bits)), 2)


def describe(data: bytes) -> dict:
    """SHA-256, pHash (hex 16 ký tự), kích thước; ảnh hỏng trả về lỗi thay vì ném ngoại lệ."""
    sha = hashlib.sha256(data).hexdigest()
    try:
        with Image.open(io.BytesIO(data)) as im:
            im.load()
            return {"sha256": sha, "phash": f"{phash(im):016x}", "width": im.width, "height": im.height, "bytes": len(data)}
    except Exception as exc:  # noqa: BLE001 - ghi nhận ảnh hỏng, không dừng cả bộ
        return {"sha256": sha, "phash": None, "width": None, "height": None, "bytes": len(data), "error": type(exc).__name__}


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def norm_text(text: str) -> str:
    """Chuẩn hóa văn bản để so trùng chú thích/câu hỏi: NFC, chữ thường, bỏ dấu câu và khoảng trắng thừa."""
    t = unicodedata.normalize("NFC", text or "").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", t)).strip()


def text_hash(text: str) -> str:
    return hashlib.sha256(norm_text(text).encode("utf-8")).hexdigest()

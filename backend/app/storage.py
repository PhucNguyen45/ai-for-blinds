"""Lưu ảnh tạm, bộ nhớ đệm kết quả và nhật ký yêu cầu (đều là file trong data/)."""
import hashlib
import io
import json
import re
import threading
import time
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageOps, UnidentifiedImageError

from .config import settings

_IMAGE_ID = re.compile(r"^[0-9a-f]{16}$")
_log_lock = threading.Lock()


class InvalidImage(Exception):
    pass


class ImageTooLarge(Exception):
    pass


def _dir(name: str) -> Path:
    path = settings.data_dir / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def prepare_image(raw: bytes) -> Tuple[str, str, bytes]:
    """Kiểm tra ảnh, xoay theo EXIF, thu về cạnh dài tối đa IMAGE_MAX_SIDE, nén JPEG.

    Trả (image_id, sha256 của ảnh gốc, jpeg đã xử lý).
    """
    if not raw:
        raise InvalidImage("Ảnh rỗng")
    if len(raw) > settings.max_image_mb * 1024 * 1024:
        raise ImageTooLarge(f"Ảnh lớn hơn {settings.max_image_mb:g} MB")
    sha = hashlib.sha256(raw).hexdigest()
    try:
        img = Image.open(io.BytesIO(raw))
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImage(str(exc))
    img.thumbnail((settings.image_max_side, settings.image_max_side))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return sha[:16], sha, buf.getvalue()


def save_image(image_id: str, jpeg: bytes, description: str) -> None:
    images = _dir("images")
    (images / f"{image_id}.jpg").write_bytes(jpeg)
    (images / f"{image_id}.json").write_text(
        json.dumps({"description": description}, ensure_ascii=False), encoding="utf-8"
    )


def load_image(image_id: str) -> Optional[Tuple[bytes, str]]:
    if not _IMAGE_ID.match(image_id):
        return None
    images = _dir("images")
    jpg, meta = images / f"{image_id}.jpg", images / f"{image_id}.json"
    if not jpg.is_file():
        return None
    description = ""
    if meta.is_file():
        description = json.loads(meta.read_text(encoding="utf-8")).get("description", "")
    return jpg.read_bytes(), description


def _cache_path(sha: str, page_type: str) -> Path:
    key = hashlib.sha256(
        f"{sha}|{page_type}|{settings.model_name}|{settings.prompt_version}".encode()
    ).hexdigest()
    return _dir("cache") / f"{key}.json"


def cache_get(sha: str, page_type: str) -> Optional[dict]:
    path = _cache_path(sha, page_type)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def cache_put(sha: str, page_type: str, result: dict) -> None:
    _cache_path(sha, page_type).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")


def log_request(**fields) -> None:
    """Ghi một dòng JSON vào data/logs/requests.jsonl — đầu vào cho bảng đánh giá."""
    fields.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    line = json.dumps(fields, ensure_ascii=False)
    with _log_lock:
        with open(_dir("logs") / "requests.jsonl", "a", encoding="utf-8") as f:
            f.write(line + "\n")

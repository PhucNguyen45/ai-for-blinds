"""
Money service — Vietnamese banknote (VND) denomination recognition.

Two-tier strategy (aligned with the SgBE proposal's multi-task
"detection + recognition" design):
1. If a custom YOLO banknote model exists at ``vnd_yolo_model_path``,
   use it (detection + denomination classification).
2. Otherwise fall back to Gemini VLM which reads the denomination
   from the note image directly — no training data required.

Returns structured results: denomination, formatted, method, confidence.
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

from backend.config import settings

# 9 official polymer/paper VND denominations.
VND_DENOMINATIONS = {
    "1000": "1.000 đồng",
    "2000": "2.000 đồng",
    "5000": "5.000 đồng",
    "10000": "10.000 đồng",
    "20000": "20.000 đồng",
    "50000": "50.000 đồng",
    "100000": "100.000 đồng",
    "200000": "200.000 đồng",
    "500000": "500.000 đồng",
}


def canonical_denomination(raw: str | int | None) -> str | None:
    """
    Normalize a raw denomination label to a canonical key of
    ``VND_DENOMINATIONS`` (e.g. "100_000", "100k", "100,000" → "100000").
    """
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if not s:
        return None
    s = (
        s.replace("đồng", "")
        .replace("vnd", "")
        .replace(".", "")
        .replace(",", "")
        .replace("_", "")
        .replace(" ", "")
    )
    if not s:
        return None
    if s.endswith("k"):
        num = s[:-1]
        if not num.isdigit():
            return None
        s = str(int(num) * 1000)
    elif not s.isdigit():
        digits = "".join(ch for ch in s if ch.isdigit())
        if not digits:
            return None
        s = digits
    if s in VND_DENOMINATIONS:
        return s
    return None


def format_denomination(denomination: str | None) -> str | None:
    """Return the human-readable Vietnamese label for a denomination."""
    if not denomination:
        return None
    return VND_DENOMINATIONS.get(denomination)


class MoneyService:
    """Vietnamese banknote recognition (lazy singleton)."""

    def __init__(self) -> None:
        self._yolo_model: Any = None

    # ── YOLO tier (optional) ──────────────────────────────────
    @property
    def _yolo_available(self) -> bool:
        if self._yolo_model is not None:
            return True
        try:
            import os

            from ultralytics import YOLO

            model_path = settings.vnd_yolo_model_path
            if not os.path.exists(model_path):
                logger.warning(f"VND YOLO model not found at {model_path}")
                return False
            self._yolo_model = YOLO(model_path)
            logger.info(f"VND YOLO model loaded from {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load VND YOLO model: {e}")
            return False

    def _recognize_yolo(self, image_bytes: bytes) -> dict | None:
        try:
            import io

            import cv2
            import numpy as np
            from PIL import Image

            image = Image.open(io.BytesIO(image_bytes))
            img_array = np.array(image)
            if img_array.ndim == 3 and img_array.shape[2] == 4:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)

            results = self._yolo_model(img_array, conf=settings.money_confidence)[0]
            if results.boxes is None or len(results.boxes) == 0:
                return None

            names = getattr(self._yolo_model, "names", {})
            best = None  # (confidence, denomination)
            for cls, conf in zip(results.boxes.cls, results.boxes.conf):
                cls_id = int(cls.item())
                conf_val = float(conf)
                label = names.get(cls_id, "") if isinstance(names, dict) else ""
                denom = canonical_denomination(label)
                if denom is None:
                    continue
                if best is None or conf_val > best[0]:
                    best = (conf_val, denom)

            if best is None:
                return None

            confidence, denom = best
            return {
                "denomination": denom,
                "formatted": format_denomination(denom),
                "method": "yolo",
                "confidence": round(confidence, 3),
            }
        except Exception as e:
            logger.error(f"VND YOLO recognition error: {e}")
            return None

    # ── VLM tier (default) ────────────────────────────────────
    @staticmethod
    def _parse_vlm_json(text: str | None) -> dict | None:
        if not text or not isinstance(text, str):
            return None
        try:
            cleaned = re.sub(r"```(?:json)?", "", text).strip()
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1:
                return None
            payload = json.loads(cleaned[start : end + 1])
            return payload if isinstance(payload, dict) else None
        except Exception:
            return None

    def _recognize_vlm(self, image_bytes: bytes, mime_type: str) -> dict | None:
        if not settings.google_api_key:
            return None
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.google_api_key)
            model = genai.GenerativeModel(settings.gemini_model)

            prompt = (
                "Bạn là trợ lý cho người khiếm thị Việt Nam. Hãy xác định mệnh giá "
                "tờ tiền Việt Nam trong ảnh.\n"
                "Chỉ trả về một đối tượng JSON hợp lệ có dạng:\n"
                '{"denomination": "100000", "currency": "VND", "confidence": 0.95}\n'
                "denomination là mệnh giá dạng số nguyên không dấu phẩy "
                '(ví dụ "100000" cho tờ 100.000 đồng).\n'
                'Nếu ảnh không phải tờ tiền Việt Nam, trả về '
                '{"denomination": null, "currency": "", "confidence": 0}.'
            )
            response = model.generate_content(
                [
                    prompt,
                    {"mime_type": mime_type, "data": image_bytes},
                ]
            )

            data = self._parse_vlm_json(getattr(response, "text", None))
            if data is None:
                return None

            denom = canonical_denomination(data.get("denomination"))
            try:
                confidence = round(float(data.get("confidence", 0.0)), 3)
            except (TypeError, ValueError):
                confidence = 0.0

            return {
                "denomination": denom,
                "formatted": format_denomination(denom),
                "method": "vlm",
                "confidence": confidence,
            }
        except Exception as e:
            logger.error(f"VND VLM recognition error: {e}")
            return None

    # ── Public API ────────────────────────────────────────────
    def recognize(self, image_bytes: bytes, mime_type: str) -> dict | None:
        """
        Recognize a Vietnamese banknote denomination.

        Returns None when no recognition method is available; otherwise a
        result dict (denomination may be None when no note is detected).
        """
        if self._yolo_available:
            result = self._recognize_yolo(image_bytes)
            if result is not None:
                return result
        return self._recognize_vlm(image_bytes, mime_type)


# Singleton instance
money_service = MoneyService()

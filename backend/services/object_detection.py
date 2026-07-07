"""Object Detection Service using Ultralytics YOLOv8 with Vietnamese labels."""

import logging

logger = logging.getLogger(__name__)

# Vietnamese label map for COCO classes commonly relevant to students
VIETNAMESE_LABELS = {
    0: "người",
    1: "xe đạp",
    2: "xe hơi",
    3: "xe máy",
    4: "máy bay",
    5: "xe buýt",
    6: "tàu hỏa",
    7: "xe tải",
    8: "thuyền",
    9: "đèn giao thông",
    10: "biển báo",
    11: "vòi chữa cháy",
    12: "biển dừng",
    13: "máy đỗ xe",
    14: "ghế dài",
    15: "chim",
    16: "mèo",
    17: "chó",
    18: "ngựa",
    19: "cừu",
    20: "bò",
    21: "voi",
    22: "gấu",
    23: "ngựa vằn",
    24: "hươu cao cổ",
    25: "ba lô",
    26: "ô",
    27: "túi xách",
    28: "cà vạt",
    29: "va li",
    30: "đĩa bay",
    31: "ván trượt",
    32: "ván lướt",
    33: "vợt tennis",
    34: "chai",
    35: "ly",
    36: "bát",
    37: "thìa",
    38: "dao",
    39: "nĩa",
    40: "kéo",
    41: "bát nhỏ",
    42: "chuối",
    43: "táo",
    44: "bánh mì",
    45: "cam",
    46: "bông cải",
    47: "cà rốt",
    48: "xúc xích",
    49: "pizza",
    50: "bánh rán",
    51: "bánh ngọt",
    52: "ghế",
    53: "sofa",
    54: "chậu cây",
    55: "giường",
    56: "bàn",
    57: "nhà vệ sinh",
    58: "màn hình",
    59: "laptop",
    60: "chuột máy tính",
    61: "điều khiển",
    62: "bàn phím",
    63: "điện thoại",
    64: "lò vi sóng",
    65: "lò nướng",
    66: "tủ lạnh",
    67: "máy giặt",
    68: "máy sấy",
    69: "bồn rửa",
    70: "nồi",
    71: "ấm đun nước",
    72: "nồi cơm điện",
    73: "lẩu",
    74: "cốc",
    75: "cốc thủy tinh",
    76: "cốc nhựa",
    77: "dao kéo",
    78: "thìa dĩa",
    79: "bát đĩa",
    80: "đũa",
    81: "bình hoa",
    82: "đồng hồ treo tường",
    83: "tạp chí",
    84: "sách",
    85: "tranh ảnh",
    86: "khung ảnh",
    87: "nến",
    88: "đèn bàn",
    89: "đèn trần",
    90: "gương",
    91: "tủ quần áo",
    92: "cửa",
    93: "cửa sổ",
    94: "rèm cửa",
    95: "thảm",
    96: "giường ngủ",
    97: "chăn",
    98: "gối",
    99: "nệm",
}


class ObjectDetectionService:
    """YOLOv8 object detection with Vietnamese labels."""

    def __init__(self):
        self._model = None
        self._device = None

    @property
    def available(self) -> bool:
        return self._ensure_model()

    def _ensure_model(self) -> bool:
        if self._model is not None:
            return True
        try:
            import os

            from ultralytics import YOLO

            from backend.config import settings

            model_path = settings.yolo_model_path
            if not os.path.exists(model_path):
                logger.warning(f"YOLO model not found at {model_path}")
                return False

            self._model = YOLO(model_path)
            self._device = settings.yolo_device if hasattr(settings, "yolo_device") else "cpu"
            logger.info(f"YOLOv8 loaded on {self._device}")
            return True
        except Exception as e:
            logger.error(f"Failed to load YOLO: {e}")
            return False

    def detect(self, image_bytes: bytes, confidence: float = 0.5) -> dict | None:
        """
        Detect objects in image. Returns structured result with Vietnamese labels.

        Returns: {
            "objects": [
                {"label": "người", "confidence": 0.95,
                 "bbox": {"x1": 100, "y1": 200, "x2": 300, "y2": 500}},
                ...
            ],
            "object_count": 3,
            "scene_description": "Trong ảnh có 3 vật thể..."
        }
        """
        if not self._ensure_model():
            return None

        try:
            import io

            import cv2
            import numpy as np
            from PIL import Image

            # Read image
            image = Image.open(io.BytesIO(image_bytes))
            img_array = np.array(image)
            if img_array.shape[2] == 4:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)

            # Run detection
            results = self._model(img_array, conf=confidence, device=self._device)
            result = results[0]

            objects = []
            if result.boxes is not None:
                for box, cls, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                    x1, y1, x2, y2 = [int(v) for v in box.tolist()]
                    cls_id = int(cls.item())
                    label = VIETNAMESE_LABELS.get(cls_id, f"vật thể số {cls_id}")
                    objects.append(
                        {
                            "label": label,
                            "confidence": round(float(conf), 3),
                            "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                        }
                    )

            # Generate scene description in Vietnamese
            from collections import Counter

            label_counts = Counter(obj["label"] for obj in objects)
            desc_parts = [f"{count} {label}" for label, count in label_counts.most_common(5)]
            scene_desc = (
                f"Trong ảnh có {len(objects)} vật thể: {', '.join(desc_parts)}."
                if objects
                else "Không phát hiện vật thể nào."
            )

            return {
                "objects": objects,
                "object_count": len(objects),
                "scene_description": scene_desc,
            }

        except Exception as e:
            logger.error(f"Detection error: {e}")
            return None


# Singleton
object_detection_service = ObjectDetectionService()

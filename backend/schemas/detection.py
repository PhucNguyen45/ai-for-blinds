"""Detection schemas for YOLOv8 object detection."""

from pydantic import BaseModel, Field
from typing import Optional


class BoundingBox(BaseModel):
    x1: int = Field(..., description="Tọa độ X góc trên trái")
    y1: int = Field(..., description="Tọa độ Y góc trên trái")
    x2: int = Field(..., description="Tọa độ X góc dưới phải")
    y2: int = Field(..., description="Tọa độ Y góc dưới phải")


class DetectedObject(BaseModel):
    label: str = Field(..., description="Tên vật thể bằng tiếng Việt")
    confidence: float = Field(..., ge=0, le=1, description="Độ tin cậy (0-1)")
    bbox: BoundingBox = Field(..., description="Tọa độ khung bao quanh vật thể")


class DetectionResponse(BaseModel):
    success: bool = True
    message: str = "Phát hiện vật thể thành công"
    data: Optional[dict] = None

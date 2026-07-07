"""
POST /detect — Object Detection with YOLOv8 in Vietnamese.

Detects objects in uploaded images and returns results with
Vietnamese labels and bounding box coordinates.
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from backend.api.auth import verify_api_key
from backend.deps import limiter
from backend.services.object_detection import object_detection_service
from backend.utils.file_handler import validate_image
from backend.utils.response_builder import success_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/detect")
@limiter.limit("10/minute")
async def detect_objects(
    request: Request,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    """Phát hiện vật thể trong ảnh bằng YOLOv8. Trả về danh sách vật thể kèm vị trí."""

    if not object_detection_service.available:
        raise HTTPException(status_code=503, detail="YOLOv8 model not available")

    image_data = validate_image(file)

    try:
        result = object_detection_service.detect(image_data)
        if result is None:
            raise HTTPException(status_code=502, detail="Detection failed")

        return success_response(
            data=result,
            message=f"Phát hiện {result['object_count']} vật thể",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection error: {e}")
        raise HTTPException(status_code=500, detail="Internal detection error")

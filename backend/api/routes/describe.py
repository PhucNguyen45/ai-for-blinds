"""
POST /describe — Image description with Gemini 2.5 Flash in Vietnamese.

Part of the VLM (Vision-Language Model) service.
"""

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from backend.api.auth import verify_api_key
from backend.main import limiter
from backend.services.vlm_service import vlm_service
from backend.utils.file_handler import validate_image
from backend.utils.response_builder import success_response

router = APIRouter()


@router.post("/describe")
@limiter.limit("10/minute")
async def describe_image(
    request: Request,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    """
    Mô tả ảnh bằng tiếng Việt cho học sinh khiếm thị.

    Sử dụng Gemini 2.5 Flash để phân tích và mô tả nội dung ảnh.
    Trả về mô tả chi tiết bằng tiếng Việt tự nhiên.
    """
    contents = validate_image(file)

    description = vlm_service.describe(contents, file.content_type)
    if description is None:
        raise HTTPException(
            status_code=502,
            detail="Không thể mô tả ảnh. Vui lòng thử lại sau.",
        )

    return success_response(data={"description": description})

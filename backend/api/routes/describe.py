"""
POST /describe — Image description with Gemini 2.5 Flash in Vietnamese.

Part of the VLM (Vision-Language Model) service.
"""

from fastapi import APIRouter, UploadFile, File

from backend.services.vlm_service import vlm_service
from backend.utils.file_handler import validate_image
from backend.utils.response_builder import success_response, error_response

router = APIRouter()


@router.post("/describe")
async def describe_image(file: UploadFile = File(...)):
    """
    Mô tả ảnh bằng tiếng Việt cho học sinh khiếm thị.

    Sử dụng Gemini 2.5 Flash để phân tích và mô tả nội dung ảnh.
    Trả về mô tả chi tiết bằng tiếng Việt tự nhiên.
    """
    contents = validate_image(file)

    description = vlm_service.describe(contents, file.content_type)
    if description is None:
        return error_response(
            message="Không thể mô tả ảnh. Vui lòng thử lại sau.",
            status_code=502,
        )

    return success_response(data={"description": description})

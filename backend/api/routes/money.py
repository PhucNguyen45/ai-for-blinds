"""
POST /money — Vietnamese banknote (VND) denomination recognition.

Recognizes the denomination of a VND banknote from a photo using
a two-tier strategy: an optional YOLO model, falling back to Gemini VLM.
"""

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from backend.api.auth import verify_api_key
from backend.deps import limiter
from backend.services.money_service import money_service
from backend.utils.file_handler import validate_image
from backend.utils.response_builder import error_response, success_response

router = APIRouter()


@router.post("/money")
@limiter.limit("10/minute")
async def recognize_money(
    request: Request,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    """
    Nhận dạng mệnh giá tờ tiền Việt Nam từ ảnh.

    Trả về mệnh giá chuẩn hóa (denomination), tên hiển thị (formatted),
    phương thức nhận dạng (method: yolo/vlm) và độ tin cậy (confidence).
    """
    contents = validate_image(file)

    result = money_service.recognize(contents, file.content_type or "image/jpeg")
    if result is None:
        return error_response(
            message="Nhận dạng tiền không khả dụng. Vui lòng kiểm tra cài đặt.",
            status_code=503,
        )

    if result.get("denomination") is None:
        return success_response(
            data=result,
            message="Không phát hiện tờ tiền Việt Nam trong ảnh.",
        )

    formatted = result.get("formatted") or "không xác định"
    return success_response(
        data=result,
        message=f"Nhận diện tờ tiền {formatted}",
    )

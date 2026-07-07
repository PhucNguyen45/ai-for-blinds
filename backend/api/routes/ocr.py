"""
POST /ocr — Optical Character Recognition with PaddleOCR.

Extracts Vietnamese text from images.
"""

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from backend.api.auth import verify_api_key
from backend.deps import limiter
from backend.services.ocr_service import ocr_service
from backend.utils.file_handler import validate_image
from backend.utils.response_builder import error_response, success_response

router = APIRouter()


@router.post("/ocr")
@limiter.limit("30/minute")
async def ocr_image(
    request: Request,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    """
    Nhận dạng văn bản từ ảnh bằng PaddleOCR.

    Hỗ trợ tiếng Việt và tiếng Anh.
    Trả về văn bản đã trích xuất.
    """
    if not ocr_service.available:
        return error_response(
            message="OCR không khả dụng. Vui lòng kiểm tra cài đặt PaddleOCR.",
            status_code=503,
        )

    contents = validate_image(file)

    text = ocr_service.extract_text(contents)
    if text is None:
        raise HTTPException(
            status_code=500,
            detail="Không thể trích xuất văn bản từ ảnh.",
        )

    return success_response(data={"text": text})

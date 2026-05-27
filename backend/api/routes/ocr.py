"""
POST /ocr — Optical Character Recognition with PaddleOCR.

Extracts Vietnamese text from images.
"""

from fastapi import APIRouter, UploadFile, File

from backend.services.ocr_service import ocr_service
from backend.utils.file_handler import validate_image
from backend.utils.response_builder import success_response, error_response

router = APIRouter()


@router.post("/ocr")
async def ocr_image(file: UploadFile = File(...)):
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
        return error_response(
            message="Không thể trích xuất văn bản từ ảnh.",
            status_code=500,
        )

    return success_response(data={"text": text})

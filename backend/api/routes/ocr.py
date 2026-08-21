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
    Nhận dạng văn bản từ ảnh.

    Dùng PaddleOCR nếu đã cài, ngược lại để VLM đọc chữ.
    Trả về văn bản đã trích xuất.
    """
    contents = validate_image(file)

    # Không chặn ở đây nữa: thiếu PaddleOCR thì service tự chuyển sang VLM.
    text = ocr_service.extract_text(contents, file.content_type)
    if text is None:
        return error_response(
            message="Không thể trích xuất văn bản từ ảnh.",
            status_code=500,
        )

    return success_response(data={"text": text})

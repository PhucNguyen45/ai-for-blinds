"""
POST /describe — Image description with Gemini 2.5 Flash in Vietnamese.

Part of the VLM (Vision-Language Model) service.
"""

from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile

from backend.services.vlm_service import vlm_service
from backend.utils.file_handler import validate_image
from backend.utils.response_builder import success_response, error_response

router = APIRouter()


@router.post("/describe")
async def describe_image(
    file: UploadFile = File(...),
    question: Optional[str] = Form(None),
    context: Optional[str] = Form(None),
    textbook_page: bool = Form(False),
):
    """
    Mô tả ảnh bằng tiếng Việt cho học sinh khiếm thị.

    Không truyền gì thêm thì trả về mô tả đầy đủ. Truyền `question` để hỏi
    thẳng một chi tiết trong ảnh — nhanh hơn và đỡ phải nghe lại từ đầu.
    Truyền `context` (ví dụ tên bài đang học) để mô tả bám nội dung đó.
    """
    contents = validate_image(file)

    if question and question.strip():
        description = vlm_service.answer_about_image(
            contents, file.content_type, question.strip()
        )
    elif context and context.strip():
        description = vlm_service.describe_with_context(
            contents, file.content_type, context.strip()
        )
    else:
        description = vlm_service.describe(
            contents, file.content_type, textbook_page=textbook_page
        )
    if description is None:
        return error_response(
            message="Không thể mô tả ảnh. Vui lòng thử lại sau.",
            status_code=502,
        )

    return success_response(data={"description": description})

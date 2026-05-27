"""
POST /stt — Speech-to-Text with Whisper/phoWhisper.

Transcribes Vietnamese speech to text.
"""

from fastapi import APIRouter, UploadFile, File, Form

from backend.services.stt_service import stt_service
from backend.utils.file_handler import validate_audio
from backend.utils.response_builder import success_response, error_response

router = APIRouter()


@router.post("/stt")
async def speech_to_text(
    file: UploadFile = File(...),
    language: str = Form("vi"),
):
    """
    Nhận dạng giọng nói tiếng Việt thành văn bản.

    Sử dụng PhoWhisper (tối ưu cho tiếng Việt) hoặc Whisper.
    Trả về văn bản đã nhận dạng kèm segments thời gian.
    """
    if not stt_service.available:
        return error_response(
            message="STT không khả dụng. Vui lòng kiểm tra cài đặt Whisper.",
            status_code=503,
        )

    audio_bytes = validate_audio(file)

    result = stt_service.transcribe(audio_bytes, language=language)
    if result is None:
        return error_response(
            message="Không thể nhận dạng giọng nói.",
            status_code=500,
        )

    return success_response(data=result)

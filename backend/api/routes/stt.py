"""
POST /stt — Speech-to-Text with Whisper/phoWhisper.

Transcribes Vietnamese speech to text.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from backend.api.auth import verify_api_key
from backend.deps import limiter
from backend.services.stt_service import stt_service
from backend.utils.file_handler import validate_audio
from backend.utils.response_builder import error_response, success_response

router = APIRouter()


@router.post("/stt")
@limiter.limit("10/minute")
async def speech_to_text(
    request: Request,
    file: UploadFile = File(...),
    language: str = Form("vi"),
    api_key: str = Depends(verify_api_key),
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
        raise HTTPException(
            status_code=500,
            detail="Không thể nhận dạng giọng nói.",
        )

    return success_response(data=result)

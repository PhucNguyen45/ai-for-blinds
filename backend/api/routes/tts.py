"""
POST /tts — Text-to-Speech with Edge TTS in Vietnamese.

Converts text to MP3 audio binary (not JSON).
Frontend plays the audio file directly.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.schemas.tts import TtsRequest
from backend.services.tts_service import tts_service
from backend.utils.response_builder import error_response

router = APIRouter()


@router.post("/tts")
async def text_to_speech(request: TtsRequest):
    """
    Chuyển văn bản thành giọng nói tiếng Việt.

    Trả về file audio/mpeg thay vì JSON để client phát ngay lập tức.
    Sử dụng Edge TTS với giọng Hoài My (vi-VN-HoaiMyNeural).
    Hỗ trợ đọc với cảm xúc cho văn học (phân vai, cảm xúc).
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Văn bản không được để trống.")

    if request.emotion != "neutral":
        output_path = await tts_service.synthesize_with_emotion(
            request.text, request.emotion, voice=request.voice
        )
    else:
        output_path = await tts_service.synthesize(request.text, voice=request.voice)

    if output_path is None:
        return error_response(
            message="Không thể tạo giọng nói. Vui lòng thử lại sau.",
            status_code=500,
        )

    return FileResponse(
        output_path,
        media_type="audio/mpeg",
        filename="speech.mp3",
        headers={
            "Content-Disposition": 'attachment; filename="speech.mp3"',
        },
    )

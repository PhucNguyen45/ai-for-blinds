"""
POST /tts — Text-to-Speech with Edge TTS in Vietnamese.

Converts text to MP3 audio binary (not JSON).
Frontend plays the audio file directly.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from backend.api.auth import verify_api_key
from backend.deps import limiter
from backend.schemas.tts import TtsRequest
from backend.services.tts_service import tts_service

router = APIRouter()


@router.post("/tts")
@limiter.limit("30/minute")
async def text_to_speech(
    request: Request,
    tts_request: TtsRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Chuyển văn bản thành giọng nói tiếng Việt.

    Trả về file audio/mpeg thay vì JSON để client phát ngay lập tức.
    Sử dụng Edge TTS với giọng Hoài My (vi-VN-HoaiMyNeural).
    Hỗ trợ đọc với cảm xúc cho văn học (phân vai, cảm xúc).
    """
    if not tts_request.text.strip():
        raise HTTPException(status_code=400, detail="Văn bản không được để trống.")

    if tts_request.emotion != "neutral":
        output_path = await tts_service.synthesize_with_emotion(
            tts_request.text, tts_request.emotion, voice=tts_request.voice
        )
    else:
        output_path = await tts_service.synthesize(tts_request.text, voice=tts_request.voice)

    if output_path is None:
        raise HTTPException(
            status_code=500,
            detail="Không thể tạo giọng nói. Vui lòng thử lại sau.",
        )

    return FileResponse(
        output_path,
        media_type="audio/mpeg",
        filename="speech.mp3",
        headers={
            "Content-Disposition": 'attachment; filename="speech.mp3"',
        },
    )

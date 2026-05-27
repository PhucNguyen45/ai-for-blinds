"""
TTS schemas — request/response validation for POST /tts.

Defines text-to-speech request parameters and response format.
Endpoint returns binary audio/mpeg, so no JSON response schema needed.
"""

from pydantic import BaseModel, Field


class TtsRequest(BaseModel):
    """Request schema for TTS endpoint."""
    text: str = Field(
        ...,
        min_length=1,
        description="Văn bản cần đọc thành tiếng",
        examples=["Xin chào, tôi là trợ lý học tập của bạn."],
    )
    voice: str | None = Field(
        None,
        description="Giọng đọc (mặc định: vi-VN-HoaiMyNeural)",
        examples=["vi-VN-HoaiMyNeural"],
    )
    emotion: str = Field(
        "neutral",
        description="Cảm xúc: neutral, happy, sad, angry, excited",
        examples=["neutral", "happy", "sad"],
    )

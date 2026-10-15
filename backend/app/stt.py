"""Nhận dạng giọng nói (mảng của Toàn).

Hiện chỉ có chế độ mock. Toàn thêm chế độ "phowhisper" vào hàm transcribe:
  - nạp vinai/PhoWhisper-base một lần (khởi tạo lười)
  - đổi âm thanh WAV/M4A sang 16 kHz mono rồi nhận dạng
Hợp đồng API giữ nguyên: vào là bytes âm thanh, ra là chuỗi văn bản.
"""
import asyncio

from .config import settings


class SttError(Exception):
    pass


async def transcribe(audio: bytes, filename: str) -> str:
    if settings.stt_mode == "mock":
        await asyncio.sleep(min(settings.mock_delay, 0.5))
        return settings.mock_stt_text
    raise SttError(f"Chưa cài chế độ STT '{settings.stt_mode}'")

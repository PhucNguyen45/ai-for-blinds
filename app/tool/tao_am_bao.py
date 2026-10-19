"""Sinh 4 âm báo trạng thái cho app (WAV mono 22.05 kHz, 16-bit).

Chạy lại khi muốn đổi âm: python tool/tao_am_bao.py
Âm do script tự tạo nên không vướng bản quyền.
"""
import math
import struct
import wave
from pathlib import Path

RATE = 22050
OUT = Path(__file__).resolve().parent.parent / "assets" / "audio"


def tone(freq: float, ms: int, volume: float = 0.5) -> list[float]:
    n = int(RATE * ms / 1000)
    fade = max(1, int(RATE * 0.008))  # 8 ms vào/ra để không bị tiếng "bụp"
    out = []
    for i in range(n):
        env = min(1.0, i / fade, (n - i) / fade)
        out.append(volume * env * math.sin(2 * math.pi * freq * i / RATE))
    return out


def silence(ms: int) -> list[float]:
    return [0.0] * int(RATE * ms / 1000)


def write(name: str, samples: list[float]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(s * 32767)) for s in samples))


# Chụp: một tiếng ngắn, cao, giống cửa trập
write("chup.wav", tone(1400, 70, 0.55))
# Đang chờ: hai nhịp nhẹ, phát lặp lại trong lúc máy chủ xử lý
write("cho.wav", tone(620, 90, 0.3) + silence(110) + tone(620, 90, 0.3))
# Xong: hai nốt đi lên
write("xong.wav", tone(660, 110, 0.5) + silence(30) + tone(990, 160, 0.5))
# Lỗi: hai nốt đi xuống, trầm hơn
write("loi.wav", tone(440, 170, 0.55) + silence(40) + tone(300, 260, 0.55))
print("Đã ghi:", sorted(p.name for p in OUT.glob("*.wav")))

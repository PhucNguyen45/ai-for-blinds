"""
Đo chất lượng và tốc độ nhận dạng giọng nói tiếng Việt.

Chạy từ gốc repo:
    .venv\\Scripts\\python.exe scripts\\bench_stt.py

Script tự sinh câu hỏi mẫu bằng Edge TTS (giọng thật, không phải file thu sẵn),
rồi cho từng model nghe lại và so với câu gốc. Kết quả: tỉ lệ lỗi từ (WER) và
thời gian xử lý — căn cứ để chọn kích thước model chạy trên server của trường.

WER càng thấp càng tốt. Thời gian tính trên CPU, vì server có thể không có GPU.
"""

import asyncio
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import edge_tts  # noqa: E402

from backend.config import settings  # noqa: E402

# Câu hỏi kiểu học sinh thật sự hỏi — có thuật ngữ SGK, có từ dễ nghe nhầm.
SENTENCES = [
    "Vì sao dân cư nước ta phân bố không đều",
    "Nguyên phân là gì",
    "Quá trình đô thị hoá diễn ra như thế nào",
    "Đồng bằng sông Hồng có mật độ dân số cao nhất cả nước",
    "Hãy đọc lại đoạn văn trang bốn mươi lăm",
]

# Bản CTranslate2 do cộng đồng convert sẵn — dùng luôn, khỏi cài torch để tự
# convert. PhoWhisper do VinAI fine-tune riêng cho tiếng Việt.
MODELS = [
    "tiny",
    "base",
    "small",
    "diepho/PhoWhisper-tiny-ct2",
    "diepho/PhoWhisper-base-ct2",
    "diepho/PhoWhisper-small-ct2",
]

AUDIO_DIR = Path("data/audio_samples")


def normalize(text: str) -> list[str]:
    """Bỏ dấu câu và viết hoa để so sánh công bằng."""
    text = re.sub(r"[.,!?;:\"'()]", " ", text.lower())
    return text.split()


def wer(reference: str, hypothesis: str) -> float:
    """Tỉ lệ lỗi từ, tính bằng khoảng cách Levenshtein trên đơn vị từ."""
    ref, hyp = normalize(reference), normalize(hypothesis)
    if not ref:
        return 0.0

    # Quy hoạch động: d[i][j] = số phép sửa để biến ref[:i] thành hyp[:j].
    d = [[0] * (len(hyp) + 1) for _ in range(len(ref) + 1)]
    for i in range(len(ref) + 1):
        d[i][0] = i
    for j in range(len(hyp) + 1):
        d[0][j] = j

    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)

    return d[len(ref)][len(hyp)] / len(ref)


async def make_audio() -> list[tuple[Path, str]]:
    """Sinh file mp3 cho từng câu, bỏ qua câu đã có file."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    pairs = []
    for index, sentence in enumerate(SENTENCES, start=1):
        path = AUDIO_DIR / f"cau_{index:02d}.mp3"
        if not path.exists():
            communicate = edge_tts.Communicate(sentence, settings.tts_voice)
            await communicate.save(str(path))
        pairs.append((path, sentence))
    return pairs


def bench(model_name: str, pairs: list[tuple[Path, str]]) -> dict | None:
    from faster_whisper import WhisperModel

    try:
        load_started = time.time()
        model = WhisperModel(
            model_name,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
        load_seconds = round(time.time() - load_started, 1)
    except Exception as e:
        print(f"  {model_name:32} không nạp được: {str(e)[:70]}")
        return None

    total_wer = 0.0
    started = time.time()
    outputs = []

    for path, reference in pairs:
        segments, _ = model.transcribe(str(path), language="vi", beam_size=5)
        hypothesis = " ".join(s.text for s in segments).strip()
        total_wer += wer(reference, hypothesis)
        outputs.append((reference, hypothesis))

    elapsed = round(time.time() - started, 1)
    average = total_wer / len(pairs)

    print(
        f"  {model_name:32} WER {average:6.1%}   "
        f"{elapsed:5.1f}s nghe   {load_seconds:5.1f}s nạp"
    )
    return {
        "model": model_name,
        "wer": average,
        "seconds": elapsed,
        "load_seconds": load_seconds,
        "outputs": outputs,
    }


def main() -> None:
    pairs = asyncio.run(make_audio())
    print(f"Đã có {len(pairs)} câu mẫu trong {AUDIO_DIR}\n")

    results = [r for r in (bench(m, pairs) for m in MODELS) if r]
    if not results:
        return

    best = min(results, key=lambda r: (r["wer"], r["seconds"]))
    print(f"\nTốt nhất: {best['model']} — WER {best['wer']:.1%}")
    print("\nCâu nghe được từ model tốt nhất:")
    for reference, hypothesis in best["outputs"]:
        mark = "đúng" if normalize(reference) == normalize(hypothesis) else "lệch"
        print(f"  [{mark}] {hypothesis}")
        if mark == "lệch":
            print(f"         gốc: {reference}")


if __name__ == "__main__":
    main()

"""
So sánh các mô hình thị giác trên cùng một bộ ảnh.

Chạy từ gốc repo:
    .venv\\Scripts\\python.exe scripts\\eval_vlm.py data/eval/*.png

Với mỗi ảnh, script gọi lần lượt từng model trong MODELS, đo thời gian trả lời
và tự kiểm tra các quy tắc văn nói bắt buộc của đề tài (không markdown, không
cụm chỉ thị thị giác, không viết số bằng chữ số). Kết quả ghi ra
data/eval/results.json để đưa vào báo cáo.

Đây là căn cứ để trả lời câu hỏi "tại sao chọn model này" trước hội đồng.
"""

import glob
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Console Windows mặc định là cp1252, in tiếng Việt sẽ nổ.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.config import settings  # noqa: E402
from backend.services.vlm_service import VlmService  # noqa: E402

# Ứng viên. Bản :free không tốn tiền nhưng dùng chung hạn mức với người khác
# nên có lúc trả 429; bản trả phí rất rẻ và ổn định hơn.
MODELS = [
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "qwen/qwen3-vl-30b-a3b-instruct",
    "qwen/qwen3-vl-8b-instruct",
]

# Cụm chỉ thị thị giác — người nghe không thấy màn hình nên đọc lên là vô nghĩa.
VISUAL_DEIXIS = [
    "như bạn thấy", "như ta thấy", "hình bên trái", "hình bên phải",
    "ở phía trên", "ở phía dưới", "bên dưới đây", "trong hình trên",
    "nhìn vào hình", "như hình vẽ",
]

MARKDOWN = re.compile(r"(\*\*|^\s*[-*•]\s|^#{1,6}\s|```|\|\s*-{2,})", re.M)

# Chữ số thì không sao — máy đọc phát âm đúng. Ký hiệu mới là thứ đọc lên
# thành vô nghĩa, và từ tiếng Anh lọt vào thì máy đọc giọng Việt sẽ đọc sai.
SYMBOLS = re.compile(r"[%°²³×÷≥≤±]|m2")
ENGLISH = re.compile(
    r"(point|percent|the|and|is|are|this|image|chart|figure|table|shows?)",
    re.I,
)


def check_speech_rules(text: str) -> dict:
    """Đếm các vi phạm quy tắc văn nói. Càng ít càng tốt."""
    lowered = text.lower()
    return {
        "markdown": len(MARKDOWN.findall(text)),
        "visual_deixis": sum(1 for p in VISUAL_DEIXIS if p in lowered),
        "symbols": len(SYMBOLS.findall(text)),
        "english": len(ENGLISH.findall(text)),
    }


def run_one(model: str, image_bytes: bytes, mime: str) -> dict:
    """Gọi một model, trả về kết quả kèm thời gian và điểm kiểm tra."""
    service = VlmService()
    settings.vlm_model = model

    started = time.time()
    text = service.describe(image_bytes, mime)
    elapsed = round(time.time() - started, 1)

    if text is None:
        return {"model": model, "ok": False, "seconds": elapsed}

    return {
        "model": model,
        "ok": True,
        "seconds": elapsed,
        "chars": len(text),
        "violations": check_speech_rules(text),
        "text": text,
    }


def main(patterns: list[str]) -> None:
    paths: list[str] = []
    for pattern in patterns:
        paths.extend(sorted(glob.glob(pattern)))

    if not paths:
        print("Không tìm thấy ảnh nào khớp:", patterns)
        return

    if not settings.vlm_api_key:
        print("Thiếu OPENROUTER_API_KEY trong .env")
        return

    results = []
    for path in paths:
        mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
        data = Path(path).read_bytes()
        print(f"\n=== {os.path.basename(path)} ===")

        for model in MODELS:
            row = run_one(model, data, mime)
            row["image"] = os.path.basename(path)
            results.append(row)

            if not row["ok"]:
                print(f"  {model:42} lỗi sau {row['seconds']}s")
                continue

            v = row["violations"]
            print(
                f"  {model:42} {row['seconds']:>5}s  {row['chars']:>5} ký tự  "
                f"markdown={v['markdown']} chỉ-thị={v['visual_deixis']} "
                f"ký-hiệu={v['symbols']} tiếng-Anh={v['english']}"
            )

    out = Path("data/eval/results.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nĐã ghi {len(results)} kết quả vào {out}")


if __name__ == "__main__":
    main(sys.argv[1:] or ["data/eval/*.png"])

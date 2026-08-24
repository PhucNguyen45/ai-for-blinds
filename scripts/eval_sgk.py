"""
Đo mô hình trên bộ ảnh SGK thật của nhóm.

Chạy từ gốc repo:
    .venv\\Scripts\\python.exe scripts\\eval_sgk.py
    .venv\\Scripts\\python.exe scripts\\eval_sgk.py --model qwen/qwen3-vl-30b-a3b-instruct
    .venv\\Scripts\\python.exe scripts\\eval_sgk.py --che-do doc --show

Khác `eval_vqa.py` (dữ liệu mạng, ảnh sạch, câu hỏi ngắn), script này chấm trên
đúng loại trang học sinh sẽ chụp: bản đồ, lược đồ, bảng số liệu, biểu đồ, trục
thời gian. Điểm tính bằng tỉ lệ thông tin bắt buộc mà mô hình đọc ra được.

Đây là bảng số để trả lời hội đồng câu "mô hình đọc được sách giáo khoa đến đâu".
"""

import argparse
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.config import settings  # noqa: E402
from backend.services.vlm_service import VlmService  # noqa: E402

PAGES_DIR = Path("data/sgk_pages")
ANNOTATIONS = PAGES_DIR / "annotations.json"

# Cùng bộ tiêu chí văn nói với eval_vlm.py.
MARKDOWN = re.compile(r"(\*\*|^\s*[-*•]\s|^#{1,6}\s|```|\|\s*-{2,})", re.M)
SYMBOLS = re.compile(r"[%°²³×÷≥≤±]|m2\b")
ENGLISH = re.compile(
    r"\b(point|percent|the|and|is|are|this|image|chart|figure|table|map|shows?)\b",
    re.I,
)
VISUAL_DEIXIS = [
    "như bạn thấy", "như ta thấy", "hình bên trái", "hình bên phải",
    "ở phía trên", "ở phía dưới", "bên dưới đây", "trong hình trên",
    "nhìn vào hình", "như hình vẽ",
]


def normalize(text: str) -> str:
    """Chuẩn hoá để so khớp: thường hoá, bỏ dấu câu, gộp khoảng trắng.

    Giữ nguyên dấu tiếng Việt — đọc sai dấu là đọc sai tên riêng.
    Bỏ khoảng trắng trong số ('3 360' và '3360' tính là một).
    """
    text = unicodedata.normalize("NFC", text.lower())
    text = re.sub(r"(?<=\d)[  .](?=\d)", "", text)
    text = re.sub(r"[.,!?;:\"'()\[\]–—-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def found(needle: str, haystack: str) -> bool:
    return normalize(needle) in haystack


def check_speech_rules(text: str) -> dict:
    lowered = text.lower()
    return {
        "markdown": len(MARKDOWN.findall(text)),
        "chi_thi_thi_giac": sum(1 for p in VISUAL_DEIXIS if p in lowered),
        "ky_hieu": len(SYMBOLS.findall(text)),
        "tieng_anh": len(ENGLISH.findall(text)),
    }


def evaluate_page(service: VlmService, page: dict, mode: str, show: bool) -> dict:
    image_path = PAGES_DIR / "images" / page["file"]
    if not image_path.exists():
        print(f"  {page['id']:<18} thiếu ảnh: {image_path}")
        return {"id": page["id"], "ok": False, "ly_do": "thiếu ảnh"}

    data = image_path.read_bytes()
    mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"

    started = time.time()
    if mode == "doc":
        text = service.transcribe(data, mime)
    else:
        text = service.describe(data, mime, textbook_page=True)
    elapsed = round(time.time() - started, 1)

    if not text:
        print(f"  {page['id']:<18} lỗi gọi mô hình sau {elapsed}s")
        return {"id": page["id"], "ok": False, "ly_do": "lỗi gọi mô hình"}

    flat = normalize(text)
    must = page.get("phai_co", [])
    should = page.get("nen_co", [])
    hit_must = [m for m in must if found(m, flat)]
    miss_must = [m for m in must if m not in hit_must]
    hit_should = [m for m in should if found(m, flat)]

    coverage = len(hit_must) / len(must) if must else 1.0
    violations = check_speech_rules(text)

    print(
        f"  {page['id']:<18} {coverage:5.0%} bắt buộc  "
        f"({len(hit_should)}/{len(should)} nên có)  "
        f"{elapsed:5.1f}s  {len(text):>5} ký tự  [{page['kho']}]"
    )
    if miss_must:
        print(f"       thiếu: {', '.join(miss_must[:8])}")
    if show:
        print(f"       ---\n{text.strip()[:900]}\n       ---")

    return {
        "id": page["id"],
        "ok": True,
        "loai": page.get("loai", []),
        "kho": page.get("kho"),
        "coverage": coverage,
        "thieu": miss_must,
        "nen_co_dat": len(hit_should),
        "nen_co_tong": len(should),
        "seconds": elapsed,
        "chars": len(text),
        "vi_pham": violations,
        "text": text,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=None, help="ghi đè VLM_MODEL")
    parser.add_argument(
        "--che-do",
        choices=["mo_ta", "doc"],
        default="mo_ta",
        help="mo_ta = mô tả trang; doc = chép nguyên văn chữ",
    )
    parser.add_argument("--show", action="store_true", help="in cả câu trả lời")
    args = parser.parse_args()

    if not settings.vlm_api_key:
        print("Thiếu OPENROUTER_API_KEY trong .env")
        return
    if not ANNOTATIONS.exists():
        print(f"Không thấy {ANNOTATIONS}")
        return

    if args.model:
        settings.vlm_model = args.model

    spec = json.loads(ANNOTATIONS.read_text(encoding="utf-8"))
    pages = spec["trang"]
    service = VlmService()

    print(f"Model: {settings.vlm_model}   chế độ: {args.che_do}   "
          f"{len(pages)} trang\n")

    rows = [evaluate_page(service, p, args.che_do, args.show) for p in pages]
    done = [r for r in rows if r.get("ok")]

    if not done:
        print("\nChưa chấm được trang nào. Chép ảnh vào data/sgk_pages/images/ "
              "theo tên trong annotations.json.")
        return

    average = sum(r["coverage"] for r in done) / len(done)
    print(f"\nTrung bình: {average:.1%} trên {len(done)}/{len(pages)} trang")

    # Điểm theo mức khó — trang khó điểm thấp là bình thường, trang dễ điểm
    # thấp mới là dấu hiệu ảnh hoặc pipeline có vấn đề.
    for level in ("de", "trung_binh", "kho"):
        group = [r for r in done if r.get("kho") == level]
        if group:
            mean = sum(r["coverage"] for r in group) / len(group)
            print(f"  {level:<12} {mean:5.0%}  ({len(group)} trang)")

    total_violations: dict[str, int] = {}
    for r in done:
        for key, value in r["vi_pham"].items():
            total_violations[key] = total_violations.get(key, 0) + value
    print("  vi phạm văn nói:", total_violations)

    out = Path("data/eval/sgk_results.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "model": settings.vlm_model,
                "che_do": args.che_do,
                "trung_binh": average,
                "trang": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Chi tiết: {out}")


if __name__ == "__main__":
    main()

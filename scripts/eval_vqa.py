"""
Đo mô hình trên bộ ViInfographicVQA — ảnh infographic tiếng Việt có sẵn đáp án.

Chạy từ gốc repo:
    .venv\\Scripts\\python.exe scripts\\eval_vqa.py --n 20
    .venv\\Scripts\\python.exe scripts\\eval_vqa.py --n 20 --model qwen/qwen3-vl-30b-a3b-instruct

Khác với `eval_vlm.py` (chấm mô tả tự do, phải người đọc mới biết đúng sai),
script này chấm được tự động: mỗi ảnh có sẵn câu hỏi và đáp án do người Việt
gán nhãn. Nhờ vậy đo được nhiều ảnh mà không tốn công chấm tay.

Ảnh chỉ tải đúng số cần, không kéo cả 6.747 file của bộ dữ liệu.
"""

import argparse
import json
import random
import re
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.config import settings  # noqa: E402
from backend.services.vlm_service import VlmService  # noqa: E402

REPO = "TanSeng/ViInfographicVQA"
LOCAL = Path("data/datasets/infographic")


def normalize(text: str) -> str:
    """Bỏ dấu câu, gộp khoảng trắng, chuẩn hoá unicode để so khớp công bằng."""
    text = unicodedata.normalize("NFC", text.lower())
    text = re.sub(r"[.,!?;:\"'()\[\]°]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def score(expected: str, got: str) -> float:
    """
    Điểm khớp: tỉ lệ từ trong đáp án chuẩn xuất hiện trong câu trả lời.

    Không dùng so khớp chính xác vì mô hình hay trả lời thành câu đầy đủ —
    "Nam Bộ và Tây Nguyên" vẫn đúng so với đáp án "nam bộ, tây nguyên".
    """
    want = set(normalize(expected).split())
    have = set(normalize(got).split())
    if not want:
        return 0.0
    return len(want & have) / len(want)


def load_items(n: int, seed: int) -> list[dict]:
    from huggingface_hub import hf_hub_download

    path = hf_hub_download(
        REPO, "data/single_test.json", repo_type="dataset", local_dir=str(LOCAL)
    )
    items = json.loads(Path(path).read_text(encoding="utf-8"))
    random.Random(seed).shuffle(items)
    return items[:n]


def fetch_image(rel_path: str) -> Path:
    from huggingface_hub import hf_hub_download

    return Path(
        hf_hub_download(REPO, rel_path, repo_type="dataset", local_dir=str(LOCAL))
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=20, help="số câu cần đo")
    parser.add_argument("--seed", type=int, default=42, help="cố định để đo lại được")
    parser.add_argument("--model", default=None, help="ghi đè VLM_MODEL")
    parser.add_argument("--show", action="store_true", help="in từng câu trả lời")
    args = parser.parse_args()

    if not settings.vlm_api_key:
        print("Thiếu OPENROUTER_API_KEY trong .env")
        return

    if args.model:
        settings.vlm_model = args.model

    items = load_items(args.n, args.seed)
    service = VlmService()
    print(f"Model: {settings.vlm_model} — {len(items)} câu\n")

    total, exact, elapsed = 0.0, 0, 0.0
    rows = []

    for i, item in enumerate(items, start=1):
        image = fetch_image(item["image_path"])
        prompt = (
            "Trả lời câu hỏi sau dựa trên ảnh, bằng tiếng Việt, thật ngắn gọn, "
            "chỉ nêu đáp án, không giải thích.\n\n"
            f"Câu hỏi: {item['question']}"
        )

        started = time.time()
        answer = service._generate(prompt, image.read_bytes(), "image/jpeg") or ""
        elapsed += time.time() - started

        point = score(item["answer"], answer)
        total += point
        exact += 1 if point == 1.0 else 0
        rows.append((item, answer, point))

        print(f"  [{i:>3}/{len(items)}] {point:5.0%}  {item['image_type'][:28]}")
        if args.show:
            print(f"        hỏi:  {item['question'][:110]}")
            print(f"        đáp:  {item['answer']}")
            print(f"        model: {answer.strip()[:110]}")

    print(
        f"\nĐiểm trung bình: {total / len(items):.1%}   "
        f"Đúng hoàn toàn: {exact}/{len(items)}   "
        f"Trung bình {elapsed / len(items):.1f}s mỗi câu"
    )

    out = Path("data/eval/vqa_results.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "model": settings.vlm_model,
                "n": len(items),
                "seed": args.seed,
                "average": total / len(items),
                "exact": exact,
                "items": [
                    {
                        "question": it["question"],
                        "expected": it["answer"],
                        "got": ans,
                        "score": pt,
                        "image_type": it["image_type"],
                    }
                    for it, ans, pt in rows
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Chi tiết: {out}")


if __name__ == "__main__":
    main()

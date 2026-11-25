"""Số hóa một cuốn sách: thư mục ảnh trang → data/library/<book>/manifest.json.

Ví dụ (chạy từ thư mục gốc repo, đã cài backend/requirements.txt):
  python scripts/digitize_book.py --book lsdl4-ktt --title "Lịch sử và Địa lí 4 (Kết nối tri thức)" --images anh/lsdl4

- Tên file ảnh phải chứa số trang, ví dụ trang_012.jpg → trang 12.
- Trang đã có reviewed=true và ảnh không đổi sẽ được GIỮ NGUYÊN, không gọi lại mô hình.
- Chạy lại khi prompt lên phiên bản mới: thêm --force để làm lại cả trang chưa duyệt.
"""
import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app import prompts, storage  # noqa: E402
from app.config import settings  # noqa: E402
from app.speech import clean_for_speech  # noqa: E402
from app.vlm import get_vlm, parse_describe_output  # noqa: E402

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def page_number(path: Path) -> int:
    nums = re.findall(r"\d+", path.stem)
    if not nums:
        raise ValueError(f"Tên file không có số trang: {path.name}")
    return int(nums[-1])


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True, help="mã sách, chữ thường, ví dụ lsdl4-ktt")
    ap.add_argument("--title", required=True)
    ap.add_argument("--images", required=True, type=Path)
    ap.add_argument("--page-type", default="auto")
    ap.add_argument("--force", action="store_true", help="làm lại các trang chưa duyệt")
    args = ap.parse_args()

    out = settings.data_dir / "library" / args.book / "manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    old = {}
    if out.is_file():
        old = {p["page"]: p for p in json.loads(out.read_text(encoding="utf-8")).get("pages", [])}

    files = sorted((p for p in args.images.iterdir() if p.suffix.lower() in IMAGE_EXT), key=page_number)
    vlm = get_vlm()
    pages = []
    for path in files:
        num = page_number(path)
        raw = path.read_bytes()
        _, sha, jpeg = storage.prepare_image(raw)
        prev = old.get(num)
        if prev and prev.get("image_sha256") == sha and (prev.get("reviewed") or not args.force):
            pages.append(prev)
            print(f"trang {num}: giữ nguyên{' (đã duyệt)' if prev.get('reviewed') else ''}")
            continue
        text = await vlm.describe(prompts.describe_messages(jpeg, args.page_type), args.page_type)
        desc, ptype, _ = parse_describe_output(text, args.page_type)
        pages.append({
            "book": args.book, "page": num, "page_type": ptype,
            "description": clean_for_speech(desc), "image_sha256": sha,
            "model": settings.model_name, "prompt_version": settings.prompt_version,
            "reviewed": False,
        })
        print(f"trang {num}: xong ({ptype})")
        save(out, args, pages, old)  # ghi sau mỗi trang để lỡ dừng giữa chừng không mất kết quả

    total = save(out, args, pages, old)
    print(f"Đã ghi {total} trang vào {out}")


def save(out: Path, args, pages: list, old: dict) -> int:
    done = {p["page"] for p in pages}
    merged = sorted(pages + [p for n, p in old.items() if n not in done], key=lambda p: p["page"])
    out.write_text(json.dumps({"book": args.book, "title": args.title, "pages": merged}, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    return len(merged)


if __name__ == "__main__":
    asyncio.run(main())

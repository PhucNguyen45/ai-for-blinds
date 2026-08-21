"""
Nạp nội dung sách giáo khoa vào ChromaDB cho phần Hỏi đáp kiến thức.

Chạy từ gốc repo:
    .venv\\Scripts\\python.exe scripts\\ingest_sgk.py data/sgk/dia_ly_10.md

Định dạng file nguồn: Markdown hoặc text thuần, mỗi bài một file, đặt tên
theo mẫu ``<mon>_<lop>.md``. Trong file, mỗi mục bắt đầu bằng một dòng tiêu đề
kiểu ``## Bài 12. Cơ cấu dân số Việt Nam`` — script cắt theo các dòng đó.

Vì sao cắt theo tiêu đề mà không cắt theo số ký tự: học sinh hỏi theo bài,
theo mục. Cắt giữa câu làm đoạn truy xuất được mất ngữ cảnh và câu trả lời
đọc lên sẽ cụt.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.services.rag_service import rag_service  # noqa: E402

HEADING = re.compile(r"^#{1,3}\s+(.+)$", re.M)

# Tên file → môn học. Thêm môn mới thì bổ sung vào đây.
SUBJECTS = {
    "dia_ly": "Địa lý",
    "sinh_hoc": "Sinh học",
    "lich_su": "Lịch sử",
    "ngu_van": "Ngữ văn",
    "toan": "Toán",
    "vat_ly": "Vật lý",
    "hoa_hoc": "Hoá học",
}


def parse_filename(path: Path) -> tuple[str, int]:
    """Suy ra môn và lớp từ tên file, ví dụ 'dia_ly_10.md'."""
    stem = path.stem
    match = re.search(r"_(\d{1,2})$", stem)
    grade = int(match.group(1)) if match else 0
    key = stem[: match.start()] if match else stem
    return SUBJECTS.get(key, key), grade


def split_sections(text: str) -> list[tuple[str, str]]:
    """Cắt file thành các cặp (tiêu đề, nội dung) theo dòng tiêu đề."""
    matches = list(HEADING.finditer(text))
    if not matches:
        return [("Toàn bài", text.strip())]

    sections = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((m.group(1).strip(), body))
    return sections


def ingest(path: Path) -> int:
    subject, grade = parse_filename(path)
    text = path.read_text(encoding="utf-8")
    sections = split_sections(text)

    added = 0
    for index, (title, body) in enumerate(sections, start=1):
        chunk_id = f"{path.stem}_muc{index:03d}"
        # Giữ tiêu đề trong nội dung: nhờ vậy câu hỏi nhắc tên bài vẫn khớp.
        document = f"{title}\n{body}"
        ok = rag_service.add_textbook_chunk(
            chunk_id=chunk_id,
            text=document,
            metadata={
                "grade": grade,
                "subject": subject,
                "section": title,
                "source": f"SGK {subject} {grade}, {title}",
            },
        )
        if ok:
            added += 1
        else:
            print(f"  bỏ qua {chunk_id} (đã có hoặc lỗi ghi)")

    print(f"{path.name}: {added}/{len(sections)} mục — {subject} lớp {grade}")
    return added


def main(args: list[str]) -> None:
    paths = [Path(a) for a in args] or sorted(Path("data/sgk").glob("*.md"))
    paths = [p for p in paths if p.is_file()]

    if not paths:
        print("Không có file nào để nạp. Đặt file .md vào data/sgk/")
        return

    if not rag_service.available:
        print("ChromaDB chưa sẵn sàng. Cài chromadb và sentence-transformers.")
        return

    total = sum(ingest(p) for p in paths)
    print(f"\nĐã nạp {total} mục. Kho hiện có {rag_service.count_chunks()} đoạn.")


if __name__ == "__main__":
    main(sys.argv[1:])

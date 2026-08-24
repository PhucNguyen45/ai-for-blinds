"""
Tải các bộ dữ liệu ảnh tiếng Việt về máy để thử nghiệm và đánh giá.

Chạy từ gốc repo:
    .venv\\Scripts\\python.exe scripts\\download_datasets.py --list
    .venv\\Scripts\\python.exe scripts\\download_datasets.py infographic textvqa

Dữ liệu về thư mục data/datasets/<tên>. Các bộ này KHÔNG phải sách giáo khoa —
dùng để đo mô hình đọc chữ và hiểu biểu đồ tiếng Việt, không dùng làm nội dung
trả lời cho học sinh. Nội dung SGK nạp riêng bằng scripts/ingest_sgk.py.
"""

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT_DIR = Path("data/datasets")

# Xếp theo mức hữu ích cho đề tài: ảnh càng giống trang SGK càng đứng trước.
DATASETS = {
    "infographic": {
        "repo": "TanSeng/ViInfographicVQA",
        "size": "khoảng 6.700 file",
        "why": "Infographic tiếng Việt — gần biểu đồ và sơ đồ SGK nhất. "
               "Đây là bộ đáng ưu tiên đo trước.",
    },
    "textvqa": {
        "repo": "nhonhoccode/ViTextVQA",
        "size": "vài nghìn ảnh",
        "why": "Ảnh có chữ tiếng Việt trong khung cảnh thật. Đo khả năng đọc "
               "chữ có dấu ở góc nghiêng, thiếu sáng — đúng cảnh chụp SGK.",
    },
    "openvivqa": {
        "repo": "uitnlp/OpenViVQA-dataset",
        "size": "11.000 ảnh, 37.000 cặp hỏi đáp",
        "why": "Bộ hỏi đáp ảnh mở tiếng Việt lớn nhất, do UIT xây dựng. "
               "Câu hỏi do người Việt viết, không phải dịch máy.",
    },
    "vivqa_x": {
        "repo": "VLAI-AIVN/ViVQA-X",
        "size": "32.886 cặp hỏi đáp",
        "why": "Mỗi đáp án kèm câu giải thích bằng lời — hợp với việc học "
               "cách diễn đạt cho người nghe.",
    },
    "vivqa": {
        "repo": "SEACrowd/vivqa",
        "size": "10.328 ảnh, 15.000 cặp",
        "why": "Dịch máy từ COCO-QA sang tiếng Việt. Chất lượng câu chữ thấp "
               "hơn các bộ trên, chỉ dùng để so sánh.",
    },
    "handwriting": {
        "repo": "5CD-AI/Viet-Handwriting-OCR-v2",
        "size": "lớn",
        "why": "Chữ viết tay tiếng Việt. Cần khi muốn đọc vở ghi của học sinh, "
               "chưa cần cho giai đoạn SGK in.",
    },
}


def show_list() -> None:
    print("Các bộ dữ liệu có thể tải:\n")
    for key, info in DATASETS.items():
        print(f"  {key}")
        print(f"    kho:  {info['repo']}")
        print(f"    cỡ:   {info['size']}")
        print(f"    dùng: {info['why']}\n")
    print("Tải: python scripts/download_datasets.py infographic textvqa")


def download(keys: list[str]) -> None:
    from huggingface_hub import snapshot_download

    for key in keys:
        info = DATASETS.get(key)
        if info is None:
            print(f"Không có bộ tên '{key}'. Chạy --list để xem danh sách.")
            continue

        target = OUT_DIR / key
        print(f"\nTải {info['repo']} → {target}")
        try:
            snapshot_download(
                repo_id=info["repo"],
                repo_type="dataset",
                local_dir=str(target),
            )
            files = sum(1 for _ in target.rglob("*") if _.is_file())
            print(f"  xong: {files} file")
        except Exception as e:
            print(f"  lỗi: {str(e)[:160]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="*", help="tên bộ dữ liệu cần tải")
    parser.add_argument("--list", action="store_true", help="xem danh sách")
    args = parser.parse_args()

    if args.list or not args.names:
        show_list()
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    download(args.names)


if __name__ == "__main__":
    main()

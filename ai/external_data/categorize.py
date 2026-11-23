#!/usr/bin/env python3
"""Xếp dữ liệu ngoài vào ba mục thật trong data/external/: 1_hoc_tap, 2_cuoc_song, 3_hon_hop (bộ có cả nội dung học tập lẫn đời sống).

Việc xếp mục khai báo ở `hf.GROUPS` (nguồn duy nhất); `hf.dataset_dir()` tìm thư mục ở vị trí mới hay cũ nên mọi công cụ khác chạy được cả hai bố cục.
Mặc định chỉ IN danh sách sẽ chuyển (dry run); `--apply` mới chuyển thật bằng `mv` (đổi tên trong cùng ổ đĩa: tức thì, không sao chép, không xóa dữ liệu).

ViInfographicVQA là một bộ 9 chủ đề, không tách vật lý được nên nằm ở 3_hon_hop; chủ đề "Giáo dục - Khoa Học" được đánh dấu theo từng mẫu trong
_reports/phan_loai_infographic.csv. Căn cứ phân loại là nội dung đã xem (câu hỏi, ảnh mẫu, chủ đề), không chỉ tên bộ; lý do ghi trong bản mô tả ghi cục bộ ở
data/external/_reports/phan_loai.md (external_data/report.py ghép vào báo cáo công khai duy nhất ai/evaluation/reports/du_lieu_ngoai_20261118.md).

  uv run --with pyarrow --with numpy python external_data/categorize.py            # dry run
  uv run --with pyarrow --with numpy python external_data/categorize.py --apply    # chuyển thật
"""

import argparse
import csv
import shutil
import sys
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from external_data import hf  # noqa: E402

ROOT = hf.ROOT
EDU_TOPICS = {"Giáo dục - Khoa Học"}
TITLES = {"1_hoc_tap": "Mục HỌC TẬP (`1_hoc_tap/`)", "2_cuoc_song": "Mục CUỘC SỐNG (`2_cuoc_song/`)", "3_hon_hop": "Mục HỖN HỢP (`3_hon_hop/`)"}

# thư mục -> (tên hiển thị, lý do phân mục)
WHY = {
    "ViSGKCap": ("bbdontcry/ViSGKCap", "Trang sách giáo khoa Cánh Diều lớp 1-3 (Toán, Tiếng Việt, Tự nhiên và Xã hội, Đạo đức)."),
    "D-Truong__ViEduVQA": ("D-Truong/ViEduVQA", "Hỏi đáp trên tranh minh họa tiểu học; đã xác nhận có trang SGK Cánh Diều (trùng ViSGKCap). Nội dung tranh là cảnh đời thường vẽ trong SGK."),
    "anvo25__vmmu": ("anvo25/vmmu", "Ảnh trang đề thi trắc nghiệm có hình (Toán, Lý, Hóa, Sinh, Địa, IQ, thi bằng lái xe), tiếng Việt kèm tiếng Anh; 210 câu hỏi xuất hiện 5 lần dưới dạng ảnh khác nhau (nguyên trang, cắt khung, chỉ chữ), đã nối theo mã câu hỏi khi chia split."),
    "VLAI-AIVN__ViInfographicVQA": ("VLAI-AIVN/ViInfographicVQA", "Infographic tin tức, 9 chủ đề; chỉ 'Giáo dục - Khoa Học' liên quan học tập, 8 chủ đề còn lại (kinh tế, y tế, văn hóa, thiên tai, thể thao, thời tiết, quốc phòng, nhân vật) là đời sống. Không tách vật lý được."),
    "uitnlp__OpenViVQA-dataset": ("uitnlp/OpenViVQA-dataset", "Ảnh đời thường ở Việt Nam (phố, quán, nhà, ghe), hỏi đáp mở."),
    "Ouyangxuelili__vlsp2023-vqa-dataset": ("Ouyangxuelili/vlsp2023-vqa-dataset", "Bản sao một phần của OpenViVQA (cảnh đời thường); đã bị loại khỏi vai trò huấn luyện vì trùng."),
    "huyhuy123__ViOCRVQA": ("huyhuy123/ViOCRVQA", "Ảnh bìa sách (không phải SGK): hỏi tên sách, tác giả, nhà xuất bản, thể loại."),
    "5CD-AI__Viet-Table-Markdown": ("5CD-AI/Viet-Table-Markdown", "Ảnh bảng/biểu mẫu trong báo cáo, tin tức, hành chính; từ khóa học đường chỉ ~5% (mẫu 400)."),
}


def infographic_topics():
    """{id mẫu: chủ đề} cho mẫu dạng parquet (tệp#n) và ảnh jpg (qua images_paths)."""
    src = hf.dataset_dir("VLAI-AIVN__ViInfographicVQA") / "data"
    by_row, by_jpg, n = {}, {}, 0
    for f in sorted(src.glob("*.parquet")):
        for r in pq.read_table(f, columns=["images_paths", "image_type"]).to_pylist():
            n += 1
            by_row[f"{f.name}#{n}"] = r["image_type"]
            for p in r["images_paths"] or []:
                by_jpg.setdefault(p, r["image_type"])
    return by_row, by_jpg


def current_location(name):
    p = hf.dataset_dir(name)
    return p.relative_to(ROOT).parent.as_posix() if p.parent != ROOT else ""


def remove_old_symlinks():
    """Gỡ các liên kết mềm do lần làm trước để lại trong thư mục mục (chỉ liên kết, không động tới đích)."""
    removed = 0
    for group in hf.GROUPS:
        d = ROOT / group
        for entry in d.iterdir() if d.exists() else []:
            if entry.is_symlink():
                entry.unlink()
                removed += 1
    return removed


def move_all(apply):
    if apply:
        print("Đã gỡ", remove_old_symlinks(), "liên kết mềm cũ")
    moves = []
    for group, names in hf.GROUPS.items():
        for name in names:
            now = hf.dataset_dir(name)
            target = ROOT / group / name
            if now != target:
                moves.append((now, target))
    for src, dst in moves:
        print(("CHUYỂN  " if apply else "SẼ CHUYỂN  "), src.relative_to(ROOT), "->", dst.relative_to(ROOT))
        if apply:
            dst.parent.mkdir(exist_ok=True)
            if dst.exists():
                raise SystemExit(f"Đích đã tồn tại, dừng để không ghi đè: {dst}")
            shutil.move(str(src), str(dst))  # cùng ổ đĩa: đổi tên
    if not moves:
        print("Mọi bộ đã ở đúng mục.")
    return moves


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="chuyển thư mục thật (mặc định chỉ in kế hoạch)")
    args = ap.parse_args()
    move_all(args.apply)
    if not args.apply:
        print("\n(dry run: chưa chuyển gì; thêm --apply để chuyển)")

    overlay = list(csv.DictReader((ROOT / "_reports" / "splits_overlay.csv").open(encoding="utf-8")))
    dir_of = {v[0]: k for k, v in WHY.items()}
    by_dir = {name: [] for name in WHY}
    for r in overlay:
        if r["dataset"] in dir_of:
            by_dir[dir_of[r["dataset"]]].append(r)

    # thông tin riêng của ViInfographicVQA: chủ đề từng mẫu
    by_row, by_jpg = infographic_topics()
    with (ROOT / "_reports" / "phan_loai_infographic.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sample_id", "chu_de", "muc_noi_dung", "role"])
        part = {"hoc_tap": Counter(), "cuoc_song": Counter()}
        for r in by_dir["VLAI-AIVN__ViInfographicVQA"]:
            sid = r["sample_id"]
            topic = by_jpg.get(sid.split("/", 1)[1]) if sid.startswith("images/") else by_row.get(sid)
            muc = "hoc_tap" if topic in EDU_TOPICS else "cuoc_song"
            part[muc][r["role"]] += 1
            w.writerow([sid, topic or "", muc, r["role"]])
    topics = Counter(t for sid, t in by_row.items())

    def size_gb(name):
        return sum(p.stat().st_size for p in hf.dataset_dir(name).rglob("*") if p.is_file() and not p.name.endswith(".part")) / 1e9

    L = ["# Phân mục dữ liệu ngoài", "",
         "Các thư mục bộ dữ liệu nằm thật trong `data/external/1_hoc_tap/`, `2_cuoc_song/`, `3_hon_hop/` (khai báo ở `hf.GROUPS`). `_index/`, `_reports/`, `_sft/` ở cấp trên.",
         "Số mẫu là số dòng/ảnh trong lớp phủ train/val/test (`splits_overlay.csv`), gồm cả mẫu bị loại (`excluded`). Phân loại dựa trên nội dung đã xem, xem cột nội dung.", ""]
    for group, names in hf.GROUPS.items():
        L += [f"## {TITLES[group]}", "", "| Bộ dữ liệu | Thư mục | Số mẫu | train | val | test | bị loại | Dung lượng (GB) | Nội dung |", "|---|---|---|---|---|---|---|---|---|"]
        tot = Counter()
        for name in names:
            c = Counter(r["role"] for r in by_dir[name])
            tot.update(c)
            L.append(f"| {WHY[name][0]} | `{name}/` | {sum(c.values())} | {c['train']} | {c['val']} | {c['test']} | {c['excluded']} | {size_gb(name):.1f} | {WHY[name][1]} |")
        L += [f"| **Tổng** | | **{sum(tot.values())}** | {tot['train']} | {tot['val']} | {tot['test']} | {tot['excluded']} | | |", ""]
    L += ["### Bên trong ViInfographicVQA (chia theo chủ đề, ánh xạ từng mẫu ở `_reports/phan_loai_infographic.csv`)", "",
          "| Chủ đề | Thuộc | Số Q/A (parquet) |", "|---|---|---|"]
    L += [f"| {t} | {'học tập' if t in EDU_TOPICS else 'đời sống'} | {n} |" for t, n in topics.most_common()]
    L += ["", f"Tính cả ảnh jpg bổ sung: nội dung học tập {sum(part['hoc_tap'].values())} mẫu (train {part['hoc_tap']['train']}, test {part['hoc_tap']['test']}), "
          f"đời sống {sum(part['cuoc_song'].values())} mẫu (train {part['cuoc_song']['train']}, test {part['cuoc_song']['test']}, bị loại {part['cuoc_song']['excluded']}).", "",
          "## Lưu ý", "",
          "- Phân loại theo nội dung, không theo giấy phép. ViEduVQA CC BY-NC; các bộ khác phần lớn không khai báo giấy phép; ảnh SGK có bản quyền, chỉ dùng nghiên cứu nội bộ.",
          "- ViEduVQA xếp HỌC TẬP vì có trang SGK; hình bên trong là cảnh đời thường vẽ cho trẻ em. Tỉ lệ ảnh thuộc SGK trong bộ chưa đo hết.",
          "- Khoảng trống: chưa có SGK lớp 4-5, chưa có biểu đồ/bản đồ SGK thật; mục HỌC TẬP hiện chủ yếu là lớp 1-3.", ""]
    text = "\n".join(L)
    (ROOT / "_reports" / "phan_loai.md").write_text(text, encoding="utf-8")
    for old in (ROOT / "PHAN_LOAI.md", ROOT / "_reports" / "phan_loai_mau.csv"):  # tệp thừa của lần làm trước; đã có tệp thay thế
        if old.exists():
            old.unlink()
            print("Đã xóa tệp thừa:", old.relative_to(ROOT))
    print(text)


if __name__ == "__main__":
    main()

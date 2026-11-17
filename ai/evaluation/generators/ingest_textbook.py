#!/usr/bin/env python3
"""Nạp ảnh SGK/học liệu thật vào benchmark, theo phiếu nạp (intake.csv).

Quy trình:
  1. Đặt ảnh gốc vào data/benchmark/textbook/raw/ và điền data/benchmark/textbook/intake.csv
     (mẫu: ai/docs/textbook/intake_template.csv; hướng dẫn: ai/docs/textbook/HUONG_DAN.md): file, book, publisher, series, grade, subject, page,
     figure_label, category, difficulty, notes.
  2. `ingest_textbook.py`            kiểm tra phiếu, đăng ký ảnh (id ổn định theo sha256), sao chép vào
                                      textbook/images/, tạo mẫu ground truth rỗng textbook/truth/<id>_truth.json.
  3. NGƯỜI điền mệnh đề/câu hỏi trong file truth, rồi đặt ground_truth_status = "verified" và
     verified_by = tên người duyệt (khuyến nghị có người thứ hai rà soát).
  4. `ingest_textbook.py --promote`  đưa các mẫu đã verified vào manifest.json (source=textbook).

Nguyên tắc: ground truth KHÔNG được lấy từ đầu ra VLM chưa kiểm chứng; dev/test chia THEO SÁCH (không
tách các trang của cùng một sách); ảnh gốc mặc định không đưa lên git (xem .gitignore) vì bản quyền.

Chạy từ thư mục ai/:  uv run python evaluation/generators/ingest_textbook.py [--promote]
"""

import argparse
import csv
import hashlib
import json
import re
import shutil
from pathlib import Path

from PIL import Image

DEFAULT_ROOT = Path(__file__).resolve().parents[3] / "data" / "benchmark"
CATEGORIES = {"bar_chart", "line_chart", "pie_chart", "table", "flow_diagram", "cycle_diagram",
              "geometry", "map", "science_figure", "text", "other"}
GROUP = {"bar_chart": "chart", "line_chart": "chart", "pie_chart": "chart", "table": "table",
         "map": "map", "text": "text"}  # còn lại -> figure
DIFFICULTIES = {"easy", "medium", "hard"}
SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
REQUIRED = ["file", "book", "publisher", "grade", "subject", "category"]
LICENSE = "internal-research (GVHD cho phép dùng SGK; chưa có văn bản; không phát tán)"
GUIDE = ("Điền propositions (kind: value|relation|comparison|structure|inference; critical=true cho dữ kiện "
         "bắt buộc) và questions (type: lookup|comparison|computation|relation|refusal) CHỈ từ những gì nhìn "
         "thấy trong ảnh gốc. Không sao chép đầu ra của VLM. Sau khi đối chiếu xong: đặt "
         "ground_truth_status='verified' và verified_by='<tên người duyệt>'.")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_for_book(book: str) -> str:
    """Chia theo sách: mọi trang của một sách luôn cùng một split (xác định, không đổi theo thứ tự)."""
    h = int(hashlib.sha256(book.strip().lower().encode("utf-8")).hexdigest(), 16)
    return "dev" if h % 5 in (0, 2) else "test"


def read_intake(root: Path) -> list[dict]:
    path = root / "textbook" / "intake.csv"
    if not path.is_file():
        raise SystemExit(f"Chưa có phiếu nạp: {path}\nSao chép ai/docs/textbook/intake_template.csv thành data/benchmark/textbook/intake.csv rồi điền.")
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def validate_row(row: dict, raw_dir: Path) -> list[str]:
    errs = [f"thiếu '{k}'" for k in REQUIRED if not row.get(k)]
    if row.get("file"):
        p = (raw_dir / row["file"]).resolve()
        if not p.is_relative_to(raw_dir.resolve()):
            errs.append("đường dẫn file không an toàn")
        elif p.suffix.lower() not in SUFFIXES:
            errs.append(f"định dạng không hỗ trợ ({p.suffix})")
        elif not p.is_file():
            errs.append("không thấy file trong raw/")
        else:
            try:
                with Image.open(p) as im:
                    if min(im.size) < 300:
                        errs.append(f"ảnh quá nhỏ {im.size} (tối thiểu 300 px)")
            except Exception:
                errs.append("không mở được ảnh")
    if row.get("category") and row["category"] not in CATEGORIES:
        errs.append(f"category phải thuộc {sorted(CATEGORIES)}")
    if row.get("grade") and not (row["grade"].isdigit() and 1 <= int(row["grade"]) <= 12):
        errs.append("grade phải là số 1..12")
    if row.get("difficulty") and row["difficulty"] not in DIFFICULTIES:
        errs.append("difficulty phải là easy/medium/hard")
    return errs


def load_registry(root: Path) -> dict:
    p = root / "textbook" / "registry.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"items": {}}


def save_registry(root: Path, reg: dict) -> None:
    (root / "textbook").mkdir(parents=True, exist_ok=True)
    (root / "textbook" / "registry.json").write_text(
        json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def truth_template(item_id: str, row: dict) -> dict:
    return {
        "schema": "truth_v0.2", "id": item_id, "category": row["category"], "synthetic": False,
        "language": "vi",
        "title": f"{row['book']} — trang {row.get('page') or '?'} {row.get('figure_label') or ''}".strip(),
        "expected_status": "ok",
        "ground_truth_status": "template_unfilled", "verified_by": "",
        "annotation_guide": GUIDE,
        "source": {k: row.get(k, "") for k in ("book", "publisher", "series", "grade", "subject",
                                                 "page", "figure_label")},
        "data": {}, "propositions": [], "questions": [],
    }


def ingest(root: Path) -> dict:
    rows = read_intake(root)
    raw_dir, img_dir, truth_dir = (root / "textbook" / n for n in ("raw", "images", "truth"))
    img_dir.mkdir(parents=True, exist_ok=True)
    truth_dir.mkdir(parents=True, exist_ok=True)
    reg = load_registry(root)
    problems, added = [], 0
    for n, row in enumerate(rows, 2):  # dòng 1 là tiêu đề
        errs = validate_row(row, raw_dir)
        if errs:
            problems.append(f"dòng {n} ({row.get('file') or '?'}): " + "; ".join(errs))
            continue
        src = raw_dir / row["file"]
        sha = sha256_file(src)
        if sha in reg["items"]:
            continue
        item_id = f"tb_{len(reg['items']) + 1:03d}"
        dst = img_dir / f"{item_id}{src.suffix.lower()}"
        shutil.copyfile(src, dst)
        reg["items"][sha] = {"id": item_id, "image": f"textbook/images/{dst.name}", **{
            k: row.get(k, "") for k in ("book", "publisher", "series", "grade", "subject", "page",
                                        "figure_label", "category", "difficulty", "notes")}}
        tpath = truth_dir / f"{item_id}_truth.json"
        if not tpath.exists():
            tpath.write_text(json.dumps(truth_template(item_id, row), ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
        added += 1
    save_registry(root, reg)
    return {"rows": len(rows), "added": added, "problems": problems, "total": len(reg["items"])}


def promote(root: Path) -> dict:
    """Đưa các mẫu đã được người xác nhận vào manifest.json."""
    reg = load_registry(root)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    existing = {i["id"] for i in manifest["items"]}
    promoted, skipped = [], {}
    for sha, meta in reg["items"].items():
        item_id = meta["id"]
        if item_id in existing:
            continue
        tpath = root / "textbook" / "truth" / f"{item_id}_truth.json"
        truth = json.loads(tpath.read_text(encoding="utf-8")) if tpath.exists() else None
        why = None
        if truth is None:
            why = "chưa có file ground truth"
        elif truth.get("ground_truth_status") != "verified" or not truth.get("verified_by", "").strip():
            why = "chưa verified (cần ground_truth_status='verified' và verified_by)"
        elif not any(p.get("critical") for p in truth.get("propositions", [])):
            why = "chưa có mệnh đề critical"
        elif not truth.get("questions"):
            why = "chưa có câu hỏi"
        if why:
            skipped[item_id] = why
            continue
        img = root / meta["image"]
        category = meta["category"]
        manifest["items"].append({
            "id": item_id, "category": category, "group": GROUP.get(category, "figure"),
            "source": "textbook", "image": meta["image"],
            "ground_truth": f"textbook/truth/{item_id}_truth.json",
            "sha256": sha256_file(img), "ground_truth_sha256": sha256_file(tpath),
            "difficulty": meta.get("difficulty") or "medium",
            "split": split_for_book(meta["book"]), "expected_status": truth["expected_status"],
            "truth_schema": "truth_v0.2", "license": LICENSE, "restricted": True,
            "textbook": {k: meta.get(k, "") for k in ("book", "publisher", "series", "grade",
                                                     "subject", "page")},
        })
        promoted.append(item_id)
    if promoted:
        if not any(i.get("source") == "textbook" for i in manifest["items"][:-len(promoted)]):
            manifest["version"] = "0.3.0"  # lần đầu có ảnh thật: đổi thành phần benchmark
        else:
            a, b, c = (int(x) for x in manifest["version"].split("."))
            manifest["version"] = f"{a}.{b}.{c + 1}"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
    return {"promoted": promoted, "skipped": skipped, "version": manifest["version"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--promote", action="store_true", help="đưa mẫu đã verified vào manifest.json")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args()
    if args.promote:
        r = promote(args.root)
        print(f"Đã đưa vào manifest: {len(r['promoted'])} mẫu {r['promoted']} (phiên bản {r['version']})")
        for k, v in r["skipped"].items():
            print(f"  bỏ qua {k}: {v}")
        return
    r = ingest(args.root)
    print(f"Phiếu: {r['rows']} dòng | đăng ký mới: {r['added']} | tổng đã đăng ký: {r['total']}")
    for p in r["problems"]:
        print("  LỖI", p)
    if r["problems"]:
        raise SystemExit(1)
    print("Mẫu ground truth rỗng ở textbook/truth/ — hãy điền rồi chạy lại với --promote.")


if __name__ == "__main__":
    main()

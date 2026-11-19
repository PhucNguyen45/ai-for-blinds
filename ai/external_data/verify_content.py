#!/usr/bin/env python3
"""Kiểm lại các ứng viên trùng mức "nội dung" (pHash 5-10 bit) bằng một thước đo độc lập: tương quan chuẩn hóa (NCC) của ảnh xám 64x64.

Hiệu chỉnh trên cặp đã biết: trùng thật (mức `near`, đã xác nhận bằng mắt) và cặp ngẫu nhiên. Chỉ ĐỌC dữ liệu, không sửa.
  uv run --with pyarrow --with numpy python external_data/verify_content.py [--per-dataset 25]
Đầu ra: data/external/_reports/content_candidates_verified.csv và bảng tóm tắt in ra.
"""

import argparse
import csv
import io
import random
import sys
import zipfile
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from external_data import hf  # noqa: E402
from external_data.rows import read_row  # noqa: E402

ROOT = hf.ROOT
REPORT = ROOT / "_reports"
DIRS = {"D-Truong/ViEduVQA": "D-Truong__ViEduVQA", "uitnlp/OpenViVQA-dataset": "uitnlp__OpenViVQA-dataset",
        "Ouyangxuelili/vlsp2023-vqa-dataset": "Ouyangxuelili__vlsp2023-vqa-dataset", "VLAI-AIVN/ViInfographicVQA": "VLAI-AIVN__ViInfographicVQA",
        "huyhuy123/ViOCRVQA": "huyhuy123__ViOCRVQA", "5CD-AI/Viet-Table-Markdown": "5CD-AI__Viet-Table-Markdown"}


def fetch(dataset, sample):
    """Bytes ảnh của một mẫu theo id trong tệp trùng lặp (parquet#n, zip:tên, hoặc đường dẫn tệp)."""
    src = hf.dataset_dir(DIRS[dataset])
    if ".parquet#" in sample:
        return read_row(src, sample, ["image"])["image"]["bytes"]
    if ".zip:" in sample:
        zname, member = sample.split(".zip:", 1)
        zpath = next(p for p in src.rglob(zname + ".zip"))
        with zipfile.ZipFile(zpath) as z:
            return z.read(member)
    return (src / sample).read_bytes()


def visgkcap_bytes(page_id):
    for f in sorted((hf.dataset_dir("ViSGKCap") / "data").glob("*.parquet")):
        t = pq.read_table(f, columns=["id", "image"]).to_pylist()
        for r in t:
            if r["id"] == page_id:
                return r["image"]["bytes"]
    raise KeyError(page_id)


def thumb(data):
    g = np.asarray(Image.open(io.BytesIO(data)).convert("L").resize((64, 64), Image.LANCZOS), dtype=np.float64)
    g = g - g.mean()
    n = np.linalg.norm(g)
    return g / n if n > 1e-9 else g


def ncc(a, b):
    return float((thumb(a) * thumb(b)).sum())


VERIFIED, REVIEW = 0.6, 0.5  # NCC >= 0.6: trùng thật (cùng tranh, khác khung cắt); 0.5-0.6: cần xem tay; < 0.5: bác bỏ


def load_sha_map(dataset_dir):
    f = ROOT / "_index" / f"{dataset_dir}.jsonl"
    import json
    return {json.loads(line)["id"]: json.loads(line)["sha256"] for line in f.read_text(encoding="utf-8").splitlines()}


def verify_all():
    """Kiểm MỌI cặp ứng viên mức nội dung (theo ảnh duy nhất); ghi content_candidates_verified_all.csv và content_verified_edges.csv."""
    sha_vis = load_sha_map("visgkcap")  # chỉ mục tham chiếu có id là mã trang (SGK_CanhDieu_...)
    pages_cache = {}
    rows_out = []
    for ds, d in DIRS.items():
        sha_map = load_sha_map(d)
        f = REPORT / f"duplicates_{d}.csv"
        seen = {}
        for r in csv.DictReader(f.open(encoding="utf-8")):
            if r["level"] != "content" or not r["against"].split(":", 1)[0].endswith("ViSGKCap"):
                continue
            pid = r["against"].split(":", 1)[1]
            sha = sha_map.get(r["sample"])
            if sha is None or (sha, pid) in seen:
                continue
            seen[(sha, pid)] = r
        for (sha, pid), r in seen.items():
            if pid not in pages_cache:
                pages_cache[pid] = visgkcap_bytes(pid)
            try:
                score = ncc(fetch(ds, r["sample"]), pages_cache[pid])
            except Exception:  # noqa: BLE001
                score = float("nan")
            decision = "verified" if score >= VERIFIED else "review" if score >= REVIEW else "rejected"
            rows_out.append({"dataset": ds, "image_sha256": sha, "visgkcap_page": pid, "visgkcap_sha256": sha_vis[pid], "distance": r["distance"], "ncc": round(score, 3), "decision": decision, "sample": r["sample"]})
        print(ds, "cặp duy nhất:", len(seen), flush=True)
    with (REPORT / "content_candidates_verified_all.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_out[0]))
        w.writeheader()
        w.writerows(rows_out)
    with (REPORT / "content_verified_edges.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sha_a", "sha_b", "ncc"])
        for r in rows_out:
            if r["decision"] == "verified":
                w.writerow([r["image_sha256"], r["visgkcap_sha256"], r["ncc"]])
    for ds in DIRS:
        c = {k: sum(1 for r in rows_out if r["dataset"] == ds and r["decision"] == k) for k in ("verified", "review", "rejected")}
        print(f"{ds:40s} {c}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-dataset", type=int, default=25)
    ap.add_argument("--all", action="store_true", help="kiểm mọi cặp ứng viên và ghi danh sách cạnh đã xác nhận")
    a = ap.parse_args()
    if a.all:
        return verify_all()
    rnd = random.Random(7)
    pages_cache = {}

    def page(pid):
        if pid not in pages_cache:
            pages_cache[pid] = visgkcap_bytes(pid)
        return pages_cache[pid]

    out = []
    for ds, d in DIRS.items():
        f = REPORT / f"duplicates_{d}.csv"
        rows = [r for r in csv.DictReader(f.open(encoding="utf-8")) if r["against"].startswith("ViSGKCap:") or r["against"].startswith("bbdontcry/ViSGKCap:")]
        by_level = {lv: [r for r in rows if r["level"] == lv] for lv in ("near", "content")}
        for lv, rs in by_level.items():
            rs = sorted(rs, key=lambda r: r["sample"])
            rnd.shuffle(rs)
            seen = set()
            for r in rs:
                key = r["against"]
                if key in seen:  # một trang ViSGKCap chỉ kiểm một lần cho mỗi mức
                    continue
                seen.add(key)
                if len(seen) > a.per_dataset:
                    break
                pid = r["against"].split(":", 1)[1]
                try:
                    score = ncc(fetch(ds, r["sample"]), page(pid))
                except Exception as exc:  # noqa: BLE001
                    score = float("nan")
                    print("lỗi", ds, r["sample"], type(exc).__name__, flush=True)
                out.append({"dataset": ds, "level": lv, "distance": r["distance"], "sample": r["sample"], "visgkcap_page": pid, "ncc": round(score, 3)})
        print(ds, "xong", flush=True)
    # cặp ngẫu nhiên (âm tính) để hiệu chỉnh
    ids = [r["visgkcap_page"] for r in out]
    neg = []
    allp = sorted({r["visgkcap_page"] for r in out})
    for r in out[: min(30, len(out))]:
        other = rnd.choice([p for p in allp if p != r["visgkcap_page"]])
        try:
            neg.append(ncc(fetch(r["dataset"], r["sample"]), page(other)))
        except Exception:  # noqa: BLE001
            pass
    REPORT.mkdir(parents=True, exist_ok=True)
    with (REPORT / "content_candidates_verified.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print("\nNCC cặp ngẫu nhiên (âm tính): trung vị %.3f, tối đa %.3f (n=%d)" % (float(np.median(neg)), max(neg), len(neg)))
    for lv in ("near", "content"):
        for ds in DIRS:
            v = [r["ncc"] for r in out if r["dataset"] == ds and r["level"] == lv and r["ncc"] == r["ncc"]]
            if v:
                print(f"{ds:40s} {lv:8s} n={len(v):3d} NCC trung vị {np.median(v):.3f} | >=0.8: {sum(x >= 0.8 for x in v)} | <0.5: {sum(x < 0.5 for x in v)}")
    del ids


if __name__ == "__main__":
    main()

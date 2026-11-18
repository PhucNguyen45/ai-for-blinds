#!/usr/bin/env python3
"""Lập lớp phủ (overlay) phân vai train/val/test/excluded cho dữ liệu ngoài, theo cụm ảnh trùng/gần trùng. KHÔNG sửa dữ liệu gốc.

Đầu vào: data/external/_index/*.jsonl (chỉ mục băm, do `dedup.py index` tạo), content_verified_edges.csv (do `verify_content.py --all` tạo), benchmark của nhóm (data/benchmark/manifest.json) và tệp split gốc.
Đầu ra: data/external/_reports/splits_overlay.csv (cục bộ), splits_overlay_summary.json, ai/evaluation/reports/datasets/splits_overlay_summary.md.

  uv run --with pyarrow --with numpy python external_data/make_splits.py
"""

import csv
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from external_data import hf, imghash  # noqa: E402
from external_data.clusters import Item, assign_roles, build_clusters, check_invariants  # noqa: E402

ROOT = hf.ROOT
BENCH = ROOT.parent / "benchmark"
REPORT = ROOT / "_reports"
PUBLIC = Path(__file__).resolve().parents[1] / "evaluation" / "reports" / "datasets"
TRAIN_ONLY = {"D-Truong/ViEduVQA", "5CD-AI/Viet-Table-Markdown"}
SUBSET_OF = {"Ouyangxuelili/vlsp2023-vqa-dataset": "uitnlp/OpenViVQA-dataset"}
SPLIT_NAMES = {"train": "train", "training": "train", "validation": "val", "val": "val", "dev": "val", "test": "test"}


def dataset_name(stem):
    return stem.replace("__", "/")


def origins_viocrvqa():
    z = zipfile.ZipFile(ROOT / "huyhuy123__ViOCRVQA" / "data_ViOCRVQA.zip")
    out = {}
    for split in ("train", "dev", "test"):
        for im in json.loads(z.read(f"data/{split}.json"))["images"]:
            out[im["filename"]] = SPLIT_NAMES[split]
    return out


def origins_infographic_jpg():
    out = {}
    for f in sorted((ROOT / "VLAI-AIVN__ViInfographicVQA" / "data").glob("*.parquet")):
        split = "test" if f.name.startswith(("single_test", "multi_test")) else "train"
        for paths in pq.read_table(f, columns=["images_paths"]).column("images_paths").to_pylist():
            for p in paths or []:
                if out.get(p) != "test":  # ảnh tham chiếu bởi cả train và test: coi là test (thận trọng)
                    out[p] = split
    return out


def origin_of(ds, sample, vio, info_jpg):
    if ds == "bbdontcry/ViSGKCap":
        m = re.match(r"(train|validation|test)-", sample)
        return SPLIT_NAMES[m.group(1)] if m else None
    if ds == "uitnlp/OpenViVQA-dataset":
        m = re.search(r"(train|dev|test)-images", sample)
        return SPLIT_NAMES[m.group(1)] if m else None
    if ds == "huyhuy123/ViOCRVQA":
        return vio.get(sample.rsplit("/", 1)[-1])
    if ds == "VLAI-AIVN/ViInfographicVQA":
        if sample.startswith("images/"):
            return info_jpg.get(sample.split("/", 1)[1])
        return "test" if sample.startswith(("single_test", "multi_test")) else "train"
    if ds in TRAIN_ONLY:
        return "train"
    return None  # vlsp2023: tập con của OpenViVQA, không quyết định vai trò


def load_items():
    vio, info_jpg = origins_viocrvqa(), origins_infographic_jpg()
    items = []
    for f in sorted((ROOT / "_index").glob("*.jsonl")):
        if f.stem == "visgkcap":  # chỉ mục tham chiếu cũ của ViSGKCap, trùng với bbdontcry__ViSGKCap
            continue
        ds = dataset_name(f.stem)
        for line in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            bpp = r["bytes"] / (r["width"] * r["height"]) if r.get("width") and r.get("height") else None
            items.append(Item(ds, r["id"], r["sha256"], int(r["phash"], 16) if r.get("phash") else None, origin_of(ds, r["id"], vio, info_jpg), bpp))
    manifest = json.loads((BENCH / "manifest.json").read_text(encoding="utf-8"))
    for it in manifest["items"]:
        d = imghash.describe((BENCH / it["image"]).read_bytes())
        items.append(Item("benchmark_nhom", it["id"], d["sha256"], int(d["phash"], 16) if d.get("phash") else None, "bench",
                          d["bytes"] / (d["width"] * d["height"]) if d.get("width") else None))
    return items


def main():
    items = load_items()
    print("mẫu:", len(items), "| ảnh duy nhất:", len({i.sha for i in items}), flush=True)
    edges_file = REPORT / "content_verified_edges.csv"
    extra = [(r["sha_a"], r["sha_b"]) for r in csv.DictReader(edges_file.open(encoding="utf-8"))] if edges_file.exists() else []
    print("cạnh mức nội dung đã xác nhận bằng NCC:", len(extra), flush=True)
    cluster_of, suspicious = build_clusters(items, extra_edges=extra)
    roles = assign_roles(items, cluster_of, train_only=TRAIN_ONLY, subset_of=SUBSET_OF)
    problems = check_invariants(items, cluster_of, roles)
    REPORT.mkdir(parents=True, exist_ok=True)
    with (REPORT / "splits_overlay.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["dataset", "sample_id", "image_sha256", "cluster_id", "origin_split", "role", "reason"])
        for it, (role, reason) in zip(items, roles):
            if role != "benchmark":
                w.writerow([it.dataset, it.sample, it.sha, cluster_of[it.sha], it.origin or "", role, reason])
    table = Counter((it.dataset, role, reason, it.origin or "khong_ro") for it, (role, reason) in zip(items, roles) if role != "benchmark")
    per_cluster = Counter(cluster_of[it.sha] for it in items)
    multi = sum(1 for c, n in per_cluster.items() if n > 1)
    summary = {"samples": sum(1 for _, (r, _) in zip(items, roles) if r != "benchmark"), "benchmark_images": sum(1 for it in items if it.origin == "bench"),
               "invariant_violations": problems, "suspicious_clusters": suspicious, "clusters": len(per_cluster), "clusters_with_multiple_samples": multi,
               "table": [{"dataset": k[0], "role": k[1], "reason": k[2], "origin": k[3], "count": v} for k, v in sorted(table.items())]}
    hf.dump(REPORT / "splits_overlay_summary.json", summary)

    L = ["# Lớp phủ phân vai train/val/test cho dữ liệu ngoài (overlay)", "",
         "Giữ nguyên dữ liệu và split gốc; bảng ánh xạ nằm cục bộ ở `data/external/_reports/splits_overlay.csv`. Cụm ảnh = SHA-256 giống hệt, pHash cách <= 4 bit, hoặc cặp mức nội dung đã xác nhận bằng NCC >= 0.6 (cùng tranh, khác khung cắt); xuyên mọi bộ và benchmark của nhóm.", "",
         f"- Mẫu có vai trò: {summary['samples']}; ảnh benchmark của nhóm tham gia gom cụm: {summary['benchmark_images']}; số cụm: {summary['clusters']} (có nhiều mẫu: {multi}).",
         f"- Cụm quá lớn bị tách và gắn cờ đáng ngờ: {len(suspicious)}.",
         f"- **Kiểm tra bất biến (không cụm nào có cả train và val/test; cụm trùng benchmark không còn train/val/test):** {'ĐẠT' if not problems else f'VI PHẠM {len(problems)}'}.", "",
         "| Bộ dữ liệu | Split gốc | Vai trò | Lý do | Số mẫu |", "|---|---|---|---|---|"]
    L += [f"| {r['dataset']} | {r['origin']} | {r['role']} | {r['reason']} | {r['count']} |" for r in summary["table"]]
    L += ["", "Ghi chú: `group_split` = chia nội bộ theo cụm (5% val, 5% test) cho bộ chỉ có train, KHÔNG so sánh được với số liệu công bố; `leak_to_test/val` = ảnh trùng với tập đánh giá của bộ khác nên loại khỏi huấn luyện;",
          "`benchmark_overlap` = trùng với benchmark dev/test của nhóm; `duplicate_of_*` = bản sao của bộ khác. Mức `content` (pHash 5-10 bit) chỉ được nối khi NCC >= 0.6; các ca NCC 0.5-0.6 (`review`) chưa xử lý, cần xem tay.", ""]
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "splits_overlay_summary.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:12]))
    if problems:
        print("VI PHẠM:", problems[:5])
        sys.exit(1)


if __name__ == "__main__":
    main()

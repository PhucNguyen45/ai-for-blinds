#!/usr/bin/env python3
"""Kiểm tra trùng lặp giữa các bộ dữ liệu và ViSGKCap (không sửa, không xóa dữ liệu gốc).

Lệnh (chạy từ ai/, cần pyarrow và numpy: `uv run --with pyarrow --with numpy python external_data/dedup.py ...`):
  index-visgkcap                 lập chỉ mục băm của ViSGKCap (SHA-256, pHash, băm chú thích) -> data/external/_index/visgkcap.jsonl
  probe <repo> [--rows N]        lấy mẫu N dòng qua datasets-server (không tải cả bộ) và so với ViSGKCap
  index <thư mục> <tên>          lập chỉ mục băm của một bộ -> _index/<tên>.jsonl
  cross                          so sánh chéo (exact/near) mọi cặp bộ đã có chỉ mục
  full <thư mục> <tên>           so toàn bộ một bộ đã tải (parquet, thư mục ảnh hoặc zip) với ViSGKCap, và tìm trùng trong chính bộ đó

Mức trùng: exact (SHA-256 giống nhau), near (pHash cách nhau <= 4 bit), content (pHash 5-10 bit HOẶC cùng văn bản chú thích
trong ảnh khác nhau), annotation (cùng văn bản câu hỏi/chú thích sau chuẩn hóa nhưng ảnh khác).
"""

import argparse
import csv
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from external_data import hf, imghash  # noqa: E402

ROOT = hf.ROOT
INDEX = ROOT / "_index" / "visgkcap.jsonl"
REPORT = ROOT / "_reports"
NEAR, CONTENT = 4, 10
TEXT_COLS = ("caption_short", "caption_detail", "question", "Question", "Answer", "answer", "description", "markdown", "text")


def popcount64(arr: np.ndarray) -> np.ndarray:
    b = arr.view(np.uint8).reshape(-1, 8)
    return np.unpackbits(b, axis=1).sum(axis=1)


def load_index():
    rows = [json.loads(line) for line in INDEX.read_text(encoding="utf-8").splitlines()]
    ph = np.array([int(r["phash"], 16) if r.get("phash") else 0 for r in rows], dtype=np.uint64)
    return rows, ph, {r["sha256"]: r for r in rows}, {r["text_hashes"][k]: r for r in rows for k in r["text_hashes"]}


def cmd_index_visgkcap():
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    data = hf.dataset_dir("ViSGKCap") / "data"
    n = 0
    with INDEX.open("w", encoding="utf-8") as out:
        for f in sorted(data.glob("*.parquet")):
            pf = pq.ParquetFile(f)
            for batch in pf.iter_batches(batch_size=32):
                for r in batch.to_pylist():
                    d = imghash.describe(r["image"]["bytes"])
                    d.update(id=r["id"], file=f.name, title=r["metadata_title"],
                             text_hashes={k: imghash.text_hash(r[k]) for k in ("caption_short", "caption_detail") if r.get(k)})
                    out.write(json.dumps(d, ensure_ascii=False) + "\n")
                    n += 1
    print("Đã lập chỉ mục", n, "ảnh ViSGKCap ->", INDEX)


def compare(img_info, texts, ref_rows, ref_ph, ref_sha, ref_text):
    """Danh sách (mức, id ViSGKCap, khoảng cách/ghi chú) cho một mẫu."""
    hits = []
    if img_info["sha256"] in ref_sha:
        hits.append(("exact", ref_sha[img_info["sha256"]]["id"], 0))
    if img_info.get("phash"):
        d = popcount64(ref_ph ^ np.uint64(int(img_info["phash"], 16)))
        j = int(d.argmin())
        if d[j] <= NEAR and not hits:
            hits.append(("near", ref_rows[j]["id"], int(d[j])))
        elif d[j] <= CONTENT and not hits:
            hits.append(("content", ref_rows[j]["id"], int(d[j])))
    for t in texts:
        h = imghash.text_hash(t)
        if len(imghash.norm_text(t)) >= 25 and h in ref_text:
            hits.append(("annotation", ref_text[h]["id"], "text"))
            break
    return hits


def cmd_probe(repo, nrows):
    ref = load_index()
    rows_out = []
    seen = 0
    for offset in (0, 2000, 6000, 12000, 20000, 40000):
        if seen >= nrows:
            break
        st, js = hf.server_json("rows", dataset=repo, config="default", split="train", offset=offset, length=min(100, nrows - seen))
        if st != 200 or not js.get("rows"):
            continue
        for r in js["rows"]:
            row = r["row"]
            img = row.get("image") or {}
            if not img.get("src"):
                continue
            data = hf._get(img["src"]).content
            info = imghash.describe(data)
            texts = [str(row[c]) for c in TEXT_COLS if row.get(c)]
            hits = compare(info, texts, *ref)
            rows_out.append({"repo": repo, "offset": offset + r["row_idx"] - offset, "row_idx": r["row_idx"], "sha256": info["sha256"],
                             "phash": info["phash"], "hits": hits})
            seen += 1
    n_hit = sum(bool(r["hits"]) for r in rows_out)
    levels = {}
    for r in rows_out:
        for lv, _, _ in r["hits"]:
            levels[lv] = levels.get(lv, 0) + 1
    print(f"{repo}: mẫu {len(rows_out)}, có trùng {n_hit}, theo mức {levels}")
    hf.dump(REPORT / f"probe_{repo.replace('/', '__')}.json", {"repo": repo, "sampled": len(rows_out), "with_duplicate": n_hit,
                                                              "levels": levels, "rows": rows_out})


IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}


def iter_samples(src: Path):
    """(id mẫu, bytes ảnh, danh sách văn bản chú thích) cho parquet, thư mục ảnh hoặc tệp zip chứa ảnh."""
    n = 0
    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext == ".parquet":
            pf = pq.ParquetFile(f)
            names = pf.schema_arrow.names
            for batch in pf.iter_batches(batch_size=64):
                for r in batch.to_pylist():
                    n += 1
                    img = r.get("image")
                    if isinstance(img, dict) and img.get("bytes"):
                        yield f"{f.name}#{n}", img["bytes"], [str(r[c]) for c in TEXT_COLS if c in names and r.get(c)]
        elif ext == ".zip":
            with zipfile.ZipFile(f) as z:
                for info in z.infolist():
                    if Path(info.filename).suffix.lower() in IMG_EXT:
                        yield f"{f.name}:{info.filename}", z.read(info), []
        elif ext in IMG_EXT:
            yield str(f.relative_to(src)), f.read_bytes(), []


def cmd_full(src, name):
    ref_rows, ref_ph, ref_sha, ref_text = load_index()
    out_rows, sha_seen, ph_seen, n_img, n_bad = [], {}, {}, 0, 0
    for rid, data, texts in iter_samples(Path(src)):
        n_img += 1
        info = imghash.describe(data)
        n_bad += "error" in info
        for lv, vid, d in compare(info, texts, ref_rows, ref_ph, ref_sha, ref_text):
            out_rows.append({"dataset": name, "sample": rid, "level": lv, "against": f"ViSGKCap:{vid}", "distance": d})
        if info["sha256"] in sha_seen:
            out_rows.append({"dataset": name, "sample": rid, "level": "exact", "against": f"{name}:{sha_seen[info['sha256']]}", "distance": 0})
        else:
            sha_seen[info["sha256"]] = rid
        if info.get("phash"):
            first = ph_seen.setdefault(info["phash"], (rid, info["sha256"]))
            if first[0] != rid and first[1] != info["sha256"]:  # cùng pHash, khác SHA-256: ảnh gần giống trong cùng bộ
                out_rows.append({"dataset": name, "sample": rid, "level": "near", "against": f"{name}:{first[0]}", "distance": 0})
    REPORT.mkdir(parents=True, exist_ok=True)
    with (REPORT / f"duplicates_{name}.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["dataset", "sample", "level", "against", "distance"])
        w.writeheader()
        w.writerows(out_rows)
    levels = {}
    for r in out_rows:
        key = ("noi_bo_" if not r["against"].startswith("ViSGKCap") else "voi_visgkcap_") + r["level"]
        levels[key] = levels.get(key, 0) + 1
    hf.dump(REPORT / f"full_{name}.json", {"dataset": name, "images": n_img, "unreadable_images": n_bad, "unique_sha256": len(sha_seen),
                                           "unique_phash": len(ph_seen), "dup_rows": len(out_rows), "levels": levels})
    print(f"{name}: {n_img} ảnh, SHA-256 duy nhất {len(sha_seen)}, pHash duy nhất {len(ph_seen)}, bản ghi trùng {len(out_rows)} {levels}")


def cmd_index(src, name):
    """Ghi chỉ mục băm (SHA-256, pHash, băm văn bản) của một bộ để so sánh chéo giữa các bộ."""
    out = ROOT / "_index" / f"{name}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w", encoding="utf-8") as fh:
        for rid, data, texts in iter_samples(Path(src)):
            d = imghash.describe(data)
            d.update(id=rid, text_hashes=[imghash.text_hash(t) for t in texts if len(imghash.norm_text(t)) >= 25][:3])
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")
            n += 1
    print(f"{name}: đã lập chỉ mục {n} ảnh -> {out}")


def _load_unique(path):
    """{sha256: (id, phash int)} của một chỉ mục; mỗi ảnh duy nhất theo SHA-256 chỉ giữ mẫu đầu tiên."""
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        out.setdefault(r["sha256"], (r["id"], int(r["phash"], 16) if r.get("phash") else None))
    return out


def cmd_cross():
    """So sánh chéo từng cặp bộ đã lập chỉ mục: trùng chính xác (SHA-256) và gần trùng (pHash <= 4, tra bằng 5 khối 13 bit)."""
    idx = {p.stem: _load_unique(p) for p in sorted((ROOT / "_index").glob("*.jsonl")) if p.stem != "visgkcap"}  # "visgkcap" là chỉ mục tham chiếu (trùng với bbdontcry__ViSGKCap)
    names = sorted(idx)
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            A, B = idx[a], idx[b]
            exact = set(A) & set(B)
            for sha in exact:
                rows.append({"a": a, "b": b, "level": "exact", "a_sample": A[sha][0], "b_sample": B[sha][0], "distance": 0})
            # gần trùng: chỉ xét ảnh KHÔNG trùng chính xác; khối 13 bit (5 khối) theo nguyên lý ngăn kéo
            masks = [((1 << 13) - 1) << (13 * k) for k in range(5)]
            buckets = [{} for _ in masks]
            for sha, (rid, ph) in B.items():
                if ph is None or sha in exact:
                    continue
                for k, m in enumerate(masks):
                    buckets[k].setdefault(ph & m, []).append((rid, ph))
            seen = set()
            for sha, (rid, ph) in A.items():
                if ph is None or sha in exact:
                    continue
                for k, m in enumerate(masks):
                    for rid2, ph2 in buckets[k].get(ph & m, ()):
                        d = (ph ^ ph2).bit_count()
                        if d <= NEAR and (rid, rid2) not in seen:
                            seen.add((rid, rid2))
                            rows.append({"a": a, "b": b, "level": "near", "a_sample": rid, "b_sample": rid2, "distance": d})
            print(f"{a} x {b}: exact {len(exact)}, near {sum(1 for r in rows if r['a'] == a and r['b'] == b and r['level'] == 'near')}", flush=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    with (REPORT / "cross_dataset_duplicates.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["a", "b", "level", "a_sample", "b_sample", "distance"])
        w.writeheader()
        w.writerows(rows)
    print("Đã ghi cross_dataset_duplicates.csv:", len(rows), "dòng")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index-visgkcap")
    p = sub.add_parser("probe")
    p.add_argument("repo")
    p.add_argument("--rows", type=int, default=300)
    ix = sub.add_parser("index")
    ix.add_argument("src")
    ix.add_argument("name")
    sub.add_parser("cross")
    f = sub.add_parser("full")
    f.add_argument("src")
    f.add_argument("name")
    a = ap.parse_args()
    {"index-visgkcap": lambda: cmd_index_visgkcap(), "probe": lambda: cmd_probe(a.repo, a.rows),
     "full": lambda: cmd_full(a.src, a.name), "index": lambda: cmd_index(a.src, a.name), "cross": lambda: cmd_cross()}[a.cmd]()


if __name__ == "__main__":
    main()

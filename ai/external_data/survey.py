#!/usr/bin/env python3
"""Khảo sát các bộ dữ liệu Hugging Face (không tải dữ liệu): dataset card, cấu trúc, split, số mẫu, dung lượng, license, nguồn.

Ghi ra data/external/_reports/: survey_raw.json (phản hồi gốc rút gọn) và dataset_inventory.csv.
Chạy từ ai/:  uv run python external_data/survey.py
"""

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from external_data import hf  # noqa: E402

TARGETS = [
    ("A", "D-Truong/ViEduVQA"), ("A", "bbdontcry/ViSGKCap"), ("A", "5CD-AI/Viet-Doc-VQA-flash2"),
    ("A", "5CD-AI/Viet-Doc-VQA-II-flash2"), ("A", "5CD-AI/Viet-Doc-VQA-verIII"),
    ("B", "5CD-AI/Viet-OCR-VQA-flash2"), ("B", "huyhuy123/ViOCRVQA"), ("B", "VLAI-AIVN/ViInfographicVQA"),
    ("B", "Ouyangxuelili/vlsp2023-vqa-dataset"), ("B", "uitnlp/OpenViVQA-dataset"),
    ("B", "5CD-AI/Viet-Table-Markdown"), ("B", "5CD-AI/Viet-Handwriting-OCR-v2"),
]
SOURCE_HINT = re.compile(r"(sách giáo khoa|SGK|textbook|crawl|scrape|thu thập|nguồn|source|derived|synthetic|gemini|gpt|flash|"
                         r"annotat|license|giấy phép|cite|paper|arxiv)", re.I)


def summarize(group, repo, status, meta, card, info, rows_probe):
    cd = meta.get("cardData") or {}
    sib = meta.get("siblings") or []
    total = sum(s.get("size") or 0 for s in sib if s["rfilename"] not in (".gitattributes", "README.md"))
    ds = (info.get("dataset_info") or {}) if isinstance(info, dict) else {}
    # info có thể ở dạng {config: {...}}
    cfg = next(iter(ds.values()), {}) if ds and "features" not in ds else ds
    splits = {k: v.get("num_examples") for k, v in (cfg.get("splits") or {}).items()}
    feats = list((cfg.get("features") or {}).keys()) if isinstance(cfg.get("features"), dict) else [f["name"] for f in cfg.get("features", [])]
    if not feats:
        dsi = cd.get("dataset_info")
        if isinstance(dsi, dict):
            feats = [f["name"] for f in dsi.get("features", [])]
            splits = splits or {s["name"]: s.get("num_examples") for s in dsi.get("splits", [])}
    hints = sorted({m.group(0).lower() for m in SOURCE_HINT.finditer(card or "")})[:12]
    return {
        "group": group, "repo_id": repo, "status": status, "gated": meta.get("gated"), "private": meta.get("private"),
        "license_declared": cd.get("license"), "languages": cd.get("language"), "task_categories": cd.get("task_categories"),
        "downloads": meta.get("downloads"), "likes": meta.get("likes"), "last_modified": meta.get("lastModified"),
        "commit_sha": meta.get("sha"), "num_files": len(sib), "data_bytes": total, "splits": splits, "columns": feats,
        "has_image": "image" in feats or any("image" in f.lower() for f in feats), "card_chars": len(card or ""),
        "source_hints_in_card": hints, "arxiv": [t for t in meta.get("tags", []) if t.startswith("arxiv:")],
        "sample_rows": rows_probe,
    }


def main():
    out = hf.ROOT / "_reports"
    raw, rows = {}, []
    for group, repo in TARGETS:
        print("khảo sát", repo, flush=True)
        status, meta = hf.api_dataset(repo)
        if status != 200:
            rec = {"group": group, "repo_id": repo, "status": f"không truy cập được (HTTP {status})"}
            raw[repo] = rec
            rows.append(rec)
            continue
        card = hf.card_text(repo)
        st_info, info = hf.server_json("info", dataset=repo)
        probe = None
        if not meta.get("gated"):
            st_r, fr = hf.server_json("first-rows", dataset=repo, config="default", split="train")
            if st_r == 200 and fr.get("rows"):
                r0 = fr["rows"][0]["row"]
                probe = {k: (str(v)[:160] if k != "image" else "<image>") for k, v in r0.items() if not isinstance(v, (list, dict)) or k != "image"}
        rec = summarize(group, repo, "truy cập được" if not meta.get("gated") else f"bị khóa (gated={meta.get('gated')})", meta, card, info.get("dataset_info") and info or info, probe)
        rec["info_http"] = st_info
        raw[repo] = {**rec, "card_head": (card or "")[:1500]}
        rows.append(rec)
    hf.dump(out / "survey_raw.json", raw)

    # tìm thêm: ViTextVQA chính thức và các ứng viên khác (CHỈ liệt kê, không tải)
    extra = {}
    for term in ("ViTextVQA", "Vietnamese textbook", "Vietnamese VQA", "Viet-Doc", "ViSGK"):
        extra[term] = [{"id": d.get("id"), "downloads": d.get("downloads"), "likes": d.get("likes")} for d in hf.search(term, 12)]
    hf.dump(out / "survey_search.json", extra)

    cols = ["group", "repo_id", "status", "gated", "license_declared", "languages", "has_image", "splits", "columns", "data_bytes",
            "num_files", "downloads", "likes", "last_modified", "commit_sha", "arxiv", "source_hints_in_card", "card_chars"]
    with (out / "dataset_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (str(v) if isinstance(v, (dict, list)) else v) for k, v in r.items()})
    print("Đã ghi", out)


if __name__ == "__main__":
    main()

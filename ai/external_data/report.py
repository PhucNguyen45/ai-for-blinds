#!/usr/bin/env python3
"""Tổng hợp 5 báo cáo khảo sát/tải/trùng lặp từ dữ liệu trong data/external/_reports và các thư mục đã tải.

Đầu ra (data/external/_reports/): dataset_inventory.csv, dataset_manifest.json, duplicate_report.csv, download_report.md,
dataset_overview.md. Bản sao không chứa nội dung dữ liệu của hai tệp .md được đặt ở ai/evaluation/reports/datasets/.

Chạy từ ai/:  uv run python external_data/report.py
"""

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from external_data import hf  # noqa: E402

REPORT = hf.ROOT / "_reports"
PUBLIC = Path(__file__).resolve().parents[1] / "evaluation" / "reports" / "datasets"
GATED_NOTE = "bị khóa (gated=manual): cần đăng nhập Hugging Face và được chủ bộ dữ liệu duyệt; không có token nên không truy cập, không tải được"

# repo -> (quyết định, lý do, ghi chú nguồn gốc/quan hệ). Lý do dựa trên dataset card và số liệu khảo sát, không giả định.
DECISIONS = {
    "bbdontcry/ViSGKCap": ("da_crawl_truoc", "Đã tải trước đó; chỉ kiểm kê và kiểm tra trùng, không tải lại.",
                           "1229 trang SGK Cánh Diều lớp 1-3; chú thích do máy sinh (chưa kiểm chứng); không khai báo giấy phép."),
    "D-Truong/ViEduVQA": ("tai", "Công khai, CC BY-NC 4.0 (khai báo). Thuộc nhóm A theo yêu cầu.",
                          "Không có dataset card: nguồn ảnh và cách sinh Q/A chưa xác minh. ĐÃ XÁC NHẬN bằng mắt: có chứa trang SGK Cánh Diều (vd Tự nhiên và Xã hội 2, tr.53) trùng với ViSGKCap ở độ phân giải khác (799x1070 so với 558x783); nhiều Q/A cho mỗi ảnh (18.838 Q/A, 3.915 ảnh duy nhất)."),
    "5CD-AI/Viet-Doc-VQA-flash2": ("khong_tai_duoc", GATED_NOTE, "Cùng họ 5CD-AI/Viet-Doc-VQA; hậu tố flash2 gợi ý chú thích sinh bằng Gemini Flash 2 (suy ra từ tên, chưa xác minh vì thẻ bị khóa)."),
    "5CD-AI/Viet-Doc-VQA-II-flash2": ("khong_tai_duoc", GATED_NOTE, "Họ Viet-Doc-VQA-II; 64.516 mẫu: quan hệ với flash2 (51.672 mẫu) và verIII (205.346 mẫu) chưa xác minh được do bị khóa."),
    "5CD-AI/Viet-Doc-VQA-verIII": ("khong_tai_duoc", GATED_NOTE + ". Yêu cầu gốc: chỉ tải nếu xác minh nguồn và giá trị bổ sung, chưa xác minh được.",
                                   "205.346 mẫu, 28 GB: có thể là tập lớn hơn bao gồm các bản kia (chưa xác minh)."),
    "5CD-AI/Viet-OCR-VQA-flash2": ("khong_tai_duoc", GATED_NOTE, "Họ Viet-OCR-VQA; 136.654 mẫu."),
    "5CD-AI/Viet-Handwriting-OCR-v2": ("khong_tai_duoc", GATED_NOTE + " (khai báo CC BY-NC-ND 4.0: cấm tạo tác phẩm phái sinh, cần cân nhắc nếu dùng để huấn luyện).", "Tùy chọn theo yêu cầu."),
    "huyhuy123/ViOCRVQA": ("tai", "Công khai; một tệp zip ảnh 6,5 GB. Không khai báo giấy phép.", "Bài báo ViOCRVQA (ảnh bìa sách có chữ kèm Q/A). Nhãn Q/A nằm trong zip: data/train.json, dev.json, test.json (split gốc)."),
    "VLAI-AIVN/ViInfographicVQA": ("tai", "Công khai; infographic có biểu đồ, bản đồ: lấp khoảng trống của ViSGKCap. Tải parquet trước; sau khi kiểm tra thấy cột images_paths tham chiếu các ảnh jpg riêng của tập đa ảnh, nên tải thêm 6747 tệp images/*.jpg (5,0 GB).", "Không khai báo giấy phép; mục 'source' trong card."),
    "minhquan6203/ViTextVQA": ("khong_tai_duoc", "Kho chính thức tìm được (liên kết bài báo arXiv 2404.10652, CC BY-NC 3.0) nhưng gated=auto: cần đăng nhập và đồng ý điều khoản; không có token. Các bản sao khác (nhonhoccode, xuandin, 5CD-AI/Viet-ViTextVQA-gemini-VQA) chưa xác minh nên không đưa vào danh sách tải.", "ViTextVQA: VQA đọc chữ trong ảnh cảnh."),
    "Ouyangxuelili/vlsp2023-vqa-dataset": ("tai", "Công khai; bản phân phối lại của VLSP 2023; card nhắc phải tuân thủ điều khoản gốc của VLSP.", "Không phải kho chính thức của cuộc thi (do cá nhân duy trì). TỆP CHÚ THÍCH vlsp2023_train_data.json và vlsp2023_dev_data.json có SHA-256 GIỐNG HỆT hai tệp cùng tên trong uitnlp/OpenViVQA-dataset: đây là bản sao một phần (train+dev) của OpenViVQA, không phải dữ liệu mới."),
    "uitnlp/OpenViVQA-dataset": ("tai", "Công khai, giấy phép MIT khai báo.", "Kho của nhóm UIT-NLP; ảnh đời thường, VQA mở tiếng Việt."),
    "5CD-AI/Viet-Table-Markdown": ("tai", "Công khai; ảnh bảng kèm markdown: liên quan điểm yếu đọc bảng. Dung lượng lớn nên tải cuối.", "Không có card và không khai báo giấy phép: nguồn ảnh chưa xác minh."),
}
# Số Q/A (hoặc chú thích) đo từ tệp annotation/parquet đã tải ngày 18/11/2026, và split gốc do chủ bộ dữ liệu quy định
QA_COUNTS = {"bbdontcry/ViSGKCap": ("1229 chú thích (không có Q/A)", "train 981 / validation 123 / test 125"),
             "D-Truong/ViEduVQA": ("18838 Q/A", "chỉ train (không có test)"),
             "huyhuy123/ViOCRVQA": ("123780 Q/A (train 86592 / dev 18587 / test 18601)", "train / dev / test trong data/*.json của zip"),
             "VLAI-AIVN/ViInfographicVQA": ("20409 Q/A (đơn ảnh 13895, đa ảnh 6514)", "single_train / single_test / multi_train / multi_test"),
             "Ouyangxuelili/vlsp2023-vqa-dataset": ("34378 Q/A (train 30833 / dev 3545)", "train / dev (không có test)"),
             "uitnlp/OpenViVQA-dataset": ("48413 Q/A theo tệp vlsp2023_* (train 30833 / dev 3545 / test 14035)", "train 9129 / validation 1070 / test 1000 ảnh"),
             "5CD-AI/Viet-Table-Markdown": ("64902 dòng (ảnh bảng + markdown + hội thoại); số Q/A chưa đếm", "chỉ train (không có test)")}
EXTRA = [("Zenng2812/vqa-vietnamese-charts", "VQA biểu đồ tiếng Việt, 0,24 GB, không card, chưa xác minh nguồn"),
         ("LuminarAI/vietnamese-ms-hs-textbook-math-300K", "văn bản toán THCS/THPT, chưa xác minh"),
         ("5CD-AI/Viet-ViTextVQA-gemini-VQA", "bản chú thích lại ViTextVQA bằng Gemini, chưa xác minh"),
         ("nhonhoccode/ViTextVQA", "bản sao không chính thức, chưa xác minh"), ("xuandin/ViTextVQA", "bản sao không chính thức, chưa xác minh")]


def index_stats(repo):
    """Ảnh gốc / ảnh duy nhất / ảnh hỏng, tính từ chỉ mục băm mới nhất (_index/<tên>.jsonl, gồm cả ảnh tải bổ sung)."""
    f = hf.ROOT / "_index" / f"{repo.replace('/', '__')}.jsonl"
    if not f.exists():
        return None
    n, shas, bad = 0, set(), 0
    for line in f.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        n += 1
        shas.add(r["sha256"])
        bad += "error" in r
    return {"images": n, "unique_sha256": len(shas), "unreadable_images": bad}


def du(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file() and not p.name.endswith(".part")) if path.exists() else 0


def jload(p: Path, default=None):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def main():
    raw = jload(REPORT / "survey_raw.json", {})
    rows, manifest = [], {}
    for repo, (decision, reason, note) in DECISIONS.items():
        s = raw.get(repo, {})
        dest = hf.ROOT / repo.replace("/", "__") if repo != "bbdontcry/ViSGKCap" else hf.ROOT / "ViSGKCap"
        full = index_stats(repo)
        probe = jload(REPORT / f"probe_{repo.replace('/', '__')}.json")
        dl_manifest = jload(dest / "MANIFEST.json", {})
        splits = s.get("splits") or {}
        examples = sum(v for v in splits.values() if isinstance(v, int))
        row = {
            "group": s.get("group") or ("A" if repo in list(DECISIONS)[:5] else "B"), "repo_id": repo, "access": s.get("status", ""),
            "license_declared": s.get("license_declared") or "không khai báo", "splits": json.dumps(splits, ensure_ascii=False),
            "rows_declared": examples or "", "columns": ";".join(s.get("columns") or []), "size_gb_declared": round((s.get("data_bytes") or 0) / 1e9, 2),
            "files": s.get("num_files", ""), "commit": s.get("commit_sha", ""), "last_modified": (s.get("last_modified") or "")[:10],
            "decision": decision, "reason": reason, "provenance_note": note,
            "downloaded_gb": round(du(dest) / 1e9, 2), "images_found": (full or {}).get("images", ""), "unique_sha256": (full or {}).get("unique_sha256", ""),
            "probe_sampled": (probe or {}).get("sampled", ""), "probe_with_duplicate": (probe or {}).get("with_duplicate", ""),
            "qa_or_captions": QA_COUNTS.get(repo, ("", ""))[0], "original_splits": QA_COUNTS.get(repo, ("", ""))[1],
            "duplicate_images": ((full or {}).get("images") - (full or {}).get("unique_sha256")) if full else "",
        }
        rows.append(row)
        manifest[repo] = {**row, "splits": splits, "files_downloaded": dl_manifest}
    with (REPORT / "dataset_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    hf.dump(REPORT / "dataset_manifest.json", {"generated_by": "external_data/report.py", "extra_candidates_not_downloaded": EXTRA, "datasets": manifest})

    dup_rows = []
    have_full = set()
    for p in sorted(REPORT.glob("duplicates_*.csv")):
        for r in csv.DictReader(p.open(encoding="utf-8")):
            r["dataset"] = r["dataset"].replace("__", "/").replace("ViSGKCap(nội bộ)", "bbdontcry/ViSGKCap")
            r["against"] = r["against"].replace("ViSGKCap:", "bbdontcry/ViSGKCap:") if r["dataset"] == "bbdontcry/ViSGKCap" else r["against"]
            r["against"] = r["against"].replace("__", "/")
            r["source"] = "quét toàn bộ"
            have_full.add(r["dataset"])
            dup_rows.append(r)
    for p in sorted(REPORT.glob("probe_*.json")):
        d = jload(p)
        if d["repo"] in have_full or any(d["repo"] == repo for repo in [x["repo_id"] for x in rows] if (REPORT / f"duplicates_{repo.replace('/', '__')}.csv").exists()):
            continue
        for r in d["rows"]:
            for lv, vid, dist in r["hits"]:
                dup_rows.append({"dataset": d["repo"], "sample": f"probe:row{r['row_idx']}", "level": lv, "against": f"ViSGKCap:{vid}", "distance": dist, "source": "thăm dò mẫu"})
    cross = list(csv.DictReader((REPORT / "cross_dataset_duplicates.csv").open(encoding="utf-8"))) if (REPORT / "cross_dataset_duplicates.csv").exists() else []
    for r in cross:
        dup_rows.append({"dataset": r["a"].replace("__", "/"), "sample": r["a_sample"], "level": r["level"], "against": f"{r['b'].replace('__', '/')}:{r['b_sample']}",
                         "distance": r["distance"], "source": "so sánh chéo giữa các bộ"})
    with (REPORT / "duplicate_report.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["dataset", "sample", "level", "against", "distance", "source"])
        w.writeheader()
        w.writerows(dup_rows)

    # download_report.md
    L = ["# Báo cáo tải dữ liệu", "", "Mọi dữ liệu nằm ở `data/external/` (không có trong repo). Tải có resume, kiểm tra SHA-256 (tệp LFS), không ghi đè.", "",
         "| Bộ dữ liệu | Quyết định | Dung lượng khai báo (GB) | Đã có trên đĩa (GB) | Tệp OK / tổng | Lỗi |", "|---|---|---|---|---|---|"]
    for r in rows:
        dest = hf.ROOT / r["repo_id"].replace("/", "__") if r["repo_id"] != "bbdontcry/ViSGKCap" else hf.ROOT / "ViSGKCap"
        events = [json.loads(x) for x in (dest / "download_log.jsonl").read_text(encoding="utf-8").splitlines()] if (dest / "download_log.jsonl").exists() else []
        ok = sum(e["event"] == "downloaded" for e in events)
        err = [e for e in events if e["event"] == "error"]
        mf = jload(dest / "MANIFEST.json", {})
        tot = f"{len(mf)}/{r['files']}" if mf else ("5/5 (tải trước đó)" if r["repo_id"] == "bbdontcry/ViSGKCap" else "-")
        L.append(f"| {r['repo_id']} | {r['decision']} | {r['size_gb_declared']} | {r['downloaded_gb']} | {tot} (tải mới {ok}) | {len(err)} |")
    L += ["", "## Bộ không tải được và lý do", ""]
    for r in rows:
        if r["decision"] == "khong_tai_duoc":
            L.append(f"- **{r['repo_id']}**: {r['reason']}")
    L += ["", "## Ứng viên tìm thêm, chưa xác minh nên KHÔNG tải", ""] + [f"- `{rid}`: {why}" for rid, why in EXTRA]
    text = "\n".join(L) + "\n"
    (REPORT / "download_report.md").write_text(text, encoding="utf-8")

    # dataset_overview.md
    O = ["# Tổng quan các bộ dữ liệu tiếng Việt cho VLM (khảo sát 18/11/2026)", "",
         "Nguyên tắc: không giả định giấy phép của bộ dữ liệu áp dụng cho ảnh SGK gốc; chú thích do AI sinh không phải ground truth đã kiểm chứng; "
         "không trộn train/test giữa các nguồn; không xóa dữ liệu trùng khỏi bản gốc.", ""]
    O += ["## Thống kê theo bộ", "",
          "Ảnh gốc = số bản ghi ảnh; ảnh duy nhất = theo SHA-256; ảnh trùng = ảnh gốc trừ ảnh duy nhất (với bộ nhiều Q/A mỗi ảnh, phần lớn là CÙNG ẢNH hỏi nhiều lần, không phải rác).", "",
          "| Nhóm | Bộ dữ liệu | Truy cập | Giấy phép khai báo | Q/A hoặc chú thích | Split gốc | Ảnh gốc | Ảnh duy nhất | Ảnh trùng | Dung lượng thực (GB) | Quyết định |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        O.append(f"| {r['group']} | {r['repo_id']} | {r['access']} | {r['license_declared']} | {r['qa_or_captions']} | {r['original_splits']} | {r['images_found']} | {r['unique_sha256']} | {r['duplicate_images']} | {r['downloaded_gb']} | {r['decision']} |")
    O += ["", "## Mức trùng lặp (so với ViSGKCap và trong nội bộ từng bộ)", "",
          "- exact: SHA-256 ảnh giống hệt; near: pHash cách nhau tối đa 4 bit (resize, nén lại, quét lại); content: pHash 5 đến 10 bit hoặc cùng nội dung chữ; annotation: cùng văn bản chú thích/câu hỏi sau chuẩn hóa (>= 25 ký tự) nhưng ảnh khác.",
          "- Hạn chế: pHash không bền với ảnh bị cắt mạnh; không có OCR (chưa cài engine), nên trùng nội dung chữ chỉ dò qua văn bản chú thích đi kèm; bộ bị khóa không so sánh được.", ""]
    levels = {}
    for r in dup_rows:
        if r["source"] == "so sánh chéo giữa các bộ":
            continue
        tgt = "nội bộ" if r["against"].startswith(r["dataset"] + ":") else "ViSGKCap"
        key = (r["dataset"], r["level"], tgt)
        levels[key] = levels.get(key, 0) + 1
    O += ["### So với ViSGKCap và trong nội bộ từng bộ (quét toàn bộ)", "", "`content` (pHash 5-10 bit) là ỨNG VIÊN chưa xác nhận: ngưỡng lỏng, ảnh thưa thớt hay bị báo nhầm. Đã xác nhận bằng mắt: ViEduVQA `near` (cùng trang SGK, khác kích thước).", ""]
    O += ["| Bộ dữ liệu | Mức | So với | Số bản ghi |", "|---|---|---|---|"] + [f"| {k[0]} | {k[1]} | {k[2]} | {v} |" for k, v in sorted(levels.items())] if levels else ["Chưa có bản ghi trùng."]
    if cross:
        agg = {}
        for r in cross:
            k = (r["a"].replace("__", "/"), r["b"].replace("__", "/"), r["level"])
            agg[k] = agg.get(k, 0) + 1
        O += ["", "### So sánh chéo giữa các bộ (ảnh duy nhất; exact = SHA-256 giống hệt, near = pHash <= 4)", "", "| Bộ A | Bộ B | Mức | Số cặp |", "|---|---|---|---|"] + [f"| {a_} | {b_} | {lv} | {n} |" for (a_, b_, lv), n in sorted(agg.items())]
    # rò rỉ giữa split
    O += ["", "## Rủi ro rò rỉ giữa split (chỉ báo cáo, không xóa)", ""]
    pair = {}
    for r in dup_rows:
        if r["dataset"] == "uitnlp/OpenViVQA-dataset" and r["against"].startswith("uitnlp/OpenViVQA-dataset:") and r["level"] in ("exact", "near"):
            sp = lambda x: re.search(r"(train|dev|test)-images", x).group(1) if re.search(r"(train|dev|test)-images", x) else "?"  # noqa: E731
            a_, b_ = sp(r["sample"]), sp(r["against"])
            key = (r["level"], "cùng split" if a_ == b_ else " / ".join(sorted([a_, b_])))
            pair[key] = pair.get(key, 0) + 1
    if pair:
        O += ["- **OpenViVQA, ảnh trùng giữa các split gốc:** " + "; ".join(f"{lv} {k}: {n}" for (lv, k), n in sorted(pair.items())) + ". Nên loại các ảnh trùng chéo split khi dùng test gốc để đánh giá."]
    idx = {}
    vf = hf.ROOT / "_index" / "visgkcap.jsonl"
    if vf.exists():
        for line in vf.read_text(encoding="utf-8").splitlines():
            v = json.loads(line)
            idx[v["id"]] = v["file"].split("-")[0]
    for ds in sorted({r["dataset"] for r in dup_rows if r["against"].startswith(("bbdontcry/ViSGKCap:", "ViSGKCap:")) and r["dataset"] != "bbdontcry/ViSGKCap"}):
        for lv in ("near", "content"):
            pages = {r["against"].split(":", 1)[1] for r in dup_rows if r["dataset"] == ds and r["level"] == lv and r["against"].startswith(("bbdontcry/ViSGKCap:", "ViSGKCap:")) and r["source"] == "quét toàn bộ"}
            if pages:
                cnt = {}
                for pg in pages:
                    cnt[idx.get(pg, "?")] = cnt.get(idx.get(pg, "?"), 0) + 1
                O.append(f"- **{ds}** so với ViSGKCap, mức `{lv}`: {len(pages)} trang ViSGKCap, theo split của ViSGKCap {cnt}" + (" (đã xác nhận bằng mắt)" if (ds, lv) == ("D-Truong/ViEduVQA", "near") else " (ứng viên chưa xác nhận)" if lv == "content" else ""))
    O += ["", "## Kết luận và khuyến nghị", "",
          "- **Không trộn train/test giữa nguồn:** loại khỏi huấn luyện mọi ảnh trùng hoặc gần trùng với test/validation của ViSGKCap và với benchmark dev/test của nhóm; tạo danh sách loại trừ riêng, không sửa dữ liệu gốc.",
          "- **vlsp2023-vqa là tập con của OpenViVQA** (chú thích và ảnh trùng chính xác): chỉ giữ OpenViVQA để tránh đếm hai lần.",
          "- **ViEduVQA** có trang SGK Cánh Diều; bộ có nhiều Q/A cho mỗi ảnh (3.915 ảnh cho 18.838 Q/A) nên chia theo ảnh, không theo dòng.",
          "- **Khoảng trống chưa được phủ:** lớp 4-5 và biểu đồ/bản đồ SGK thật vẫn thiếu (ViSGKCap chỉ lớp 1-3; ViInfographicVQA là infographic báo chí, không phải SGK).",
          "- Chú thích do AI sinh chưa phải ground truth; giấy phép của bộ dữ liệu không mặc nhiên áp dụng cho ảnh SGK gốc; dữ liệu chỉ dùng nghiên cứu nội bộ.",
          "- Giới hạn: không OCR; pHash không bền với ảnh cắt mạnh; mức `content` chỉ là ứng viên; với ViInfographicVQA, quét so với ViSGKCap ở mức `content` chỉ gồm ảnh trong parquet (6.747 ảnh jpg bổ sung chỉ được so ở mức exact/near qua so sánh chéo).", ""]
    overlay = PUBLIC / "splits_overlay_summary.md"
    if overlay.exists():
        O += ["", "## Lớp phủ train/val/test (overlay)", ""] + overlay.read_text(encoding="utf-8").splitlines()[2:]
    O += ["", "## Ghi chú nguồn gốc theo từng bộ", ""] + [f"- **{r['repo_id']}**: {r['provenance_note']}" for r in rows]
    overview = "\n".join(O) + "\n"
    (REPORT / "dataset_overview.md").write_text(overview, encoding="utf-8")
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "dataset_overview.md").write_text(overview, encoding="utf-8")
    (PUBLIC / "download_report.md").write_text(text, encoding="utf-8")
    print("Đã tạo 5 báo cáo ở", REPORT, "và bản .md ở", PUBLIC)


if __name__ == "__main__":
    main()

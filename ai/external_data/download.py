#!/usr/bin/env python3
"""Tải một bộ dữ liệu Hugging Face công khai: có thể tiếp tục (resume), kiểm tra checksum, ghi nhật ký, không tải đè.

  uv run python external_data/download.py <repo_id> [--include "data/*.parquet" ...] [--dry-run]

Quy tắc an toàn:
- từ chối bộ bị khóa (gated) hoặc riêng tư; không dùng token;
- từ chối `bbdontcry/ViSGKCap` (đã có sẵn, không tải lại);
- tệp đã có và khớp kích thước + SHA-256 thì bỏ qua; tệp có sẵn nhưng KHÔNG khớp thì dừng, không ghi đè;
- tệp LFS được xác minh SHA-256 theo API Hub; tệp thường chỉ kiểm tra kích thước;
- --workers N tải song song nhiều tệp nhỏ (tối đa 16); tệp lớn nên để 1;
- giữ nguyên cấu trúc thư mục gốc; chỉ ghi vào data/external/<owner>__<name>/.
"""

import argparse
import fnmatch
import hashlib
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from external_data import hf  # noqa: E402

BLOCKED = {"bbdontcry/ViSGKCap"}
CHUNK = 1 << 20


def log(dest: Path, **event):
    event["time"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with (dest / "download_log.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(CHUNK):
            h.update(block)
    return h.hexdigest()


def fetch(client, repo, name, target: Path, size: int, delay: float):
    """Tải về target.part theo Range (tiếp tục nếu dở dang), trả về đường dẫn .part đã đủ dung lượng."""
    part = target.with_name(target.name + ".part")
    part.parent.mkdir(parents=True, exist_ok=True)
    have = part.stat().st_size if part.exists() else 0
    if have > size:
        part.unlink()
        have = 0
    url = f"{hf.HUB}/datasets/{repo}/resolve/main/{name}"
    while have < size:
        headers = {**hf.HEADERS, "Range": f"bytes={have}-"}
        with client.stream("GET", url, headers=headers) as r:
            if r.status_code not in (200, 206):
                raise RuntimeError(f"HTTP {r.status_code} khi tải {name}")
            if r.status_code == 200 and have:  # máy chủ bỏ qua Range: tải lại từ đầu
                have = 0
                part.write_bytes(b"")
            with part.open("ab") as f:
                for block in r.iter_bytes(CHUNK):
                    f.write(block)
                    have += len(block)
    time.sleep(delay)
    return part


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--include", nargs="*", default=["*"], help="mẫu glob theo đường dẫn tệp trong repo")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--delay", type=float, default=0.2, help="giây nghỉ giữa các tệp (mỗi luồng)")
    ap.add_argument("--workers", type=int, default=1, help="số luồng tải song song (dùng cho bộ có rất nhiều tệp nhỏ)")
    a = ap.parse_args()
    a.workers = min(max(a.workers, 1), 16)
    if a.repo in BLOCKED:
        raise SystemExit(f"{a.repo} đã được tải trước đó; không tải lại.")
    status, meta = hf.api_dataset(a.repo)
    if status != 200 or meta.get("gated") or meta.get("private"):
        raise SystemExit(f"Không tải: {a.repo} (HTTP {status}, gated={meta.get('gated')}, private={meta.get('private')}).")
    files = [s for s in meta["siblings"] if any(fnmatch.fnmatch(s["rfilename"], p) for p in a.include) and s["rfilename"] != ".gitattributes"]
    total = sum(s.get("size") or 0 for s in files)
    dest = hf.ROOT / a.repo.replace("/", "__")
    print(f"{a.repo}: {len(files)} tệp, {total / 1e9:.2f} GB -> {dest}", flush=True)
    if a.dry_run:
        return
    dest.mkdir(parents=True, exist_ok=True)
    manifest_path = dest / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    (dest / "SOURCE.txt").write_text(
        f"Nguồn: https://huggingface.co/datasets/{a.repo} (commit {meta.get('sha')})\n"
        f"Giấy phép khai báo trên trang: {(meta.get('cardData') or {}).get('license')}\n"
        "Giấy phép của bộ dữ liệu KHÔNG mặc nhiên áp dụng cho ảnh gốc (có thể là SGK/tài liệu có bản quyền). "
        "Chỉ dùng nghiên cứu nội bộ, không đưa lên repo, không phát hành lại. Chú thích do AI sinh chưa phải ground truth.\n"
        f"Ngày tải: {datetime.now(timezone.utc).date()}\n", encoding="utf-8")
    log(dest, event="start", repo=a.repo, files=len(files), bytes=total, commit=meta.get("sha"), workers=a.workers)
    lock = threading.Lock()
    counts = {"done": 0, "failed": 0}
    client = httpx.Client(headers=hf.HEADERS, timeout=60, follow_redirects=True,
                          limits=httpx.Limits(max_connections=max(a.workers, 1) * 2))

    def one(s):
        name, size = s["rfilename"], s.get("size") or 0
        expect = (s.get("lfs") or {}).get("sha256")
        target = dest / name
        if target.exists():
            if target.stat().st_size == size and (not expect or sha256_file(target) == expect):
                result = {"size": size, "sha256": expect, "status": "da_co"}
                with lock:
                    manifest[name] = result
                    counts["done"] += 1
                return
            log(dest, event="conflict", file=name)
            raise SystemExit(f"Tệp đã có nhưng không khớp, dừng để không ghi đè: {target}")
        try:
            part = fetch(client, a.repo, name, target, size, a.delay)
            digest = sha256_file(part) if expect else None
            if expect and digest != expect:
                part.unlink()
                raise RuntimeError(f"SHA-256 không khớp: {name}")
            part.rename(target)
            with lock:
                manifest[name] = {"size": size, "sha256": digest or expect, "status": "da_tai"}
                counts["done"] += 1
                log(dest, event="downloaded", file=name, bytes=size)
                if counts["done"] % 200 == 0:
                    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
                    print(f"  {counts['done']}/{len(files)}", flush=True)
        except Exception as exc:  # noqa: BLE001 - ghi lỗi từng tệp, tiếp tục các tệp khác
            with lock:
                counts["failed"] += 1
                log(dest, event="error", file=name, error=str(exc)[:200])
            print("  LỖI", name, exc, flush=True)

    with ThreadPoolExecutor(max_workers=max(a.workers, 1)) as pool:
        list(pool.map(one, files))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    log(dest, event="finish", done=counts["done"], failed=counts["failed"])
    print(f"Xong: {counts['done']}/{len(files)} tệp, lỗi {counts['failed']}", flush=True)


if __name__ == "__main__":
    main()

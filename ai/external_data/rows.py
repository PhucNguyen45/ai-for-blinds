"""Đọc một dòng của bộ dữ liệu theo id mẫu `<tệp>.parquet#n` (n là bộ đếm toàn cục 1-based qua các tệp parquet đã sắp xếp, như `dedup.iter_samples`)."""

from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq

_cache: dict[Path, list] = {}


def _files(src: Path):
    if src not in _cache:
        _cache[src] = [(f, pq.ParquetFile(f).metadata.num_rows) for f in sorted(src.rglob("*.parquet"))]
    return _cache[src]


def read_row(src: Path, sample: str, columns: list[str]) -> dict:
    n = int(sample.split("#")[1])
    for f, rows in _files(src):
        if n > rows:
            n -= rows
            continue
        pf = pq.ParquetFile(f)
        k = n - 1
        for g in range(pf.num_row_groups):
            size = pf.metadata.row_group(g).num_rows
            if k < size:
                return pf.read_row_group(g, columns=columns).slice(k, 1).to_pylist()[0]
            k -= size
    raise KeyError(sample)


def read_rows(src: Path, samples: list[str], columns: list[str]):
    """Sinh (id mẫu, dòng) cho nhiều mẫu cùng lúc, đọc mỗi row group đúng một lần (nhanh hơn nhiều so với gọi `read_row` lặp lại)."""
    wanted: dict[tuple[Path, int], dict[int, str]] = {}
    for sample in samples:
        n = int(sample.split("#")[1])
        for f, rows in _files(src):
            if n > rows:
                n -= rows
                continue
            pf = pq.ParquetFile(f)
            k = n - 1
            for g in range(pf.num_row_groups):
                size = pf.metadata.row_group(g).num_rows
                if k < size:
                    wanted.setdefault((f, g), {})[k] = sample
                    break
                k -= size
            break
    for (f, g), idx in sorted(wanted.items()):
        rows = pq.ParquetFile(f).read_row_group(g, columns=columns).to_pylist()
        for k, sample in sorted(idx.items()):
            yield sample, rows[k]

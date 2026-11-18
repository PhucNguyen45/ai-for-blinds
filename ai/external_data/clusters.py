"""Gom cụm ảnh trùng/gần trùng xuyên các bộ dữ liệu và gán vai trò train/val/test/excluded (lớp phủ, không sửa dữ liệu gốc).

Thuần Python (không numpy/pyarrow) để kiểm thử được. Quy tắc và lý do: xem `make_splits.py` và kế hoạch overlay.

Cụm = thành phần liên thông của đồ thị nối các ảnh có cùng SHA-256 hoặc pHash cách nhau <= `max_dist` bit. Chống gộp nhầm:
ảnh gần như trống (dung lượng thấp trên mỗi điểm ảnh) chỉ nối bằng SHA-256; thành phần quá lớn bị tách và gắn cờ "đáng ngờ".
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

ORIGINS = ("train", "val", "test", "bench")
MASKS = [((1 << 13) - 1) << (13 * k) for k in range(5)]  # 5 khối 13 bit: khoảng cách <= 4 thì ít nhất một khối trùng khít


@dataclass(frozen=True)
class Item:
    dataset: str
    sample: str
    sha: str
    phash: int | None
    origin: str | None            # train | val | test | bench (benchmark của nhóm) | None (không rõ)
    bytes_per_pixel: float | None = None


def iter_near_pairs(shas: dict[str, int], max_dist: int = 4, max_bucket: int = 30000):
    """Sinh (sha_a, sha_b, khoảng cách) cho các cặp có pHash cách <= max_dist; một cặp có thể xuất hiện nhiều lần (không giữ bộ nhớ).

    Khối pHash trùng khít có hơn `max_bucket` ảnh bị bỏ qua (suy biến: gần như mọi ảnh chung khối đó)."""
    buckets = [{} for _ in MASKS]
    for sha, ph in shas.items():
        for k, m in enumerate(MASKS):
            buckets[k].setdefault(ph & m, []).append(sha)
    for group in (g for b in buckets for g in b.values() if 1 < len(g) <= max_bucket):
        for i, a in enumerate(group):
            pa = shas[a]
            for b_ in group[i + 1:]:
                d = (pa ^ shas[b_]).bit_count()
                if d <= max_dist:
                    yield (a, b_, d) if a < b_ else (b_, a, d)


def near_pairs(shas: dict[str, int], max_dist: int = 4):
    """Danh sách cặp (sha_a, sha_b, khoảng cách) không lặp, a < b (dùng cho tập nhỏ và kiểm thử)."""
    return sorted(set(iter_near_pairs(shas, max_dist)))


class UnionFind:
    def __init__(self):
        self.parent: dict[str, str] = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            # gốc là SHA nhỏ nhất: cluster_id ổn định giữa các lần chạy
            self.parent[max(ra, rb)] = min(ra, rb)


def build_clusters(items: list[Item], max_dist: int = 4, max_cluster: int = 50, low_info: float = 0.03,
                   extra_edges: list[tuple[str, str]] | None = None):
    """Trả (cluster_of: {sha: cluster_id}, suspicious: {cluster_id: số ảnh} gồm các thành phần bị tách vì quá lớn).

    `extra_edges`: các cặp (sha_a, sha_b) đã được xác nhận trùng bằng cách khác (vd NCC của ảnh bị cắt khung), được nối thêm."""
    phash: dict[str, int] = {}
    blank: set[str] = set()
    for it in items:
        if it.phash is not None:
            phash[it.sha] = it.phash
        if it.bytes_per_pixel is not None and it.bytes_per_pixel < low_info:
            blank.add(it.sha)
    uf = UnionFind()
    for it in items:
        uf.find(it.sha)
    for a, b, _ in iter_near_pairs({s: p for s, p in phash.items() if s not in blank}, max_dist):
        uf.union(a, b)
    known = {it.sha for it in items}
    for a, b in extra_edges or ():
        if a in known and b in known:
            uf.union(a, b)
    members: dict[str, list[str]] = {}
    for sha in {it.sha for it in items}:
        members.setdefault(uf.find(sha), []).append(sha)
    cluster_of: dict[str, str] = {}
    suspicious: dict[str, int] = {}
    for root, shas in members.items():
        if len(shas) > max_cluster:  # quá lớn: nhiều khả năng gộp nhầm do pHash; giữ mỗi ảnh một cụm riêng
            suspicious[root] = len(shas)
            for s in shas:
                cluster_of[s] = s
        else:
            for s in shas:
                cluster_of[s] = root
    return cluster_of, suspicious


def _bucket(cluster_id: str, seed: str) -> float:
    return int(hashlib.sha256(f"{seed}:{cluster_id}".encode()).hexdigest()[:8], 16) / 2 ** 32


def assign_roles(items: list[Item], cluster_of: dict[str, str], *, train_only: set[str], subset_of: dict[str, str],
                 val_frac: float = 0.05, test_frac: float = 0.05, seed: str = "overlay-v1"):
    """Vai trò cho từng item: danh sách (role, reason) cùng thứ tự `items`. role: train | val | test | excluded."""
    by_cluster: dict[str, list[int]] = {}
    for i, it in enumerate(items):
        by_cluster.setdefault(cluster_of[it.sha], []).append(i)
    result: list[tuple[str, str] | None] = [None] * len(items)
    for cid, idxs in by_cluster.items():
        # các mẫu thuộc bộ "tập con" không tham gia quyết định vai trò của cụm
        voters = [items[i] for i in idxs if items[i].dataset not in subset_of and items[i].origin]
        origins = {it.origin for it in voters}
        only_train_only = bool(voters) and all(it.dataset in train_only for it in voters) and origins == {"train"}
        for i in idxs:
            it = items[i]
            if it.origin == "bench":
                result[i] = ("benchmark", "benchmark_nhom")
            elif it.dataset in subset_of:
                result[i] = ("excluded", f"duplicate_of_{subset_of[it.dataset]}")
            elif "bench" in origins:
                result[i] = ("excluded", "benchmark_overlap")
            elif "test" in origins:
                result[i] = ("test", "origin") if it.origin == "test" else ("excluded", "leak_to_test")
            elif "val" in origins:
                result[i] = ("val", "origin") if it.origin == "val" else ("excluded", "leak_to_val")
            elif only_train_only:
                u = _bucket(cid, seed)
                result[i] = (("val" if u < val_frac else "test" if u < val_frac + test_frac else "train"), "group_split")
            else:
                result[i] = ("train", "origin") if it.origin == "train" else ("excluded", "origin_khong_ro")
    return result


def check_invariants(items: list[Item], cluster_of: dict[str, str], roles) -> list[str]:
    """Danh sách vi phạm: cụm có cả train với val/test; mẫu ngoài ở cụm có benchmark không bị loại."""
    problems = []
    per: dict[str, set[str]] = {}
    for it, (role, _) in zip(items, roles):
        per.setdefault(cluster_of[it.sha], set()).add(role)
    for cid, rs in per.items():
        if "train" in rs and rs & {"val", "test"}:
            problems.append(f"cụm {cid[:12]} có cả train và {sorted(rs & {'val', 'test'})}")
        if "benchmark" in rs and rs & {"train", "val", "test"}:
            problems.append(f"cụm {cid[:12]} trùng benchmark nhưng còn vai trò {sorted(rs - {'benchmark', 'excluded'})}")
    return problems

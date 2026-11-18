import pytest

from external_data.clusters import Item, assign_roles, build_clusters, check_invariants, near_pairs

TRAIN_ONLY = {"A/trainonly", "B/trainonly"}
SUBSET = {"C/subset": "D/full"}


def item(ds, sample, sha, phash, origin, bpp=0.5):
    return Item(ds, sample, sha, phash, origin, bpp)


def run(items, **kw):
    cluster_of, sus = build_clusters(items, **kw)
    roles = assign_roles(items, cluster_of, train_only=TRAIN_ONLY, subset_of=SUBSET)
    return cluster_of, sus, roles


def test_near_pairs_finds_only_close_hashes():
    base = 0x0123456789ABCDEF
    d = {"s1": base, "s2": base ^ 0b1011, "s3": base ^ 0b11111111, "s4": base ^ (0xFFFF << 20)}
    found = {(a, b): dist for a, b, dist in near_pairs(d, 4)}
    assert found == {("s1", "s2"): 3}


def test_same_sha_and_near_hash_join_one_cluster():
    base = 0x0123456789ABCDEF
    items = [item("X/orig", "r1", "sha1", base, "train"), item("X/orig", "r2", "sha1", base, "train"),
             item("Y/other", "r3", "sha2", base ^ 0b11, "test")]
    cluster_of, _, roles = run(items)
    assert cluster_of["sha1"] == cluster_of["sha2"]
    assert [r[0] for r in roles] == ["excluded", "excluded", "test"]
    assert roles[0][1] == "leak_to_test"


def test_blank_images_are_not_joined_by_phash():
    items = [item("X/orig", "r1", "blank1", 0x1, "train", bpp=0.001), item("Y/other", "r2", "blank2", 0x1, "test", bpp=0.001)]
    cluster_of, _, roles = run(items)
    assert cluster_of["blank1"] != cluster_of["blank2"]
    assert [r[0] for r in roles] == ["train", "test"]


def test_giant_component_is_split_and_flagged():
    items = [item("X/orig", f"r{i}", f"s{i:03d}", 0x0123456789ABCDEF ^ (1 << (i % 3)), "train") for i in range(60)]
    cluster_of, sus, _ = run(items, max_cluster=10)
    assert sus and len(set(cluster_of.values())) == 60


def test_priority_benchmark_over_test_over_val_over_train():
    base = 0x00FF00FF00FF00FF
    bench = [item("bench", "b1", "sB", base, "bench")]
    ext = [item("X/orig", "t", "sB", base, "train"), item("X/orig", "t2", "sT", base ^ 1, "test"),
           item("X/orig", "v", "sV", base ^ 2, "val")]
    _, _, roles = run(bench + ext)
    assert roles[0][0] == "benchmark"
    assert all(r == ("excluded", "benchmark_overlap") for r in roles[1:])


def test_val_cluster_excludes_train_members_but_keeps_val():
    items = [item("X/orig", "a", "s1", 0xAAAA, "val"), item("Y/orig", "b", "s1", 0xAAAA, "train")]
    _, _, roles = run(items)
    assert roles == [("val", "origin"), ("excluded", "leak_to_val")]


def test_subset_dataset_is_excluded_and_does_not_decide_roles():
    items = [item("D/full", "a", "s1", 0xBBBB, "train"), item("C/subset", "b", "s1", 0xBBBB, "test")]
    _, _, roles = run(items)
    assert roles == [("train", "origin"), ("excluded", "duplicate_of_D/full")]


def test_train_only_datasets_get_deterministic_group_split_close_to_fractions():
    items = [item("A/trainonly", f"r{i}", f"s{i:04d}", (i * 0x9E3779B97F4A7C15) & ((1 << 64) - 1), "train") for i in range(4000)]
    c1, _, r1 = run(items)
    _, _, r2 = run(items)
    assert r1 == r2
    counts = {k: sum(1 for r in r1 if r[0] == k) for k in ("train", "val", "test")}
    assert abs(counts["val"] / 4000 - 0.05) < 0.02 and abs(counts["test"] / 4000 - 0.05) < 0.02
    assert all(r[1] == "group_split" for r in r1)


def test_cluster_shared_by_train_only_and_original_train_stays_train():
    items = [item("A/trainonly", "a", "s1", 0xCCCC, "train"), item("Z/original", "b", "s1", 0xCCCC, "train")]
    _, _, roles = run(items)
    assert roles == [("train", "origin"), ("train", "origin")]


@pytest.mark.parametrize("seed_shift", range(5))
def test_invariant_no_cluster_mixes_train_with_val_or_test(seed_shift):
    base = 0x1234567890ABCDEF
    items = []
    for i in range(200):
        origin = ("train", "val", "test")[(i + seed_shift) % 3]
        items.append(item(f"X/orig{i % 4}", f"r{i}", f"s{i // 2:03d}", base ^ ((i // 2) % 5), origin))
    cluster_of, _, roles = run(items)
    assert check_invariants(items, cluster_of, roles) == []


def test_extra_verified_edges_join_clusters_across_datasets():
    items = [item("X/orig", "a", "sA", 0x1111111111111111, "train"), item("Y/orig", "b", "sB", 0xEEEEEEEEEEEEEEEE, "test")]
    assert build_clusters(items)[0]["sA"] != build_clusters(items)[0]["sB"]
    cluster_of, _ = build_clusters(items, extra_edges=[("sA", "sB"), ("sA", "chua_co_trong_items")])
    assert cluster_of["sA"] == cluster_of["sB"]
    roles = assign_roles(items, cluster_of, train_only=TRAIN_ONLY, subset_of=SUBSET)
    assert roles == [("excluded", "leak_to_test"), ("test", "origin")]

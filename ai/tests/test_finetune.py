import hashlib
import json
import re
from pathlib import Path

import pytest

from finetune import export_sft, train_gen
from speech.vn_numbers import sn, su, words

CASES = {0: "không", 5: "năm", 10: "mười", 11: "mười một", 15: "mười lăm", 21: "hai mươi mốt",
         25: "hai mươi lăm", 99: "chín mươi chín", 100: "một trăm", 101: "một trăm linh một",
         105: "một trăm linh năm", 110: "một trăm mười", 205: "hai trăm linh năm", 1000: "một nghìn",
         1005: "một nghìn không trăm linh năm", 1010: "một nghìn không trăm mười",
         2021: "hai nghìn không trăm hai mươi mốt", 12345: "mười hai nghìn ba trăm bốn mươi lăm",
         1000000: "một triệu"}


@pytest.mark.parametrize("n,expected", CASES.items())
def test_number_words(n, expected):
    assert words(n) == expected


def test_decimals_and_units():
    assert sn(8.5) == "tám phẩy năm" and sn(7.0) == "bảy"
    assert su(29, "°C") == "hai mươi chín độ C" and su(35, "%") == "ba mươi lăm phần trăm"
    assert su(12, "cm²") == "mười hai xăng ti mét vuông"


@pytest.fixture(scope="module")
def small_set(tmp_path_factory):
    a = tmp_path_factory.mktemp("a")
    b = tmp_path_factory.mktemp("b")
    empty_bench = tmp_path_factory.mktemp("bench")
    train_gen.generate(60, 3, a, empty_bench, 0.15)
    train_gen.generate(60, 3, b, empty_bench, 0.15)
    return a, b, empty_bench


def digest(d):
    h = hashlib.sha256()
    for p in sorted(Path(d).glob("*")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def items_of(d):
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(d).glob("tr_*.json"))]


def test_generation_is_deterministic(small_set):
    a, b, _ = small_set
    assert digest(a) == digest(b)


def test_every_sample_is_consistent(small_set):
    a, _, _ = small_set
    its = items_of(a)
    assert len(its) == 60 and (Path(a) / "index.json").is_file()
    for it in its:
        t = it["target"]
        assert t["description"].strip() and t["page_type"] in {"text", "map", "chart", "table", "figure", "mixed"}
        assert t["unreadable"] == (it["degradation"] == "issue") == bool(it["capture_issue"])
        assert (Path(a) / it["image"]).read_bytes()[:2] == b"\xff\xd8"  # JPEG như đường ống backend
        assert it["truth"]["schema"] == "truth_v0.2" and it["truth"]["source"] == "synthetic-train"
        assert it["truth"]["propositions"] and it["truth"]["questions"]
        if t["unreadable"]:
            assert it["qa"] == [] and t["page_type"] == "mixed"
            assert it["truth"]["expected_status"] == "unreadable"
        else:
            assert it["qa"] and all(q["answer_spoken"].strip() for q in it["qa"])
            assert 25 <= it["description_words"] <= 200
        assert it["split"] in ("train", "val")


def test_values_are_spoken_exactly_for_charts(small_set):
    a, _, _ = small_set
    checked = 0
    for it in items_of(a):
        if it["target"]["unreadable"]:
            continue
        d, data, cat = it["target"]["description"], it["truth"]["data"], it["category"]
        if cat == "bar_chart":
            vals = data["values"].values()
        elif cat == "line_chart":
            vals = data["points"].values()
        elif cat == "pie_chart":
            vals = data["percentages"].values()
        else:
            continue
        assert all(sn(v) in d for v in vals), it["id"]
        checked += 1
    assert checked >= 5


def test_known_text_defects_do_not_regress(small_set):
    for it in items_of(small_set[0]):
        d = it["target"]["description"]
        assert "sơ đồ sơ đồ" not in d.lower()
        assert not re.search(r"phía (tây|đông) (Nam|Bắc)", d)
        assert "bắt đầu ở bắt đầu" not in d.lower()
        assert not re.search(r"\*|#|`", d)  # văn nói thuần, không ký hiệu định dạng


def test_no_overlap_with_benchmark_titles(small_set):
    for it in items_of(small_set[0]):
        assert it["truth"]["title"] not in train_gen.T.FORBIDDEN_TITLES


def test_check_detects_overlap_with_benchmark(small_set, tmp_path):
    a, _, _ = small_set
    it = items_of(a)[0]
    bench = tmp_path / "bench"
    (bench / "synthetic").mkdir(parents=True)
    # benchmark giả có cùng tiêu đề -> phải bị phát hiện
    (bench / "synthetic" / "x_truth.json").write_text(json.dumps(
        {"title": it["truth"]["title"], "category": it["truth"]["category"], "data": it["truth"]["data"]}))
    problems = train_gen.check(a, bench)
    assert any(it["id"] in p for p in problems)
    # ảnh trùng hash cũng bị phát hiện
    (bench / "synthetic" / "dup.png").write_bytes((Path(a) / it["image"]).read_bytes())
    assert any("ảnh trùng" in p for p in train_gen.check(a, bench))


def test_generator_avoids_titles_found_in_local_benchmark(tmp_path):
    bench = tmp_path / "bench"
    (bench / "synthetic").mkdir(parents=True)
    banned = train_gen.T.BAR_THEMES[0][0]
    (bench / "synthetic" / "x_truth.json").write_text(json.dumps({"title": banned, "category": "bar_chart", "data": {}}))
    out = tmp_path / "out"
    train_gen.generate(80, 5, out, bench, 0.0)
    assert all(i["truth"]["title"] != banned for i in items_of(out))


def test_procedural_content_scales_without_duplicates(tmp_path):
    out = tmp_path / "big"
    train_gen.generate(150, 11, out, tmp_path / "nobench", 0.0)
    sigs = [train_gen.signature(i["truth"]["category"], i["truth"]["title"], i["truth"]["data"]) for i in items_of(out)]
    assert len(set(sigs)) == len(sigs) == 150


def test_export_formats(small_set, tmp_path):
    a, _, _ = small_set
    out = tmp_path / "sft.jsonl"
    lines = export_sft.export(a, out, "api_v1", "train", include_ask=True)
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == len(lines) and {r["kind"] for r in rows} == {"describe", "ask"}
    assert all(r["split"] == "train" for r in rows)
    for r in rows:
        roles = [m["role"] for m in r["messages"]]
        if r["kind"] == "describe":
            assert roles == ["system", "user", "assistant"]
            obj = json.loads(r["messages"][2]["content"])
            assert set(obj) == {"page_type", "unreadable", "description"} and isinstance(obj["unreadable"], bool)
        else:
            assert roles == ["system", "user", "assistant", "user", "assistant"]
        assert r["messages"][1]["content"][0]["type"] == "image"
    plain = export_sft.export(a, tmp_path / "p.jsonl", "plain", "all")
    assert all(not l["messages"][2]["content"].startswith("{") for l in plain if l["kind"] == "describe")
    assert {l["split"] for l in plain} == {"train", "val"}


def test_val_split_is_disjoint_from_train(small_set):
    its = items_of(small_set[0])
    ids = {s: {i["id"] for i in its if i["split"] == s} for s in ("train", "val")}
    assert ids["train"] and ids["val"] and not (ids["train"] & ids["val"])

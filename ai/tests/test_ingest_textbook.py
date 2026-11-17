import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from evaluation.generators import ingest_textbook as it

HEADER = "file,book,publisher,series,grade,subject,page,figure_label,category,difficulty,notes\n"


@pytest.fixture
def root(tmp_path):
    (tmp_path / "textbook" / "raw").mkdir(parents=True)
    (tmp_path / "manifest.json").write_text(json.dumps({"version": "0.2.0", "items": []}))
    return tmp_path


def add(root, name, color="white", size=(400, 300)):
    Image.new("RGB", size, color).save(root / "textbook" / "raw" / name)


def sheet(root, *rows):
    (root / "textbook" / "intake.csv").write_text(HEADER + "\n".join(rows) + "\n", encoding="utf-8")


ROW = "{f},Địa lí 8,NXB Giáo dục Việt Nam,KNTT,8,Địa lí,{p},Hình 1,map,medium,"


def fill(root, item_id, verified=True, critical=True, questions=True):
    p = root / "textbook" / "truth" / f"{item_id}_truth.json"
    t = json.loads(p.read_text(encoding="utf-8"))
    t["ground_truth_status"] = "verified" if verified else "template_unfilled"
    t["verified_by"] = "Phúc" if verified else ""
    t["propositions"] = [{"id": "P1", "kind": "structure", "subject": "a", "predicate": "b",
                          "object": "c", "critical": critical}]
    t["questions"] = [{"id": "Q1", "type": "lookup", "question": "?", "answer": "x"}] if questions else []
    p.write_text(json.dumps(t, ensure_ascii=False), encoding="utf-8")


def test_ingest_registers_images_and_creates_unfilled_templates(root):
    add(root, "a.png"); add(root, "b.png", "black")
    sheet(root, ROW.format(f="a.png", p=1), ROW.format(f="b.png", p=2))
    r = it.ingest(root)
    assert r["added"] == 2 and not r["problems"]
    t = json.loads((root / "textbook/truth/tb_001_truth.json").read_text(encoding="utf-8"))
    assert t["ground_truth_status"] == "template_unfilled" and t["propositions"] == []
    assert (root / "textbook/images/tb_001.png").is_file()


def test_ingest_is_idempotent_and_ids_are_stable(root):
    add(root, "a.png")
    sheet(root, ROW.format(f="a.png", p=1))
    it.ingest(root)
    assert it.ingest(root)["added"] == 0
    add(root, "c.png", "red")
    sheet(root, ROW.format(f="a.png", p=1), ROW.format(f="c.png", p=3))
    it.ingest(root)
    reg = it.load_registry(root)["items"]
    assert sorted(v["id"] for v in reg.values()) == ["tb_001", "tb_002"]


@pytest.mark.parametrize("row,msg", [
    ("missing.png,Địa lí 8,NXB,KNTT,8,Địa lí,1,H1,map,medium,", "không thấy file"),
    ("a.png,Địa lí 8,NXB,KNTT,13,Địa lí,1,H1,map,medium,", "grade"),
    ("a.png,Địa lí 8,NXB,KNTT,8,Địa lí,1,H1,vẽ_tay,medium,", "category"),
    ("a.png,,NXB,KNTT,8,Địa lí,1,H1,map,medium,", "thiếu 'book'"),
    ("a.png,Địa lí 8,NXB,KNTT,8,Địa lí,1,H1,map,rất_khó,", "difficulty"),
    ("../x.png,Địa lí 8,NXB,KNTT,8,Địa lí,1,H1,map,medium,", "không an toàn"),
])
def test_invalid_rows_are_reported(root, row, msg):
    add(root, "a.png")
    sheet(root, row)
    r = it.ingest(root)
    assert r["added"] == 0 and any(msg in p for p in r["problems"])


def test_tiny_image_rejected(root):
    add(root, "t.png", size=(100, 100))
    sheet(root, ROW.format(f="t.png", p=1))
    assert any("quá nhỏ" in p for p in it.ingest(root)["problems"])


def test_promote_requires_human_verification(root):
    add(root, "a.png"); add(root, "b.png", "black"); add(root, "c.png", "red"); add(root, "d.png", "blue")
    sheet(root, *[ROW.format(f=f"{x}.png", p=i) for i, x in enumerate("abcd", 1)])
    it.ingest(root)
    fill(root, "tb_001")                                 # đủ điều kiện
    fill(root, "tb_002", verified=False)                 # chưa người duyệt
    fill(root, "tb_003", critical=False)                 # không có mệnh đề critical
    fill(root, "tb_004", questions=False)                # không có câu hỏi
    r = it.promote(root)
    assert r["promoted"] == ["tb_001"] and set(r["skipped"]) == {"tb_002", "tb_003", "tb_004"}
    item = json.loads((root / "manifest.json").read_text())["items"][0]
    assert item["source"] == "textbook" and item["restricted"] is True
    assert item["split"] in ("dev", "test") and r["version"] == "0.3.0"
    assert it.promote(root)["promoted"] == []            # không đưa trùng


def test_split_is_per_book_not_per_page(root):
    assert len({it.split_for_book("Địa lí 8") for _ in range(5)}) == 1
    assert it.split_for_book(" địa lí 8 ") == it.split_for_book("Địa lí 8")
    splits = {it.split_for_book(f"Sách {i}") for i in range(30)}
    assert splits == {"dev", "test"}


def test_template_never_contains_model_output_fields(root):
    add(root, "a.png")
    sheet(root, ROW.format(f="a.png", p=1))
    it.ingest(root)
    t = json.loads((root / "textbook/truth/tb_001_truth.json").read_text(encoding="utf-8"))
    assert t["propositions"] == [] and "verified_by" in t and t["source"]["book"] == "Địa lí 8"

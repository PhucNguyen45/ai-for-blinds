import httpx
import pytest
from PIL import Image, ImageDraw

from capture.quality import check_image, guidance_for
from pipeline import ask_page, describe_page

ENV = {"VLM_PROVIDER": "lmstudio", "LMSTUDIO_BASE_URL": "http://x/v1", "LMSTUDIO_MODEL": "m"}


def page(tmp_path, name="ok.png", kind="ok"):
    """Trang giả: nền trắng, nhiều chữ nhỏ và đường kẻ (sắc nét) hoặc biến thể lỗi."""
    im = Image.new("RGB", (900, 600), "white")
    d = ImageDraw.Draw(im)
    for y in range(40, 560, 24):
        d.text((40, y), "Thu Hai 40  Thu Ba 30  Thu Tu 25  Thu Nam 18", fill="black")
        d.line((30, y + 18, 860, y + 18), fill="black")
    if kind == "dark":
        im = im.point(lambda v: int(v * 0.05))
    elif kind == "blur":
        from PIL import ImageFilter
        im = im.filter(ImageFilter.GaussianBlur(5)).point(lambda v: min(255, int(v * 0.5 + 100)))
    elif kind == "white":  # cháy sáng: chữ còn nhưng gần như mất tương phản
        im = im.point(lambda v: 200 + v // 5)
    p = tmp_path / name
    im.save(p)
    return p


def vlm_calls(counter):
    def post(payload, api_key, base_url, timeout=None):
        counter.append(1)
        return httpx.Response(200, json={"choices": [{"message": {"content": "1. Chủ đề: bảng."}, "finish_reason": "stop"}]})
    return post


def test_gate_accepts_sharp_page_and_rejects_dark_blur_overexposed(tmp_path):
    assert check_image(page(tmp_path)).ok
    assert check_image(page(tmp_path, "d.png", "dark")).issues == ("dark",)
    assert check_image(page(tmp_path, "b.png", "blur")).issues == ("blur",)
    assert check_image(page(tmp_path, "w.png", "white")).issues == ("glare",)


def test_dark_background_but_readable_is_warned_not_blocked():
    """Nền tối, chữ sáng (bìa sách, màn hình số): độ sáng trung bình ~52 từng bị chặn là "tối"."""
    im = Image.new("RGB", (900, 600), (20, 30, 60))
    d = ImageDraw.Draw(im)
    for y in range(40, 560, 24):
        d.rectangle((40, y, 860, y + 2), fill="white")
    r = check_image(im)
    assert r.metrics["mean"] < 60 and r.metrics["p95"] >= 200
    assert r.ok and r.issues == () and r.warnings == ("dark",)


def test_very_dark_background_with_sharp_bright_detail_is_not_blocked():
    """Hình vũ trụ, ban đêm trong SGK: trung bình dưới 30 nhưng nét sáng rõ (vd "Vòng đời Mặt Trời": 24,9)."""
    im = Image.new("RGB", (900, 600), "black")
    d = ImageDraw.Draw(im)
    for y in range(40, 560, 40):
        d.rectangle((40, y, 860, y + 3), fill="white")
    r = check_image(im)
    assert r.metrics["mean"] < 30 and r.metrics["std"] >= 20 and r.metrics["p95"] >= 40
    assert r.ok and r.warnings == ("dark",)


def test_very_dark_flat_image_is_still_blocked():
    """Trung bình dưới 30 và gần như không tương phản thì vẫn là ảnh tối, dù vài mức sáng vượt phân vị 95."""
    im = Image.new("RGB", (900, 600), (12, 12, 12))
    ImageDraw.Draw(im).rectangle((0, 0, 899, 59), fill=(60, 60, 60))
    r = check_image(im)
    assert r.metrics["mean"] < 30 and r.metrics["std"] < 20 and r.metrics["p95"] >= 40
    assert r.issues == ("dark",)


@pytest.mark.parametrize("kind,issue", [("dark", "dark"), ("blur", "blur")])
def test_bad_capture_is_blocked_before_calling_vlm(tmp_path, kind, issue):
    calls = []
    r = describe_page(page(tmp_path, "x.png", kind), post=vlm_calls(calls), env=ENV, image_id="i1")
    assert r.status == "unreadable" and not calls and r.image_id == "i1" and r.meta is None
    assert r.summary_vi == guidance_for([issue]) and r.uncertainties == [f"capture_gate:{issue}"]


def test_good_capture_reaches_vlm_and_gate_can_be_disabled(tmp_path):
    calls = []
    assert describe_page(page(tmp_path), post=vlm_calls(calls), env=ENV).status == "ok" and calls
    calls.clear()
    assert describe_page(page(tmp_path, "d.png", "dark"), gate=False, post=vlm_calls(calls), env=ENV).status == "ok"
    assert calls


def test_corrupt_and_missing_images_are_errors_not_exceptions(tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    assert describe_page(bad, env=ENV).error.code == "invalid_image"
    assert describe_page(tmp_path / "none.png", env=ENV).error.code == "invalid_image"


def test_ask_page_delegates(tmp_path):
    def post(payload, api_key, base_url, timeout=None):
        return httpx.Response(200, json={"choices": [{"message": {"content": "Bốn mươi."}, "finish_reason": "stop"}]})
    assert ask_page(page(tmp_path), "Thứ Hai bao nhiêu?", post=post, env=ENV).answer_vi == "Bốn mươi."

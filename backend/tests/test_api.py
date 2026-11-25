"""Chạy: cd backend && pytest -q"""
import io
import json
import shutil
import sys
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import vlm as vlm_module  # noqa: E402
from app.config import REPO_ROOT, settings  # noqa: E402
from app.main import app  # noqa: E402
from app.speech import clean_for_speech  # noqa: E402
from app.vlm import OpenAICompatVLM, VLMTimeout, parse_describe_output  # noqa: E402

MARKDOWN_CHARS = set("*#`|")


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "mock_delay", 0)
    monkeypatch.setattr(settings, "vlm_mode", "mock")
    shutil.copytree(REPO_ROOT / "data" / "library", tmp_path / "library")
    vlm_module.reset_vlm()
    yield
    vlm_module.reset_vlm()


@pytest.fixture
def client():
    return TestClient(app)


def png_bytes(color=(200, 180, 120), size=(800, 1100)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def test_health(client):
    body = client.get("/health").json()
    assert body["data"]["status"] == "ok"
    assert body["data"]["vlm_mode"] == "mock"


def test_describe_then_cache(client):
    files = {"image": ("trang.png", png_bytes(), "image/png")}
    r = client.post("/v1/describe", files=files, data={"page_type": "map"})
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert len(d["image_id"]) == 16
    assert d["page_type"] == "map"
    assert d["cached"] is False
    assert d["prompt_version"] == "v1"
    assert not (MARKDOWN_CHARS & set(d["description"]))

    r2 = client.post("/v1/describe", files=files, data={"page_type": "map"})
    assert r2.json()["data"]["cached"] is True
    assert r2.json()["data"]["image_id"] == d["image_id"]

    log = (settings.data_dir / "logs" / "requests.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(log) == 2 and json.loads(log[0])["page_type"] == "map"


def test_describe_auto_defaults(client):
    r = client.post("/v1/describe", files={"image": ("a.png", png_bytes((1, 2, 3)), "image/png")})
    assert r.status_code == 200
    assert r.json()["data"]["page_type"] == "mixed"


def test_describe_invalid_image(client):
    r = client.post("/v1/describe", files={"image": ("a.jpg", b"not an image", "image/jpeg")})
    assert r.status_code == 400
    assert r.json() == {"data": None, "error": {"code": "INVALID_IMAGE", "message": r.json()["error"]["message"]}}


def test_describe_bad_page_type(client):
    r = client.post("/v1/describe", files={"image": ("a.png", png_bytes(), "image/png")}, data={"page_type": "xyz"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_ask_flow(client):
    d = client.post("/v1/describe", files={"image": ("a.png", png_bytes((9, 9, 9)), "image/png")}).json()["data"]
    r = client.post("/v1/ask", json={"image_id": d["image_id"], "question": "Sông chảy ra biển nào?",
                                     "history": [{"question": "Có mấy tỉnh?", "answer": "Có ba tỉnh."}]})
    assert r.status_code == 200, r.text
    assert "Sông chảy ra biển nào?" in r.json()["data"]["answer"]


def test_ask_unknown_image(client):
    r = client.post("/v1/ask", json={"image_id": "0123456789abcdef", "question": "?"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "IMAGE_NOT_FOUND"


def test_stt_mock(client):
    r = client.post("/v1/stt", files={"audio": ("cau.wav", b"RIFF....", "audio/wav")})
    assert r.status_code == 200
    assert r.json()["data"]["text"] == settings.mock_stt_text


def test_library(client):
    books = client.get("/v1/library").json()["data"]
    assert {"book": "demo", "title": "Sách mẫu để thử ứng dụng", "page_count": 3} in books
    pages = client.get("/v1/library/demo/pages").json()["data"]["pages"]
    assert [p["page"] for p in pages] == [1, 2, 3]
    assert client.get("/v1/library/khong-co/pages").json()["error"]["code"] == "BOOK_NOT_FOUND"
    assert client.get("/v1/library/..%2F..%2Fetc/pages").status_code == 404


def test_clean_for_speech():
    raw = "## Lược đồ\n**Phía Bắc** là `Lào Cai`.\n- Sông Hồng\n| Tỉnh | Diện tích |\n|---|---|\n| A | 10 |"
    out = clean_for_speech(raw)
    assert not (MARKDOWN_CHARS & set(out))
    assert "Phía Bắc là Lào Cai." in out and "Sông Hồng" in out and "A, 10" in out


def test_parse_describe_output_variants():
    fenced = '```json\n{"page_type": "chart", "unreadable": true, "description": "Biểu đồ cột."}\n```'
    assert parse_describe_output(fenced, "auto") == ("Biểu đồ cột.", "chart", True)
    assert parse_describe_output("Chỉ là văn bản.", "map") == ("Chỉ là văn bản.", "map", False)
    assert parse_describe_output('{"page_type":"lạ","description":"X"}', "auto")[1] == "mixed"


@pytest.mark.anyio
async def test_openai_compat_retry_then_success(monkeypatch):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        assert request.url.path.endswith("/chat/completions")
        if calls["n"] == 1:
            return httpx.Response(503, text="busy")
        return httpx.Response(200, json={"choices": [{"message": {"content": "xin chào"}}]})

    monkeypatch.setattr(vlm_module.asyncio, "sleep", _no_sleep)
    v = OpenAICompatVLM(transport=httpx.MockTransport(handler))
    assert await v.ask([{"role": "user", "content": "hi"}]) == "xin chào"
    assert calls["n"] == 2


@pytest.mark.anyio
async def test_openai_compat_timeout():
    def handler(request):
        raise httpx.ReadTimeout("chậm", request=request)

    v = OpenAICompatVLM(transport=httpx.MockTransport(handler))
    with pytest.raises(VLMTimeout):
        await v.ask([{"role": "user", "content": "hi"}])


async def _no_sleep(_):
    return None


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_describe_through_openai_layer(client, monkeypatch):
    """Luồng thật: prompt v1 được nạp, ảnh gửi dạng base64, JSON trong ``` được bóc, markdown bị lọc."""
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen["model"] = body["model"]
        seen["system"] = body["messages"][0]["content"]
        seen["image"] = body["messages"][1]["content"][0]["image_url"]["url"][:22]
        content = '```json\n{"page_type": "map", "unreadable": true, "description": "**Lược đồ** vùng Tây Nguyên.\\n- Phía trên là hướng Bắc."}\n```'
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    monkeypatch.setattr(settings, "vlm_mode", "openai")
    vlm_module.reset_vlm(OpenAICompatVLM(transport=httpx.MockTransport(handler)))
    r = client.post("/v1/describe", files={"image": ("a.png", png_bytes((5, 6, 7)), "image/png")})
    d = r.json()["data"]
    assert r.status_code == 200, r.text
    assert d["page_type"] == "map" and d["unreadable"] is True
    assert d["description"] == "Lược đồ vùng Tây Nguyên.\nPhía trên là hướng Bắc."
    assert d["model"] == settings.vlm_model
    assert seen["image"] == "data:image/jpeg;base64"
    assert "Tự xác định loại trang".lower() in seen["system"].lower()

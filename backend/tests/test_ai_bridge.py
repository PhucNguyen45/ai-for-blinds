"""Kiểm thử VLM_MODE=ai: backend (API v1) gọi module AI của Phúc (ai/pipeline.py, hợp đồng v0.1).

Phần lớn giả lập describe_page/ask_page nhưng dùng ĐÚNG mô hình dữ liệu của hợp đồng (ai/contract/models.py),
nên đổi hợp đồng là test báo. Test cuối chạy pipeline thật với ảnh đen: cổng chất lượng chặn trước khi gọi
mạng, nên không cần khóa API.
Chạy: cd backend && pytest -q
"""
import io
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import ai_bridge  # noqa: E402
from app.config import REPO_ROOT, settings  # noqa: E402
from app.main import app  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "ai"))
from contract.models import AnswerResult, DescriptionResult, ErrorInfo, Meta  # noqa: E402


def _meta(prompt_id="b0g_v1") -> Meta:
    return Meta(model="lmstudio/gemma-4-e4b", provider="lmstudio", prompt_id=prompt_id, prompt_sha256="0" * 64,
                temperature=0.2, max_tokens=600, created_at_utc=datetime.now(timezone.utc))


class FakePipeline:
    def __init__(self):
        self.describe_result = DescriptionResult(
            image_type="bar_chart", status="ok", summary_vi="Biểu đồ cột số sách.",
            interpretation_vi="Biểu đồ cột có năm cột. Cột thứ Hai cao nhất, bốn mươi quyển.",
            question_answering_ready=True, meta=_meta())
        self.answer_result = AnswerResult(status="ok", answer_vi="Cột thứ Hai cao nhất.", meta=_meta("ask_calc_v1"))
        self.describe_calls, self.ask_calls = [], []

    def describe_page(self, image_path, **kwargs):
        assert Path(image_path).is_file(), "backend phải lưu ảnh trước khi gọi module AI"
        self.describe_calls.append((Path(image_path), kwargs))
        return self.describe_result

    def ask_page(self, image_path, question, **kwargs):
        assert Path(image_path).is_file()
        self.ask_calls.append((question, kwargs))
        return self.answer_result


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "vlm_mode", "ai")
    shutil.copytree(REPO_ROOT / "data" / "library", tmp_path / "library")
    yield


@pytest.fixture
def fake(monkeypatch):
    f = FakePipeline()
    monkeypatch.setattr(ai_bridge, "_pipeline", lambda: f)
    return f


@pytest.fixture
def client():
    return TestClient(app)


def jpeg(color=(200, 180, 120), size=(800, 1100)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="JPEG")
    return buf.getvalue()


def describe(client, color=(200, 180, 120)):
    return client.post("/v1/describe", files={"image": ("trang.jpg", jpeg(color), "image/jpeg")},
                       data={"page_type": "auto"})


def test_describe_ok_maps_contract_to_api_v1(client, fake):
    r = describe(client)
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    # trường API v1 (app cũ đọc)
    assert d["description"] == fake.describe_result.interpretation_vi
    assert d["page_type"] == "chart"
    assert d["unreadable"] is False
    assert d["model"] == "lmstudio/gemma-4-e4b" and d["prompt_version"] == "b0g_v1"
    # trường hợp đồng v0.1 (app mới đọc)
    assert d["status"] == "ok" and d["image_type"] == "bar_chart"
    assert d["summary_vi"] == "Biểu đồ cột số sách." and d["question_answering_ready"] is True
    assert fake.describe_calls[0][1]["image_id"] == d["image_id"]


def test_describe_same_image_is_cached(client, fake):
    describe(client)
    second = describe(client).json()["data"]
    assert second["cached"] is True and second["status"] == "ok"
    assert len(fake.describe_calls) == 1


def test_capture_gate_unreadable_is_guidance_not_cached(client, fake):
    fake.describe_result = DescriptionResult(
        status="unreadable", summary_vi="Ảnh quá tối. Bạn bật đèn rồi chụp lại nhé.",
        uncertainties=["capture_gate:dark"])
    d = describe(client).json()["data"]
    assert d["unreadable"] is True and d["status"] == "unreadable"
    assert d["description"] == "Ảnh quá tối. Bạn bật đèn rồi chụp lại nhé."
    assert d["prompt_version"] == "capture_gate"
    assert describe(client).json()["data"]["cached"] is False
    assert len(fake.describe_calls) == 2


def test_partial_means_truncated_not_unreadable(client, fake):
    fake.describe_result = DescriptionResult(
        status="partial", summary_vi="Bảng số ngày mưa.", interpretation_vi="Bảng có năm hàng tháng và ba cột",
        uncertainties=["Câu trả lời bị cắt do giới hạn độ dài."], meta=_meta())
    d = describe(client).json()["data"]
    assert d["status"] == "partial" and d["unreadable"] is False
    assert d["description"].startswith("Bảng có năm hàng")


def test_b0_result_unknown_type_is_mixed_and_flag_passed_through(client, fake):
    """B0 (phương pháp hiện tại của module AI): image_type="unknown", question_answering_ready=False."""
    fake.describe_result = DescriptionResult(
        image_type="unknown", status="ok", summary_vi="Lược đồ vùng núi.",
        interpretation_vi="Lược đồ vùng núi phía Bắc. Phía tây có dãy Hoàng Liên Sơn.",
        question_answering_ready=False, meta=_meta())
    d = describe(client).json()["data"]
    assert d["page_type"] == "mixed" and d["image_type"] == "unknown"
    assert d["question_answering_ready"] is False and d["unreadable"] is False


def test_looping_description_is_cut_marked_partial_and_not_cached(client, fake):
    """Mô hình nhỏ lặp một câu tới hết token: chỉ đọc một lần, báo bị cắt ngắn, lần sau gọi lại mô hình."""
    loop = "Cột thứ Hai cao nhất, bốn mươi quyển."
    fake.describe_result = DescriptionResult(
        status="partial", summary_vi="Biểu đồ cột.", meta=_meta(),
        interpretation_vi="Biểu đồ cột có năm cột. " + " ".join([loop] * 15) + " Cột thứ",
        uncertainties=["Câu trả lời bị cắt do giới hạn độ dài."])
    d = describe(client).json()["data"]
    assert d["description"] == "Biểu đồ cột có năm cột. " + loop
    assert d["status"] == "partial" and d["unreadable"] is False
    assert "loop_cut" in d["uncertainties"]
    assert describe(client).json()["data"]["cached"] is False
    assert len(fake.describe_calls) == 2


def test_looping_ok_result_becomes_partial(client, fake):
    fake.describe_result = DescriptionResult(
        status="ok", summary_vi="Lược đồ.", meta=_meta(),
        interpretation_vi="Lược đồ vùng núi. " + "Phía tây có dãy Hoàng Liên Sơn. " * 4)
    d = describe(client).json()["data"]
    assert d["status"] == "partial" and d["description"] == "Lược đồ vùng núi. Phía tây có dãy Hoàng Liên Sơn."


def test_looping_answer_is_cut(client, fake):
    image_id = describe(client).json()["data"]["image_id"]
    fake.answer_result = AnswerResult(status="ok", meta=_meta("ask_calc_v1"),
                                      answer_vi="Cột thứ Hai cao nhất. " * 8)
    r = client.post("/v1/ask", json={"image_id": image_id, "question": "Cột nào cao nhất?"})
    assert r.json()["data"]["answer"] == "Cột thứ Hai cao nhất."


@pytest.mark.parametrize("code,http,api_code", [
    ("timeout", 504, "VLM_TIMEOUT"),
    ("config_error", 503, "AI_NOT_CONFIGURED"),
    ("invalid_image", 400, "INVALID_IMAGE"),
    ("http_error", 502, "VLM_ERROR"),
    ("empty_response", 502, "VLM_ERROR"),
])
def test_ai_errors_become_api_v1_errors(client, fake, code, http, api_code):
    fake.describe_result = DescriptionResult(
        status="error", error=ErrorInfo(code=code, message="chi tiết nội bộ", retryable=True))
    r = describe(client)
    assert r.status_code == http
    body = r.json()
    assert body["data"] is None and body["error"]["code"] == api_code
    assert "chi tiết nội bộ" not in body["error"]["message"], "không lộ chi tiết nội bộ cho người dùng"


def test_ask_passes_history_as_pairs(client, fake):
    image_id = describe(client).json()["data"]["image_id"]
    r = client.post("/v1/ask", json={"image_id": image_id, "question": "Cột nào cao nhất?",
                                      "history": [{"question": "Có mấy cột?", "answer": "Năm cột."}]})
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["answer"] == "Cột thứ Hai cao nhất." and d["prompt_version"] == "ask_calc_v1"
    question, kwargs = fake.ask_calls[0]
    assert question == "Cột nào cao nhất?"
    assert kwargs["history"] == [("Có mấy cột?", "Năm cột.")]
    assert kwargs["image_id"] == image_id


def test_ask_error_is_mapped(client, fake):
    image_id = describe(client).json()["data"]["image_id"]
    fake.answer_result = AnswerResult(status="error", error=ErrorInfo(code="timeout", message="x", retryable=True))
    r = client.post("/v1/ask", json={"image_id": image_id, "question": "Cột nào cao nhất?"})
    assert r.status_code == 504 and r.json()["error"]["code"] == "VLM_TIMEOUT"


def test_health_reports_ai_model_from_ai_env(client, tmp_path, monkeypatch):
    ai_dir = tmp_path / "ai_cfg"
    ai_dir.mkdir()
    (ai_dir / ".env").write_text("VLM_PROVIDER=lmstudio\nLMSTUDIO_MODEL=google/gemma-4-e4b\n", encoding="utf-8")
    monkeypatch.setattr(settings, "ai_dir", ai_dir)
    for k in ("VLM_PROVIDER", "LMSTUDIO_MODEL"):
        monkeypatch.delenv(k, raising=False)
    d = client.get("/health").json()["data"]
    assert d["vlm_mode"] == "ai" and d["ai_module"] is True
    assert d["model"] == "lmstudio:google/gemma-4-e4b"


def test_real_pipeline_blocks_dark_photo_without_network(client, monkeypatch):
    """Pipeline thật của Phúc: ảnh đen bị cổng chất lượng chặn, trả lời hướng dẫn chụp lại, không gọi VLM."""
    monkeypatch.setenv("VLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")  # nếu lỡ gọi mạng thì sẽ báo lỗi cấu hình, test trượt
    d = describe(client, color=(3, 3, 3)).json()["data"]
    assert d is not None, "ảnh đen phải được chặn trước khi gọi mô hình"
    assert d["status"] == "unreadable" and d["unreadable"] is True
    assert any(u.startswith("capture_gate:") for u in d["uncertainties"])
    assert d["description"], "phải có lời hướng dẫn chụp lại"

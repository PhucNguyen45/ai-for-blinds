import json
from pathlib import Path

import httpx
import pytest
from PIL import Image
from pydantic import ValidationError

from contract.models import CONTRACT_VERSION, DescriptionResult, ErrorInfo
from vlm.describer import _extract_summary, describe_image

ENV = {"OPENROUTER_API_KEY": "test-key", "OPENROUTER_BASE_URL": "https://example.test/api/v1",
       "OPENROUTER_MODEL": "test/model"}
B0_TEXT = ("1. Chủ đề: Biểu đồ cột về số sách mượn. Đây là câu thứ hai.\n\n"
           "2. Thành phần: Năm cột.\n\n3. Quan hệ: Thứ 2 cao nhất.\n\n4. Ý nghĩa: So sánh.")


@pytest.fixture
def image(tmp_path):
    p = tmp_path / "x.png"
    Image.new("RGB", (20, 20), "white").save(p)
    return p


def fake_post(status=200, content=B0_TEXT, finish="stop", raises=None):
    def post(payload, api_key, base_url, timeout=60.0):
        if raises:
            raise raises
        assert payload["reasoning"] == {"enabled": False}
        body = {"choices": [{"message": {"content": content}, "finish_reason": finish}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
        return httpx.Response(status, json=body)
    return post


def run(image, **kw):
    return describe_image(image, env=ENV, image_id="img-1", **kw)


def test_ok_result_follows_contract(image):
    r = run(image, post=fake_post())
    assert r.status == "ok" and r.schema_version == CONTRACT_VERSION
    assert r.image_id == "img-1" and len(r.image_sha256) == 64
    assert r.summary_vi == "Biểu đồ cột về số sách mượn."
    assert r.interpretation_vi == B0_TEXT
    assert r.meta.usage.completion_tokens == 5 and r.meta.finish_reason == "stop"
    assert r.question_answering_ready is False  # B0 chưa trích xuất cấu trúc
    DescriptionResult.model_validate_json(r.model_dump_json())  # khứ hồi


def test_truncated_response_is_partial(image):
    r = run(image, post=fake_post(finish="length"))
    assert r.status == "partial" and r.uncertainties


@pytest.mark.parametrize("kwargs,code,retryable", [
    (dict(status=429), "http_error", True),
    (dict(status=500), "http_error", True),
    (dict(status=400), "http_error", False),
    (dict(content=""), "empty_response", True),
    (dict(raises=httpx.ReadTimeout("t")), "timeout", True),
    (dict(raises=httpx.ConnectError("c")), "http_error", True),
])
def test_operational_errors_do_not_raise(image, kwargs, code, retryable):
    r = run(image, post=fake_post(**kwargs))
    assert r.status == "error" and r.error.code == code and r.error.retryable is retryable
    assert r.interpretation_vi == "" and r.image_sha256


def test_error_message_never_contains_api_key(image):
    r = run(image, post=fake_post(raises=httpx.ConnectError("boom test-key")))
    assert "test-key" not in r.model_dump_json()


def test_invalid_image_and_config(tmp_path, image):
    assert describe_image(tmp_path / "none.png", env=ENV).error.code == "invalid_image"
    txt = tmp_path / "a.txt"
    txt.write_text("x")
    assert describe_image(txt, env=ENV).error.code == "invalid_image"
    r = describe_image(image, env={})
    assert r.error.code == "config_error" and not r.error.retryable
    r = describe_image(image, env=ENV, prompt_id="../secret")
    assert r.error.code == "config_error"


def test_summary_fallback_first_sentence():
    assert _extract_summary("Ảnh mờ. Không đọc được.") == "Ảnh mờ."


@pytest.mark.parametrize("bad", [
    dict(status="error"),                                       # thiếu error
    dict(status="ok"),                                          # thiếu interpretation
    dict(status="ok", interpretation_vi="x", error=ErrorInfo(  # error không đi với ok
        code="unknown", message="m", retryable=False)),
    dict(status="unreadable"),                                  # thiếu lý do
    dict(status="unreadable", summary_vi="mờ", question_answering_ready=True),
    dict(status="ok", interpretation_vi="x", unknown_field=1),  # trường lạ
])
def test_contract_rejects_inconsistent_results(bad):
    with pytest.raises(ValidationError):
        DescriptionResult(**bad)


def test_published_examples_are_valid():
    for path in sorted((Path(__file__).parents[1] / "contract" / "examples").glob("*.json")):
        DescriptionResult.model_validate_json(path.read_text(encoding="utf-8"))

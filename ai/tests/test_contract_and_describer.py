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


# ----- B1 -----
from vlm.describer import describe_image_b1, parse_extraction  # noqa: E402

JSON1 = ('{"image_type": "bar_chart", "status": "ok", "facts": ['
         '{"subject": "Cột Thứ 2", "predicate": "có giá trị", "object": "40 quyển", '
         '"evidence": "nhãn trên cột"}], "uncertainties": []}')


def seq_post(*replies):
    """Mỗi phần tử: (status, content, finish) hoặc Exception; gọi lần lượt."""
    calls = iter(replies)
    seen = []

    def post(payload, api_key, base_url, timeout=60.0):
        seen.append(payload)
        r = next(calls)
        if isinstance(r, Exception):
            raise r
        status, content, finish = r
        body = {"choices": [{"message": {"content": content}, "finish_reason": finish}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
        return httpx.Response(status, json=body)
    post.seen = seen
    return post


def test_b1_two_stage_ok(image):
    post = seq_post((200, "```json\n" + JSON1 + "\n```", "stop"), (200, B0_TEXT, "stop"))
    r = describe_image_b1(image, env=ENV, image_id="i", post=post)
    assert r.status == "ok" and r.image_type == "bar_chart" and r.meta.method == "B1"
    assert len(r.facts) == 1 and r.facts[0].object == "40 quyển"
    assert r.question_answering_ready is True
    assert r.meta.usage.completion_tokens == 10 and len(post.seen) == 2
    stage2_content = post.seen[1]["messages"][0]["content"]
    assert all(part["type"] == "text" for part in stage2_content)  # bước 2 không gửi ảnh
    assert "40 quyển" in stage2_content[0]["text"]
    assert "nhãn trên cột" not in stage2_content[0]["text"]  # evidence không đưa vào bước 2


def test_b1_unreadable_skips_second_call(image):
    unreadable = '{"image_type": "line_chart", "status": "unreadable", "facts": [], "uncertainties": ["Ảnh quá mờ."]}'
    post = seq_post((200, unreadable, "stop"))
    r = describe_image_b1(image, env=ENV, post=post)
    assert r.status == "unreadable" and r.summary_vi == "Ảnh quá mờ." and len(post.seen) == 1


@pytest.mark.parametrize("replies,code", [
    ([(200, "không phải json", "stop")], "invalid_output"),
    ([(200, '{"facts": []}', "stop")], "invalid_output"),
    ([(500, "x", "stop")], "http_error"),
    ([(200, JSON1, "stop"), httpx.ReadTimeout("t")], "timeout"),
    ([(200, JSON1, "stop"), (200, "", "stop")], "empty_response"),
])
def test_b1_failures_return_error(image, replies, code):
    r = describe_image_b1(image, env=ENV, post=seq_post(*replies))
    assert r.status == "error" and r.error.code == code and r.meta.method == "B1"


def test_b1_truncated_is_partial(image):
    r = describe_image_b1(image, env=ENV,
                          post=seq_post((200, JSON1, "length"), (200, B0_TEXT, "stop")))
    assert r.status == "partial" and r.question_answering_ready is False


def test_parse_extraction_tolerates_noise_and_bad_types():
    out = parse_extraction('Đây:\n{"image_type": "xyz", "facts": [1, {"subject": "a", '
                           '"predicate": 3, "object": "b"}], "uncertainties": "x"} hết')
    assert out["image_type"] == "other" and len(out["facts"]) == 1
    assert out["facts"][0].predicate == "3" and out["uncertainties"] == []

from pathlib import Path

import httpx
import pytest
from PIL import Image
from pydantic import ValidationError

from contract.models import CONTRACT_VERSION, AnswerResult, DescriptionResult, ErrorInfo
from vlm.common import extract_summary as _extract_summary
from vlm.describer import describe_image

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
        model = AnswerResult if path.name.startswith("answer_") else DescriptionResult
        model.model_validate_json(path.read_text(encoding="utf-8"))


# ----- B1 -----
from vlm.b1 import describe_image_b1, parse_extraction  # noqa: E402

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


# ----- Nhà cung cấp: OpenRouter / Google AI Studio -----
from vlm.client import build_chat_payload, post_chat_completion  # noqa: E402
from vlm.providers import ConfigError, resolve_provider  # noqa: E402

GENV = {"GOOGLE_API_KEY": "g-secret", "GOOGLE_MODEL": "gemini-2.5-flash"}


def test_resolve_default_is_openrouter():
    p = resolve_provider(ENV)
    assert p.name == "openrouter" and p.model == "test/model" and p.reasoning_effort is None


def test_resolve_google_and_model_name_normalization():
    p = resolve_provider(GENV, provider="google")
    assert p.name == "google" and p.model == "gemini-2.5-flash"
    assert p.base_url == "https://generativelanguage.googleapis.com/v1beta/openai"
    assert p.reasoning_effort == "none"
    assert resolve_provider(GENV, "google", "google/gemini-2.5-flash-lite").model == "gemini-2.5-flash-lite"
    assert resolve_provider({**GENV, "GOOGLE_REASONING_EFFORT": ""}, "google").reasoning_effort is None
    assert resolve_provider({"GEMINI_API_KEY": "k", "GOOGLE_MODEL": "m"}, "google").api_key == "k"


def test_provider_from_env_variable_and_overrides():
    assert resolve_provider({**ENV, **GENV, "VLM_PROVIDER": "google"}).name == "google"
    assert resolve_provider({**ENV, **GENV, "VLM_PROVIDER": "google"}, provider="openrouter").name == "openrouter"


@pytest.mark.parametrize("cfg,prov", [({}, None), ({"GOOGLE_API_KEY": "k"}, "google"),
                                      (ENV, "bogus"), ({"OPENROUTER_API_KEY": "k"}, None)])
def test_resolve_errors_are_config_errors_without_secrets(cfg, prov):
    with pytest.raises(ConfigError) as exc:
        resolve_provider(cfg, prov)
    assert "k" != str(exc.value) and "g-secret" not in str(exc.value)


def test_provider_repr_hides_key():
    assert "g-secret" not in repr(resolve_provider(GENV, "google"))


def test_payload_differs_by_provider():
    o = build_chat_payload("m", "p", None, 0.2, 100)
    assert o["reasoning"] == {"enabled": False} and "reasoning_effort" not in o
    g = build_chat_payload("m", "p", None, 0.2, 100, provider="google", reasoning_effort="none")
    assert "reasoning" not in g and g["reasoning_effort"] == "none"
    assert "reasoning_effort" not in build_chat_payload("m", "p", None, provider="google")


def test_headers_only_send_app_identity_to_openrouter(monkeypatch):
    seen = {}

    class FakeClient:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def post(self, url, headers, json):
            seen["url"], seen["headers"] = url, headers
            return httpx.Response(200, json={})
    monkeypatch.setattr(httpx, "Client", FakeClient)
    post_chat_completion({}, "k", "https://openrouter.ai/api/v1")
    assert "HTTP-Referer" in seen["headers"] and seen["url"].endswith("/chat/completions")
    post_chat_completion({}, "k", "https://generativelanguage.googleapis.com/v1beta/openai")
    assert "HTTP-Referer" not in seen["headers"] and "X-Title" not in seen["headers"]
    assert seen["headers"]["Authorization"] == "Bearer k"


def test_describe_with_google_provider_uses_google_payload(image):
    seen = {}

    def post(payload, api_key, base_url, timeout=60.0):
        seen.update(payload=payload, key=api_key, base=base_url)
        return httpx.Response(200, json={"choices": [{"message": {"content": B0_TEXT},
                                                      "finish_reason": "stop"}]})
    r = describe_image(image, env=GENV, provider="google", post=post)
    assert r.status == "ok" and r.meta.provider == "google" and r.meta.model == "gemini-2.5-flash"
    assert "reasoning" not in seen["payload"] and seen["payload"]["reasoning_effort"] == "none"
    assert seen["key"] == "g-secret" and "generativelanguage" in seen["base"]
    assert "g-secret" not in r.model_dump_json()


def test_b1_with_google_provider(image):
    post = seq_post((200, JSON1, "stop"), (200, B0_TEXT, "stop"))
    r = describe_image_b1(image, env=GENV, provider="google", post=post)
    assert r.status == "ok" and r.meta.provider == "google"
    assert all("reasoning" not in p and p["reasoning_effort"] == "none" for p in post.seen)


def test_missing_google_key_returns_config_error_not_exception(image):
    r = describe_image(image, env={"OPENROUTER_API_KEY": "k"}, provider="google")
    assert r.status == "error" and r.error.code == "config_error"


# ----- Làm sạch Markdown + thông báo HTTP -----
from vlm.common import strip_markdown  # noqa: E402

MD = ("**1. Chủ đề:**\nBiểu đồ cột về số sách. Câu hai.\n\n**2. Thành phần:**\n"
      "- Tiêu đề chính: \"Số sách\"\n- Trục *đứng*: số quyển\n\n### 3. Quan hệ\n`Thứ 2` cao nhất.")


def test_strip_markdown_removes_markup_but_keeps_text():
    out = strip_markdown(MD)
    assert "*" not in out and "#" not in out and "`" not in out and not out.startswith("-")
    assert "Tiêu đề chính" in out and "Trục đứng" in out and "Thứ 2 cao nhất" in out


def test_summary_survives_markdown_response(image):
    r = run(image, post=fake_post(content=MD))
    assert r.summary_vi == "Biểu đồ cột về số sách."
    assert "**" not in r.interpretation_vi


@pytest.mark.parametrize("status", [400, 404])
def test_http_400_404_message_hints_model_name(image, status):
    r = run(image, post=fake_post(status=status))
    assert r.error.http_status == status and "tên model" in r.error.message


def test_model_prefix_from_google_listing_is_normalized():
    assert resolve_provider(GENV, "google", "models/gemini-3.8-flash").model == "gemini-3.8-flash"


# ----- LM Studio -----
import vlm.providers as providers  # noqa: E402

LENV = {"LMSTUDIO_BASE_URL": "http://172.26.160.1:1234/v1/", "LMSTUDIO_MODEL": "qwen3-vl-4b"}


def test_lmstudio_provider_from_explicit_url():
    p = resolve_provider(LENV, "lmstudio")
    assert (p.name, p.base_url, p.model) == ("lmstudio", "http://172.26.160.1:1234/v1", "qwen3-vl-4b")
    assert p.api_key == "lm-studio" and p.timeout >= 120 and p.reasoning_effort is None


def test_lmstudio_autodetect_and_model_discovery(monkeypatch):
    monkeypatch.setattr(providers, "find_lmstudio_url", lambda: "http://10.0.0.5:1234/v1")
    monkeypatch.setattr(providers, "first_lmstudio_model", lambda base: "auto-model")
    p = resolve_provider({}, "lmstudio")
    assert p.base_url == "http://10.0.0.5:1234/v1" and p.model == "auto-model"


def test_lmstudio_unreachable_or_no_model_gives_actionable_config_error(monkeypatch):
    monkeypatch.setattr(providers, "find_lmstudio_url", lambda: None)
    with pytest.raises(ConfigError, match="Serve on Local"):
        resolve_provider({}, "lmstudio")
    monkeypatch.setattr(providers, "first_lmstudio_model", lambda base: None)
    with pytest.raises(ConfigError, match="chưa nạp model"):
        resolve_provider({"LMSTUDIO_BASE_URL": "http://h:1234/v1"}, "lmstudio")


def test_lmstudio_candidates_include_wsl_gateway(monkeypatch):
    monkeypatch.setattr(providers, "_wsl_gateway", lambda: "172.26.160.1")
    monkeypatch.setattr(providers, "_wsl_nameserver", lambda: "10.255.255.254")
    assert providers.lmstudio_candidates() == [
        "http://localhost:1234/v1", "http://172.26.160.1:1234/v1", "http://10.255.255.254:1234/v1"]


def test_lmstudio_payload_has_no_provider_specific_reasoning_fields():
    pl = build_chat_payload("m", "p", None, provider="lmstudio")
    assert "reasoning" not in pl and "reasoning_effort" not in pl


def test_lmstudio_describe_and_connection_error_message(image):
    seen = {}

    def ok(payload, api_key, base_url, timeout=60.0):
        seen.update(base=base_url, timeout=timeout, key=api_key)
        return httpx.Response(200, json={"choices": [{"message": {"content": B0_TEXT},
                                                      "finish_reason": "stop"}]})
    r = describe_image(image, env=LENV, provider="lmstudio", post=ok)
    assert r.status == "ok" and r.meta.provider == "lmstudio" and seen["timeout"] >= 120
    assert seen["base"] == "http://172.26.160.1:1234/v1"
    r = describe_image(image, env=LENV, provider="lmstudio",
                       post=fake_post(raises=httpx.ConnectError("refused")))
    assert r.error.code == "http_error" and "LM Studio" in r.error.message and r.error.retryable
    r = describe_image_b1(image, env=LENV, provider="lmstudio",
                          post=seq_post(httpx.ConnectError("refused")))
    assert "LM Studio" in r.error.message


# ----- Khôi phục JSON hỏng của bước trích xuất -----
BROKEN = ('{"image_type": "flow_diagram", "status": "ok", "facts": ['
          '{"subject": "A", "predicate": "đi đến", "object": "B", '
          '"evidence": "mũi tên từ "A" đến "B""}, '
          '{"subject": "B", "predicate": "đi đến", "object": "C", "evidence": "mũi tên từ "B" đến "C""}], '
          '"uncertainties": []}')


def test_parse_extraction_salvages_unescaped_quotes():
    out = parse_extraction(BROKEN)
    assert out["salvaged"] is True and out["image_type"] == "flow_diagram"
    assert [(f.subject, f.object) for f in out["facts"]] == [("A", "B"), ("B", "C")]
    assert parse_extraction(JSON1)["salvaged"] is False


def test_b1_with_salvaged_json_is_ok_and_flagged(image):
    r = describe_image_b1(image, env=ENV, post=seq_post((200, BROKEN, "stop"), (200, B0_TEXT, "stop")))
    assert r.status == "ok" and len(r.facts) == 2
    assert any("khôi phục" in u for u in r.uncertainties)


def test_unrecoverable_json_still_invalid_output(image):
    r = describe_image_b1(image, env=ENV, post=seq_post((200, '{"facts": [oops', "stop")))
    assert r.error.code == "invalid_output"


# ---------------------------------------------------------------- "ảnh không đọc được" do model tự báo (prompt b0g_v1)

def _png(tmp_path):
    p = tmp_path / "x.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
    return p


def _fake_reply(text, finish="stop"):
    def post(payload, api_key, base_url, timeout=None):
        return httpx.Response(200, json={"choices": [{"message": {"content": text}, "finish_reason": finish}],
                                         "usage": {"prompt_tokens": 10, "completion_tokens": 5}})
    return post


LM_ENV = {"VLM_PROVIDER": "lmstudio", "LMSTUDIO_BASE_URL": "http://x/v1", "LMSTUDIO_MODEL": "m"}


def test_model_reported_unreadable_becomes_unreadable_status(tmp_path):
    reply = "KHÔNG ĐỌC ĐƯỢC: Ảnh bị mờ. Bạn giữ yên máy rồi chụp lại nhé."
    r = describe_image(_png(tmp_path), prompt_id="b0g_v1", post=_fake_reply(reply), env=LM_ENV)
    assert r.status == "unreadable" and r.summary_vi.startswith("Ảnh bị mờ")
    assert r.interpretation_vi == "" and r.error is None


def test_normal_description_is_not_flagged_unreadable(tmp_path):
    reply = "1. Chủ đề: Biểu đồ cột.\n2. Thành phần: Thứ Hai 40."
    r = describe_image(_png(tmp_path), prompt_id="b0g_v1", post=_fake_reply(reply), env=LM_ENV)
    assert r.status == "ok"


def test_phrase_inside_sentence_is_not_a_flag(tmp_path):
    reply = "Có một ô không đọc được rõ nhưng biểu đồ vẫn đọc được: Thứ Hai 40."
    assert describe_image(_png(tmp_path), prompt_id="b0g_v1", post=_fake_reply(reply), env=LM_ENV).status == "ok"


# ---------------------------------------------------------------- bộ lọc ký tự ngoài tiếng Việt

def _seq_post(*texts):
    it = iter(texts)

    def post(payload, api_key, base_url, timeout=None):
        return httpx.Response(200, json={"choices": [{"message": {"content": next(it)}, "finish_reason": "stop"}],
                                         "usage": {"prompt_tokens": 4, "completion_tokens": 2}})
    return post


def test_foreign_script_triggers_one_retry_and_clean_text_is_used(tmp_path):
    r = describe_image(_png(tmp_path), post=_seq_post("Điểm là tám phẩy零 năm.", "Điểm là tám phẩy năm."), env=LM_ENV)
    assert r.interpretation_vi == "Điểm là tám phẩy năm." and r.uncertainties == []
    assert r.meta.usage.prompt_tokens == 8  # cộng cả hai lượt gọi


def test_persistent_foreign_script_is_removed_and_flagged(tmp_path):
    r = describe_image(_png(tmp_path), post=_seq_post("Giá trị 知 là năm.", "Giá trị 知 là năm."), env=LM_ENV)
    assert "知" not in r.interpretation_vi and r.interpretation_vi == "Giá trị là năm."
    assert any("ngoài tiếng Việt" in u for u in r.uncertainties)


def test_vietnamese_text_never_triggers_retry(tmp_path):
    calls = []

    def post(payload, api_key, base_url, timeout=None):
        calls.append(1)
        return httpx.Response(200, json={"choices": [{"message": {"content": "Biểu đồ cột: Thứ Hai bốn mươi ắ ằ ẳ ẵ ặ đ."}, "finish_reason": "stop"}]})
    describe_image(_png(tmp_path), post=post, env=LM_ENV)
    assert len(calls) == 1

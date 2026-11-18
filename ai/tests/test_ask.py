import json

import httpx
import pytest
from PIL import Image

from contract.models import AnswerResult
from vlm.ask import ACK, MAX_HISTORY_TURNS, ask_about_image

def ask_plain(*a, **k):
    return ask_about_image(*a, calc=False, **k)


ENV = {"VLM_PROVIDER": "lmstudio", "LMSTUDIO_BASE_URL": "http://x/v1", "LMSTUDIO_MODEL": "m"}


@pytest.fixture
def img(tmp_path):
    p = tmp_path / "p.png"
    Image.new("RGB", (8, 8), "white").save(p)
    return p


def reply(text, finish="stop", seen=None):
    def post(payload, api_key, base_url, timeout=None):
        if seen is not None:
            seen.append(payload)
        return httpx.Response(200, json={"choices": [{"message": {"content": text}, "finish_reason": finish}],
                                         "usage": {"prompt_tokens": 7, "completion_tokens": 3}})
    return post


def test_ok_answer_is_cleaned_and_follows_contract(img):
    r = ask_plain(img, "Cột nào cao nhất?", post=reply("**Cột Thứ Hai** cao nhất,\n bằng bốn mươi."), env=ENV)
    assert r.status == "ok" and r.answer_vi == "Cột Thứ Hai cao nhất, bằng bốn mươi."
    assert r.meta.prompt_id == "ask_v1" and r.meta.usage.prompt_tokens == 7
    AnswerResult.model_validate(json.loads(r.model_dump_json()))


def test_context_order_matches_training_format(img):
    seen = []
    ask_plain(img, "Còn cột Thứ Ba?", description="Biểu đồ cột.", history=[("Cột nào cao nhất?", "Thứ Hai.")],
                    post=reply("Ba mươi.", seen=seen), env=ENV)
    roles = [m["role"] for m in seen[0]["messages"]]
    assert roles == ["system", "user", "assistant", "user", "assistant", "user"]
    msgs = seen[0]["messages"]
    assert msgs[2]["content"] == ACK and msgs[-1]["content"] == "Còn cột Thứ Ba?"
    assert any(p.get("type") == "image_url" for p in msgs[1]["content"])
    assert "Biểu đồ cột." in msgs[1]["content"][0]["text"]


def test_history_is_trimmed(img):
    seen = []
    hist = [(f"q{i}", f"a{i}") for i in range(20)]
    ask_plain(img, "hỏi", history=hist, post=reply("ok", seen=seen), env=ENV)
    assert len(seen[0]["messages"]) == 3 + 2 * MAX_HISTORY_TURNS + 1
    assert seen[0]["messages"][3]["content"] == f"q{20 - MAX_HISTORY_TURNS}"


def test_truncated_answer_is_partial(img):
    assert ask_plain(img, "hỏi", post=reply("Một hai", finish="length"), env=ENV).status == "partial"


@pytest.mark.parametrize("q,code", [("", "invalid_input"), ("   ", "invalid_input"), ("x" * 600, "invalid_input")])
def test_bad_question_is_an_error_without_calling_model(img, q, code):
    def boom(*a, **k):
        raise AssertionError("không được gọi model")
    r = ask_plain(img, q, post=boom, env=ENV)
    assert r.status == "error" and r.error.code == code and not r.error.retryable


def test_missing_image_and_timeout_and_http_errors(tmp_path, img):
    assert ask_plain(tmp_path / "no.png", "hỏi", env=ENV).error.code == "invalid_image"

    def slow(*a, **k):
        raise httpx.ReadTimeout("t")
    assert ask_plain(img, "hỏi", post=slow, env=ENV).error.code == "timeout"

    def bad(*a, **k):
        return httpx.Response(503, json={})
    r = ask_plain(img, "hỏi", post=bad, env=ENV)
    assert r.error.code == "http_error" and r.error.retryable and r.error.http_status == 503


def test_empty_answer_is_an_error(img):
    assert ask_plain(img, "hỏi", post=reply("  \n "), env=ENV).error.code in ("empty_response",)


# ---------------------------------------------------------------- tính toán bằng mã (calc=True, mặc định)

def seq_reply(*texts):
    it = iter(texts)

    def post(payload, api_key, base_url, timeout=None):
        return httpx.Response(200, json={"choices": [{"message": {"content": next(it)}, "finish_reason": "stop"}],
                                         "usage": {"prompt_tokens": 5, "completion_tokens": 2}})
    return post


def test_model_writes_expression_and_code_computes(img):
    js = json.dumps({"can_tinh": True, "bieu_thuc": "40+35+5+19+6",
                     "tra_loi_mau": "Tổng số sách mượn trong tuần là {kq} quyển."})
    r = ask_about_image(img, "Tổng là bao nhiêu?", post=seq_reply(js), env=ENV)
    assert r.answer_vi == "Tổng số sách mượn trong tuần là một trăm linh năm quyển."
    assert r.meta.prompt_id == "ask_calc_v1"


def test_model_miscalculation_is_ignored_because_code_computes(img):
    js = json.dumps({"can_tinh": True, "bieu_thuc": "3*4/2", "tra_loi_mau": "Diện tích là {kq} cm vuông, tức mười hai."})
    assert "sáu" in ask_about_image(img, "Diện tích?", post=seq_reply(js), env=ENV).answer_vi


def test_non_calculation_question_uses_json_answer(img):
    js = json.dumps({"can_tinh": False, "tra_loi": "Cột Thứ Hai cao nhất."})
    r = ask_about_image(img, "Cột nào cao nhất?", post=seq_reply(js), env=ENV)
    assert r.answer_vi == "Cột Thứ Hai cao nhất."


@pytest.mark.parametrize("bad", [
    "không phải JSON",
    json.dumps({"can_tinh": True, "bieu_thuc": "__import__('os')", "tra_loi_mau": "{kq}"}),
    json.dumps({"can_tinh": True, "bieu_thuc": "2+2", "tra_loi_mau": "không có chỗ trống"}),
    json.dumps({"can_tinh": True, "bieu_thuc": "1/0", "tra_loi_mau": "{kq}"}),
])
def test_bad_calc_output_falls_back_to_plain_answer(img, bad):
    r = ask_about_image(img, "hỏi", post=seq_reply(bad, "Câu trả lời trực tiếp."), env=ENV)
    assert r.answer_vi == "Câu trả lời trực tiếp." and r.meta.prompt_id == "ask_calc_v1+ask_v1"
    assert r.meta.usage.prompt_tokens == 10  # cộng cả hai lượt gọi

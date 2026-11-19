# Module AI (`ai/`)

Phần AI của hệ thống: ảnh trang sách đã chụp → kiểm tra chất lượng ảnh → mô tả bằng VLM → hỏi đáp → chuẩn bị đọc ra giọng nói.
Backend (Nam) chỉ cần gọi `pipeline.py`. Hợp đồng đầu ra: `contract/` (bản nháp v0.1, chưa thống nhất với API v1).

```
pipeline.py            describe_page(), ask_page()  <- điểm vào cho backend
capture/quality.py     cổng chất lượng ảnh (tối, mờ, cháy sáng) + câu hướng dẫn chụp lại
vlm/                   gọi VLM: providers (OpenRouter/Google/LM Studio), client, describer (B0/B0e/B0g),
                       b1 (hai bước), ask (hỏi đáp), common (phần dùng chung)
speech/                chuẩn hóa văn bản cho TTS (số, đơn vị ra chữ); chưa có engine STT/TTS
contract/              mô hình Pydantic, JSON Schema, ví dụ của DescriptionResult và AnswerResult
prompts/               prompt có phiên bản (b0_v1, b0e_v1, b0g_v1, b1_*, ask_v1, ask_calc_v1, ft_describe_v1 chuẩn bị cho fine-tune)
evaluation/            benchmark, chạy thực nghiệm, báo cáo (xem mục Đánh giá bên dưới)
finetune/              bộ sinh tập huấn luyện tổng hợp (dữ liệu chỉ ở máy tác giả)
external_data/         khảo sát, tải, kiểm tra trùng, phân mục và phân vai train/val/test các bộ dữ liệu Hugging Face (dữ liệu ở data/external/, không có trong repo)
docs/textbook/         hướng dẫn nạp ảnh SGK
tests/                 kiểm thử, không gọi mạng
```

## Chạy

```bash
cp .env.example .env              # điền khóa; KHÔNG commit .env
uv run pytest -q                  # kiểm thử, không gọi mô hình thật
uv run python vlm/list_models.py --provider lmstudio
```

```python
from pipeline import describe_page, ask_page

result = describe_page("trang.jpg", provider="lmstudio")      # DescriptionResult
if result.status == "unreadable":
    ...                                                       # result.summary_vi là lời hướng dẫn chụp lại
answer = ask_page("trang.jpg", "Cột nào cao nhất?")            # AnswerResult; câu tính toán do mã tính (vlm/calc.py)
# Câu hỏi về vị trí/hướng: nên chỉ truyền ảnh; truyền description=... làm kết quả tệ hơn (đo trên dev)
```

Lỗi vận hành (mạng, HTTP, cấu hình, ảnh hỏng) trả `status="error"` kèm `error`, không ném ngoại lệ.

## Các trạng thái cần hệ thống xử lý

| `status` | Nghĩa | Việc của app |
|---|---|---|
| `ok`, `partial` | Có lời diễn giải (`partial`: bị cắt do giới hạn độ dài) | Đọc `interpretation_vi` |
| `unreadable` | Ảnh không đọc được; `summary_vi` là hướng dẫn chụp lại | Đọc `summary_vi`, mở camera lại |
| `error` | Lỗi vận hành, `error.retryable` cho biết có nên thử lại | Báo lỗi hoặc thử lại |

## Đánh giá (`evaluation/`)

Mọi lệnh chạy từ thư mục `ai/` (`uv run python ...`). Dữ liệu benchmark ở `data/benchmark/` **chỉ có ở máy tác giả**. Báo cáo kết quả ở `evaluation/reports/` (liên kết từ `README.md` gốc).

| Thư mục | Vai trò |
|---|---|
| `generators/` | sinh và kiểm tra benchmark tổng hợp, nạp ảnh SGK (`ingest_textbook.py`), tải ảnh Wikimedia (`fetch_commons_candidates.py`) |
| `runner/` | `run_b1_dev.py` (B0e/B1 trên tập dev), `survey_lmstudio.py` (khảo sát model LM Studio theo độ phóng ảnh/prompt), `run_qa_dev.py` (hỏi đáp trên câu hỏi dev) |
| `reporting/` | `proposition_check.py`, `repeat_stats.py`, `survey_report.py`, `qa_score.py`, `capture_gate_eval.py`, `archive_runs.py`, bộ chấm rubric (`create_scorecards`, `validate_score`, `finalize_score`, `summarize_scores`) |
| `reports/` | báo cáo Markdown |
| `rubrics/` | `rubric_v1.md` (C1–C6, chấm tay) |
| `legacy_b0/` | quy trình B0 theo phiên (2026-10) và script thử OpenRouter gốc; chỉ để tái hiện số liệu cũ |
| `records_*/`, `runs/`, `sessions/`, `scores/` | bản ghi đầu ra từng lần chạy, **không** có trong git |

Quy ước: chỉ số phủ mệnh đề là từ khóa thô, chạm trần và không đo độ bịa; không dùng làm điểm rubric. Tập test chưa chạy (giữ đóng băng); không sửa ground truth sau khi xem đầu ra model.

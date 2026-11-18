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
prompts/               prompt có phiên bản (b0_v1, b0e_v1, b0g_v1, b1_*, ask_v1)
evaluation/            benchmark, chạy thực nghiệm, báo cáo (xem evaluation/README.md)
finetune/              bộ sinh tập huấn luyện tổng hợp (dữ liệu chỉ ở máy tác giả)
external_data/         khảo sát, tải và kiểm tra trùng các bộ dữ liệu Hugging Face (dữ liệu ở data/external/, không có trong repo)
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

# Hợp đồng đầu ra module AI — BẢN NHÁP v0.1

> **Trạng thái:** đề xuất của Mảng A (Phúc). **Chưa** được Mảng B (Nam), Mảng C (Toàn) hay giảng viên
> xác nhận. Không phải API cuối cùng. Thay đổi làm đổi nghĩa trường → tăng `schema_version`
> và báo các bên.

> Hành vi nội dung (không giải bài tập, chỉ trả lời điều được hỏi) theo [Quy cách đầu ra](../README.md#quy-cách-đầu-ra-chốt-ngày-27112026).
> Hợp đồng v0.1 **chưa** có trường nào thể hiện quy cách này (ví dụ ảnh là bài tập, hoặc câu hỏi bị từ chối vì xin đáp án).

## Dùng thế nào

```python
from pipeline import describe_page, ask_page

result = describe_page("hinh.png", image_id="img-001")    # DescriptionResult (qua cổng chất lượng ảnh)
result.status                # "ok" | "partial" | "unreadable" | "unsupported" | "error"
result.interpretation_vi     # văn bản tiếng Việt để đọc bằng TTS
result.model_dump_json()     # JSON trả cho app
```

`describe_page` và `ask_page` **không ném ngoại lệ** vì lỗi vận hành (mạng, HTTP, cấu hình, ảnh): nó trả
`status="error"` kèm `error.code` và `error.retryable`. Backend chỉ cần xử lý một dạng kết quả.

## Trường chính (`contract/models.py`, JSON Schema: `schema_v0_1.json`, ví dụ: `examples/`)

| Trường | Ý nghĩa |
|---|---|
| `schema_version` | `"0.1"` |
| `image_id` | Do backend cấp; AI chỉ trả lại. `image_sha256` do AI tính. |
| `image_type` | bar_chart, line_chart, pie_chart, table, flow_diagram, cycle_diagram, geometry, map, text, other, unknown |
| `status` | `ok`, `partial` (bị cắt), `unreadable` (ảnh không đọc được), `unsupported`, `error` |
| `summary_vi` | Tóm tắt để phát trước |
| `facts[]` | `subject/predicate/object/evidence`. **`evidence` do VLM tự nêu, không chứng minh dữ kiện đúng** |
| `interpretation_vi` | Diễn giải đầy đủ, không Markdown/JSON |
| `uncertainties[]` | Điều chưa chắc chắn/thiếu |
| `question_answering_ready` | Đủ căn cứ để hỏi đáp tiếp; chỉ có nghĩa khi `ok`/`partial` |
| `meta` | provider (openrouter/google/lmstudio), model, method (B0/B1), prompt_id, prompt_sha256, tham số, finish_reason, độ trễ, token |
| `error` | `code` (invalid_image, invalid_input, config_error, timeout, http_error, empty_response, invalid_output, unknown), `message`, `retryable`, `http_status` |

`ask_page(...)` trả `AnswerResult` (`answer_vi`, `status` ok/partial/error, `meta`, `error`; schema `answer_schema_v0_1.json`).
Khi cổng chất lượng ảnh chặn ảnh: `status="unreadable"`, `summary_vi` là lời hướng dẫn chụp lại, `uncertainties=["capture_gate:<lỗi>"]`
và **không có `meta`** (chưa gọi model). Mã lỗi `invalid_input` dùng cho câu hỏi trống hoặc quá dài.

Ràng buộc nhất quán được kiểm bằng Pydantic (vd `error` chỉ đi với `status="error"`).

## Hạn chế hiện tại

- Phương pháp mặc định là **B0** (prompt `b0g_v1`, văn bản 4 mục): `facts` rỗng, `image_type="unknown"`,
  `question_answering_ready=False`. Các trường này chỉ được điền khi có B1, mà B1 chưa dùng trong `pipeline.py`
  (kém hơn trên 4B, xem nhật ký 17/11).
- `status="unreadable"` có hai nguồn: cổng chất lượng ảnh (chặn ảnh tối/mờ nặng/cháy sáng, không gọi VLM) và
  prompt `b0g_v1` tự báo khi không đọc được. Độ chính xác của nguồn thứ hai chưa đo được trên trang SGK thật:
  đo trên 32 trang, 5 trang sạch bị báo nhầm (xem `ai/evaluation/reports/system_modules_4b_20261118.md`, số đo với Qwen 4B).

## Điểm cần thống nhất với Nam/Toàn

1. `image_id` do ai cấp và định dạng (hiện: chuỗi tự do).
2. Có thêm trạng thái `error` và mã lỗi như trên không (đề xuất mới so với báo cáo 23/10).
3. Hội thoại nhiều lượt: định danh phiên/ngữ cảnh (chưa thiết kế).
4. Timeout mặc định 60 s cho nhà cung cấp đám mây, 300 s cho LM Studio (mô hình cục bộ chậm hơn); chính sách thử lại do backend quyết định (`retryable` chỉ là gợi ý).
5. Chính sách lưu/xóa ảnh và nội dung nhạy cảm.

## Kiểm thử và tái tạo

```bash
uv run pytest -q                                   # toàn bộ module ai, không gọi API thật (kiểm contract: test_contract_and_describer.py)
uv run python -m contract.export_contract   # xuất lại schema + ví dụ
```

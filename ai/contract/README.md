# Hợp đồng đầu ra module AI — BẢN NHÁP v0.1

> **Trạng thái:** đề xuất của Mảng A (Phúc). **Chưa** được Mảng B (Nam), Mảng C (Toàn) hay giảng viên
> xác nhận. Không phải API cuối cùng. Thay đổi làm đổi nghĩa trường → tăng `schema_version`
> và báo các bên.

## Dùng thế nào

```python
from vlm.describer import describe_image

result = describe_image("hinh.png", image_id="img-001")   # DescriptionResult
result.status                # "ok" | "partial" | "unreadable" | "unsupported" | "error"
result.interpretation_vi     # văn bản tiếng Việt để đọc bằng TTS
result.model_dump_json()     # JSON trả cho app
```

`describe_image` **không ném ngoại lệ** vì lỗi vận hành (mạng, HTTP, cấu hình, ảnh): nó trả
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
| `meta` | provider (openrouter/google), model, method (B0/B1), prompt_id, prompt_sha256, tham số, finish_reason, độ trễ, token |
| `error` | `code` (invalid_image, config_error, timeout, http_error, empty_response, invalid_output, unknown), `message`, `retryable`, `http_status` |

Ràng buộc nhất quán được kiểm bằng Pydantic (vd `error` chỉ đi với `status="error"`).

## Hạn chế hiện tại

- Chỉ có phương pháp **B0** (văn bản 4 mục): `facts` rỗng, `image_type="unknown"`,
  `question_answering_ready=False`. Các trường này chỉ được điền khi có B1.
- `status="unreadable"` hiện chưa được mô-đun tự phát hiện; sẽ cần phương pháp đánh giá riêng.

## Điểm cần thống nhất với Nam/Toàn

1. `image_id` do ai cấp và định dạng (hiện: chuỗi tự do).
2. Có thêm trạng thái `error` và mã lỗi như trên không (đề xuất mới so với báo cáo 23/10).
3. Hội thoại nhiều lượt: định danh phiên/ngữ cảnh (chưa thiết kế).
4. Timeout mặc định 60 s; chính sách thử lại do backend quyết định (`retryable` chỉ là gợi ý).
5. Chính sách lưu/xóa ảnh và nội dung nhạy cảm.

## Kiểm thử và tái tạo

```bash
uv run pytest -q                                   # 18 kiểm thử, không gọi API thật
PYTHONPATH=. uv run python contract/export_contract.py   # xuất lại schema + ví dụ
```

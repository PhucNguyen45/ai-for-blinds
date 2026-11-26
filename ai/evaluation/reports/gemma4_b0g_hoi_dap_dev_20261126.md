# Gemma 4 E4B trên tập dev: cổng "không đọc được" (b0g_v1) và hỏi đáp theo hình

> **Trạng thái:** thăm dò. **Ngày:** 2026-11-26 · **Mảng:** A
> **Kết luận ngắn:** trên 22 ảnh dev, `b0g_v1` báo "không đọc được" đúng cả 6 lượt ảnh mờ và **không báo nhầm** lượt nào trên 60 lượt ảnh đọc được. Hỏi đáp ảnh-only đạt 42/59 (71%), Qwen cùng điều kiện đạt 40/59 (68%): chênh 2 câu, trong nhiễu. Chỉ số từ khóa thô, ảnh tổng hợp; chưa kiểm tra trên trang SGK thật.

## 1. Điều kiện

- Model: `google/gemma-4-e4b` (Q4_K_M) trên LM Studio cục bộ; **reasoning tắt** (`LMSTUDIO_REASONING_EFFORT=none`).
- Tập dev, benchmark v0.2.0. Tập test không được chạy.
- **Cổng "không đọc được" (`b0g_v1`)**: 22 ảnh × 3 lần lặp, `max_tokens` 600. Lệnh:
  ```bash
  LMSTUDIO_REASONING_EFFORT=none uv run python evaluation/runner/run_b1_dev.py --method b0g --provider lmstudio --model google/gemma-4-e4b --reps 3 --max-requests 100 --execute
  ```
  Bản ghi: `ai/evaluation/records_b0g__lmstudio__google-gemma-4-e4b__reps/`. Chạy bị dừng giữa chừng để tạm nghỉ, rồi chạy tiếp; runner bỏ qua bản ghi đã có, nên không có lượt nào bị chạy lặp.
- **Hỏi đáp, chỉ có ảnh (không kèm mô tả)**: 59 câu hỏi dev. Lệnh:
  ```bash
  LMSTUDIO_REASONING_EFFORT=none uv run python evaluation/runner/run_qa_dev.py --tag gemma_off_img --model google/gemma-4-e4b --description none --max-requests 200 --execute
  ```
  Bản ghi: `ai/evaluation/records_qa__gemma_off_img/`.

## 2. Kết quả

### 2.1. Cổng "không đọc được" (`b0g_v1`)

| Nhóm ảnh | Số lượt | Báo đúng | Báo nhầm |
|---|---|---|---|
| Ảnh đọc được (`expected ok`) | 60 (20 ảnh × 3 lần) | — | **0** (60/60 trả `ok`) |
| Ảnh không đọc được (`_unreadable`) | 6 (2 ảnh × 3 lần) | **6/6** | — |

Hai ảnh mờ đều được báo đúng ở cả ba lần: `line_03_unreadable`, `cycle_01_unreadable`.

Cần đọc thận trọng: chỉ có 2 ảnh mờ, tổng hợp và rất rõ. Kết quả này chưa nói được gì về ảnh chụp thật. Trên Qwen, cùng prompt đã báo nhầm 5/32 trang SGK sạch (xem [báo cáo mô-đun](system_modules_4b_20261118.md)); **chưa chạy trang SGK với Gemma**, nên chưa biết Gemma có báo nhầm như vậy không.

### 2.2. Hỏi đáp theo hình (ảnh-only, 59 câu)

| Loại câu hỏi | Gemma (reasoning tắt) | Qwen3-VL-4B (ảnh-only, bản đã có) |
|---|---|---|
| comparison | 10/12 | 10/12 |
| computation | 11/15 | 8/15 |
| lookup | 15/16 | 15/16 |
| relation | 6/16 | 7/16 |
| **Tổng** | **42/59 (71,2%)** | **40/59 (67,8%)** |
| Thời gian TB mỗi câu | 2,1 s | 0,6 s (lưu ý: nhiều câu hỏi cùng ảnh nên dùng bộ nhớ đệm, không so sánh trực tiếp được) |

Số câu chênh nhau 2, nằm trong nhiễu của một lần chạy. Các câu `relation` (quan hệ vị trí, so sánh) vẫn yếu ở cả hai model: 6/16 và 7/16.

Lưu ý khi so sánh: bản ghi Qwen được chấm bằng cùng bộ `qa_score.py`, nhưng là lần chạy trước đó, không chạy cùng phiên với Gemma.

## 3. Giới hạn

- Chỉ số từ khóa thô (`qa_score.py`), không chấm bằng người.
- Một lần chạy mỗi điều kiện cho hỏi đáp (không lặp), 59 câu.
- Cổng `b0g` chỉ có 2 ảnh mờ, tổng hợp.
- Chưa chạy: trang SGK thật với `b0g` cho Gemma; hỏi đáp có kèm mô tả; `b0g` và hỏi đáp với reasoning bật.

## 4. Kết luận

- Với Gemma, cổng "không đọc được" đạt trên dev (6/6 báo đúng, 0 báo nhầm trên ảnh đọc được). Cần kiểm tra thêm trên trang SGK thật trước khi tin.
- Hỏi đáp ảnh-only của Gemma ngang Qwen (71% so với 68%, trong nhiễu). Điểm yếu vẫn là câu quan hệ không gian.

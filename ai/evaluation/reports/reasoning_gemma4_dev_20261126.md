# Reasoning bật/tắt của Gemma 4 E4B trên tập dev (B0e)

> **Trạng thái:** thăm dò. **Ngày:** 2026-11-26 · **Mảng:** A
> **Kết luận ngắn:** ở cùng `max_tokens` 2000, **tắt reasoning cho kết quả cao hơn** (121,3/141 so với 110,7/141 sau khi chuẩn hóa dấu thập phân) và tạo ít token hơn nhiều. Ở `max_tokens` 600, reasoning bật gần như không trả nội dung (0/141). Chỉ số từ khóa thô, 22 ảnh tổng hợp, 3 lần lặp: **không phải kết luận khoa học**.

## 1. Điều kiện

- Benchmark v0.2.0, tập **dev** (22 ảnh: 20 đọc được, 2 `_unreadable`), 141 mệnh đề critical. Tập test không được chạy.
- Model: `google/gemma-4-e4b` (Q4_K_M) trên LM Studio cục bộ, ctx 16384, parallel 1.
- Prompt `b0e_v1`, temperature 0,2, 3 lần lặp mỗi ảnh (66 request mỗi điều kiện).
- Cách bật/tắt reasoning: biến môi trường `LMSTUDIO_REASONING_EFFORT`. `none` = tắt (gửi `reasoning_effort=none`); để trống = không gửi tham số, Gemma dùng mặc định (bật).
- Lệnh chạy (từ `ai/`):
  ```bash
  LMSTUDIO_REASONING_EFFORT=none  uv run python evaluation/runner/run_b1_dev.py --method b0e --provider lmstudio --model google/gemma-4-e4b --reps 3 --max-requests 100 --max-tokens 2000 --execute
  LMSTUDIO_REASONING_EFFORT=      uv run python evaluation/runner/run_b1_dev.py --method b0e --provider lmstudio --model google/gemma-4-e4b --reps 3 --max-requests 100 --max-tokens 2000 --execute
  ```
  Tham số `--max-tokens` được thêm vào `run_b1_dev.py` ngày 2026-11-26 (mặc định 600, giữ nguyên hành vi cũ); thay đổi này chưa commit.

## 2. Kết quả

Chấm bằng `evaluation/reporting/repeat_stats.py` (chỉ số từ khóa thô, `proposition_check.py`).

| Điều kiện | Tổng mệnh đề (r01, r02, r03) | Trung bình (/141) | Độ lệch chuẩn | Ảnh ổn định hoàn toàn | Ghi chú |
|---|---|---|---|---|---|
| Tắt, 600 token | 121, 121, 122 | **121,3 (86,1%)** | 0,6 | 16/20 | `records_…-reasoning-off-mt600__reps` |
| Tắt, 2000 token | 121, 120, 123 | **121,3 (86,1%)** | 1,5 | 15/20 | `records_…-reasoning-off-mt2000__reps` |
| Bật, 600 token | 0, 0, 0 | **0 (0%)** | 0,0 | 20/20 | 18, 16, 19 request lỗi `empty_response`; `records_…-reasoning-on-mt600__reps` |
| Bật, 2000 token, chấm thô | 100, 102, 94 | 98,7 (70,0%) | 4,2 | 16/20 | `table_01` chỉ 3/15 do lỗi chấm (mục 3.1); `records_…-reasoning-on-mt2000__reps` |
| Bật, 2000 token, đã chuẩn hóa | 112, 114, 106 | **110,7 (78,5%)** | 4,2 | 16/20 | bản sao đã thay "8 phẩy 5" → "8,5", bản ghi gốc không sửa |

Thư mục bản ghi nằm trong `ai/evaluation/` và không được commit (theo README).

## 3. Phát hiện và giới hạn

1. **Lỗi chấm với dấu thập phân kiểu chữ ("phẩy").** Với reasoning bật ở 2000 token, 3/66 bản ghi (đúng 3 lần lặp của `table_01`) viết số kiểu "8 phẩy 5". `proposition_check.py` chỉ tìm dạng "8,5", nên `table_01` bị tính 3/15 thay vì 15/15. Sau khi chuẩn hóa, điểm đúng là 110,7. **Chưa sửa** `proposition_check.py`; cần sửa trước khi so sánh các lần chạy khác.
2. **Điểm 0 chưa giải thích ở `bar_01` và `bar_01_hard`.** Ví dụ `bar_01` r02/r03 và `bar_01_hard` r01 có status `ok`, nội dung trông đầy đủ về tiêu đề, trục và các nhãn, nhưng bộ chấm tính 0 mệnh đề. Chưa biết do bộ chấm hay do model. Cần kiểm tra thủ công trước khi kết luận.
3. **Chi phí sinh token.** Một ví dụ (`table_01` r01): reasoning bật ~1.311 token đầu ra, reasoning tắt ~332 token. Đây là một mẫu, chưa phải thống kê, nhưng cho thấy reasoning bật tốn nhiều thời gian sinh hơn.
4. **Ngân sách token là yếu tố quyết định.** Ở 600 token, reasoning bật không dùng được (phần suy nghĩ chiếm hết). Ở 2000 token, nó dùng được nhưng vẫn thấp hơn reasoning tắt.
5. **Giới hạn chung:** chỉ số từ khóa thô (không đo độ đúng, không đo bịa, không đo chiều quan hệ); ảnh tổng hợp sạch; 22 ảnh dev; chưa chấm rubric bằng người; tập test chưa chạy.

## 4. Kết luận và việc tiếp theo

- Giữ **reasoning tắt** (`LMSTUDIO_REASONING_EFFORT=none`) cho Gemma 4 E4B trong cấu hình hiện tại. Đây là lựa chọn có số liệu tốt hơn và nhanh hơn ở cùng điều kiện.
- Sửa `proposition_check.py` để nhận dạng dấu thập phân kiểu "phẩy", rồi chạy lại chấm cho cả hai điều kiện.
- Điều tra điểm 0 ở `bar_01` và `bar_01_hard` (bản ghi gốc trong thư mục `…-reasoning-on-mt2000__reps`).
- Chấm rubric bằng người trên các lần chạy dev trước khi dùng số liệu để chọn model.

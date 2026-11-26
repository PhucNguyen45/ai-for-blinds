# Reasoning bật/tắt của Gemma 4 E4B trên tập dev (B0e)

> **Trạng thái:** thăm dò. **Ngày:** 2026-11-26 · **Cập nhật:** 2026-11-26 (sửa bộ chấm: dấu "phẩy" và nhãn thứ; số liệu chấm lại) · **Mảng:** A
> **Kết luận ngắn:** ở cùng `max_tokens` 2000, **reasoning bật và tắt gần như ngang nhau** (120,0/141 so với 121,3/141, chênh 1,3 điểm, trong dao động). Reasoning bật tốn khoảng 4 lần số token đầu ra. Ở `max_tokens` 600, reasoning bật gần như không trả nội dung (0/141). Chỉ số từ khóa thô, 22 ảnh tổng hợp, 3 lần lặp: **không phải kết luận khoa học**.
> **Đính chính:** bản đầu của báo cáo này (cùng ngày) kết luận "tắt tốt hơn rõ rệt" (121 so với 111). Kết luận đó sai: phần chênh lớn là do bộ chấm bỏ sót dạng viết số "8 phẩy 5" và nhãn "Thứ Hai/Thứ Ba…" (xem mục 3). Số liệu dưới đây là sau khi sửa bộ chấm.

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
  Tham số `--max-tokens` được thêm vào `run_b1_dev.py` ngày 2026-11-26 (mặc định 600, giữ nguyên hành vi cũ).

## 2. Kết quả (bộ chấm đã sửa)

Chấm bằng `evaluation/reporting/repeat_stats.py` (chỉ số từ khóa thô, `proposition_check.py` đã sửa cùng ngày).

| Điều kiện | Tổng mệnh đề (r01, r02, r03) | Trung bình (/141) | Độ lệch chuẩn | Ảnh ổn định hoàn toàn | Ghi chú |
|---|---|---|---|---|---|
| Tắt, 600 token | 121, 121, 122 | **121,3 (86,1%)** | 0,6 | 16/20 | `records_…-reasoning-off-mt600__reps` |
| Tắt, 2000 token | 121, 120, 123 | **121,3 (86,1%)** | 1,5 | 15/20 | `records_…-reasoning-off-mt2000__reps` |
| Bật, 600 token | 0, 0, 0 | **0 (0%)** | 0,0 | 20/20 | 18, 16, 19 request lỗi `empty_response`; `records_…-reasoning-on-mt600__reps` |
| Bật, 2000 token | 119, 121, 120 | **120,0 (85,1%)** | 1,0 | 18/20 | `records_…-reasoning-on-mt2000__reps` |

Thư mục bản ghi nằm trong `ai/evaluation/` và không được commit (theo README). Các bản ghi không bị sửa; việc sửa nằm ở bộ chấm.

Số liệu của bản đầu (110,7 và 98,7) đã bị thay thế, không còn dùng.

## 3. Lỗi bộ chấm đã tìm ra và đã sửa

1. **Dấu thập phân kiểu chữ.** Có 3 bản ghi (đúng 3 lần lặp của `table_01`, reasoning bật 2000 token) viết "8 phẩy 5" thay vì "8,5". Bộ chấm cũ không nhận ra, nên `table_01` bị 3/15 thay vì 15/15. Đã thêm quy đổi "(số) phẩy (số)" → "số.số" vào `norm()`.
2. **Nhãn thứ viết chữ.** Ground truth ghi "Thứ 2", model viết "Thứ Hai". Đây là nguyên nhân của điểm 0 ở `bar_01` (r02, r03) và `bar_01_hard` (r01). Đã thêm quy đổi "thứ hai…thứ sáu" → "thứ 2…thứ 6". Số liệu nội dung của các bản ghi này đúng.
3. **Kiểm tra ảnh hưởng lên bản ghi cũ:** chấm lại Qwen B0e (3 lần lặp) vẫn 123/141 ở mọi lần, nên số liệu của [báo cáo so sánh 17/11](so_sanh_phuong_phap_va_model_dev_20261117.md) không đổi. Các bản ghi khảo sát và hỏi đáp của Qwen cũng có chứa nhãn thứ viết chữ, nên có thể thay đổi nhẹ nếu chấm lại; chưa chấm lại.

## 4. Phát hiện khác và giới hạn

- **Chi phí sinh token:** một ví dụ (`table_01` r01): reasoning bật ~1.311 token đầu ra, reasoning tắt ~332 token. Đây là một mẫu, chưa phải thống kê, nhưng cho thấy reasoning bật sinh nhiều hơn đáng kể.
- **Ngân sách token:** ở 600 token, reasoning bật không dùng được (phần suy nghĩ chiếm hết). Ở 2000 token, nó dùng được và ngang reasoning tắt trong dao động.
- **Lỗi chấm chưa biết hết:** bộ chấm chỉ đọc số và tên. Các lỗi quan hệ (chiều mũi tên, vị trí tương đối) không được chấm. Xem [chấm rubric mẫu](cham_rubric_gemma_sample_20261126.md): ca `cycle_03` sai chiều mũi tên ở cả hai điều kiện, mà chỉ số từ khóa không phát hiện.
- **Giới hạn chung:** chỉ số từ khóa thô; ảnh tổng hợp sạch; 22 ảnh dev; chưa có người chấm rubric; tập test chưa chạy.

## 5. Kết luận và việc tiếp theo

- Với Gemma 4 E4B, **reasoning tắt là lựa chọn nên giữ** trong cấu hình hiện tại (`LMSTUDIO_REASONING_EFFORT=none`): cùng chất lượng trên chỉ số thô, ít token hơn nhiều, không có rủi ro `empty_response`.
- Nếu muốn dùng reasoning bật, phải đặt `max_tokens` ≥ 2000 và chấm lại bằng người, vì chỉ số thô không thấy lỗi quan hệ.
- Chấm rubric bằng người (hai người độc lập) trước khi dùng số liệu để chọn model.

# Đánh giá (`ai/evaluation/`)

Mọi lệnh chạy từ thư mục `ai/` (`uv run python ...`). Dữ liệu benchmark ở `data/benchmark/` **chỉ có ở máy tác giả**.

| Thư mục | Vai trò | Dùng cho |
|---|---|---|
| `generators/` | Sinh benchmark tổng hợp, kiểm tra benchmark, nạp ảnh SGK, tải ảnh Wikimedia | Chuẩn bị dữ liệu |
| `runner/` | `run_b1_dev.py` (B0e/B1 trên tập dev), `survey_lmstudio.py` (khảo sát model LM Studio theo độ phóng ảnh/prompt), `run_qa_dev.py` (hỏi đáp trên câu hỏi dev) | Chạy thực nghiệm |
| `reporting/` | `proposition_check.py`, `repeat_stats.py`, `survey_report.py`, `qa_score.py`, `capture_gate_eval.py`, `archive_runs.py` và bộ chấm rubric (`create_scorecards`, `validate_score`, `finalize_score`, `summarize_scores`) | Chấm điểm, tổng hợp |
| `reports/` | Báo cáo đã viết (Markdown) | Kết quả, mới nhất ở đầu bảng bên dưới |
| `rubrics/` | `rubric_v1.md` (C1–C6, chấm tay) | Đánh giá bằng người |
| `reports/datasets/` | Tổng quan, báo cáo tải và lớp phủ train/val/test của dữ liệu ngoài (không chứa nội dung dữ liệu); công cụ ở `ai/external_data/` | Dữ liệu ngoài |
| `legacy_b0/` | Quy trình B0 theo phiên (10/2026) và script thử OpenRouter gốc | Chỉ để tái hiện số liệu cũ; đã được `runner/` thay thế |
| `records_*/`, `runs/`, `sessions/`, `scores/` | Bản ghi đầu ra từng lần chạy | **Không** có trong git (xem `.gitignore`) |

## Báo cáo

| File | Nội dung |
|---|---|
| `system_modules_4b_20261118.md` | Đo prompt báo "không đọc được" (`b0g_v1`) và hỏi đáp theo hình với 4B |
| `survey_qwen3vl_q4_20261117.md` | Khảo sát Qwen3-VL Q4 4B và 8B trên LM Studio (độ phóng ảnh, tốc độ, VRAM, chẩn đoán 8B chậm) |
| `capture_gate_20261118.md` | Cổng kiểm tra chất lượng ảnh trên dữ liệu tổng hợp |
| `dev_model_comparison_20261117.md` | So sánh model miễn phí (nemotron, gemini, qwen 4B) |
| `dev_b0_b0e_b1_20261117.md` | So sánh B0, B0e, B1 |
| `dev_b0_nemotron_20261117.md` | Thực nghiệm dev đầu tiên (B0, nemotron) |
| `baseline_b0_*.md`, `run_*.md`, `score_summary.csv` | Kết quả quy trình cũ (`legacy_b0/`) |

Quy ước: chỉ số phủ mệnh đề là từ khóa thô, chạm trần và không đo độ bịa; không dùng làm điểm rubric. Tập test chưa chạy
(giữ đóng băng); không sửa ground truth sau khi xem đầu ra model.

# So sánh model miễn phí trên tập dev — 2026-11-17

> **Trạng thái:** thăm dò trên tập **dev** (22 ảnh tổng hợp), 1 lần chạy mỗi ảnh, chỉ số từ khóa thô.
> **Không** đủ để kết luận model nào tốt hơn. Tập test chưa chạy. Chỉ dùng model miễn phí theo yêu cầu của Phúc.

## Điều kiện và độ phủ dữ liệu

| Điều kiện | Nhà cung cấp / model | Số ảnh có kết quả | Ghi chú |
|---|---|---:|---|
| B0, B0e, B1 | OpenRouter `nvidia/nemotron-3.5-super-vl:free` | 22/22 | Đã báo cáo ở `dev_b0_b0e_b1_20261117.md` |
| B0e | Google AI Studio `gemini-3.1-flash-lite` | 22/22 | Gói miễn phí |
| B0e | LM Studio cục bộ `qwen/qwen3-vl-4b` | 22/22 | RTX 2070 Max-Q 8 GB, trung vị 6,3 s |
| B1 | LM Studio cục bộ `qwen/qwen3-vl-4b` | 22/22 (2 lỗi `invalid_output`) | Trung vị 6,8 s |
| B0e | Google `gemini-3.8-flash` | **19/22 — không dùng để so** | Bị giới hạn 5 RPM / 20 RPD (429, 503); các bản ghi lỗi đã xóa để chạy lại sau |
| B0e | OpenRouter `gemma-4-31b-it:free` | 0/22 — chưa chạy được | 429 liên tục |

B0 (không có dòng "nêu đủ giá trị") chỉ có cho nemotron. Prompt B0e và B1 đóng băng, đồng nhất giữa các model.

## Phủ mệnh đề `critical` (chỉ số từ khóa chặt; 20 ảnh đọc được, 141 mệnh đề)

| Loại | Số mệnh đề | nemotron B0 | nemotron B0e | nemotron B1 | gemini-3.1-flash-lite B0e | **qwen3-vl-4b B0e** | qwen3-vl-4b B1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| bar_chart | 27 | 27 | 26 | 27 | 27 | 27 | 26 |
| line_chart | 19 | 17 | 17 | 17 | 17 | 17 | 10 |
| pie_chart | 12 | 8 | 10 | 8 | 12 | 12 | 9 |
| table | 33 | 20 | 23 | 33 | 33 | 33 | 33 |
| flow_diagram | 13 | 11 | 13 | 12 | 13 | 13 | 7 |
| cycle_diagram | 13 | 3 | 5 | 6 | 9 | 9 | 0* |
| geometry | 12 | 10 | 11 | 10 | 10 | 10 | 6 |
| schematic_map | 12 | 2 | 1 | 2 | 2 | 2 | 1 |
| **Tổng** | **141** | 98 (70%) | 106 (75%) | 115 (82%) | **123 (87%)** | **123 (87%)** | 92 (65%) |

\* Hai ảnh sơ đồ vòng bị `invalid_output` (JSON hỏng) nên tính 0. Khi khôi phục bằng bộ phân tích mới (chỉ offline từ văn bản đã lưu) vẫn còn các cạnh bị đọc sai, nên không coi đây là chênh lệch do lỗi cú pháp thuần túy.

## Phát hiện

1. **B0e với `qwen3-vl-4b` chạy cục bộ ngang `gemini-3.1-flash-lite` (123/141) và hơn nemotron (106/141)** trong cùng điều kiện (n=1, chỉ số thô). Model 4B miễn phí, chạy trên máy cá nhân, trung vị ≈6 s mỗi ảnh. Đây là ứng viên baseline hợp lý, nhất là cho hướng tự triển khai.
2. **Sai dấu tiếng Việt khi chép nhãn gần như biến mất** ở Qwen3-VL-4B và Gemini (pie 12/12, so với 8–10/12 ở nemotron). Lỗi này vì vậy nhiều khả năng là đặc trưng của model, không phải của bài toán.
3. **B1 không tốt hơn B0e với model nhỏ; có thể kém hơn.** Với 4B, bước trích xuất bỏ sót dữ kiện (vd `line_01`: chỉ 1 trong 6 điểm) và bước diễn giải không thể bù lại vì **không nhìn lại ảnh** (lan truyền lỗi giữa hai bước). Với nemotron, B1 giúp bảng (33/33) nhưng B0e của qwen/gemini cũng đạt 33/33 mà không cần hai bước. Ghi nhận cho RQ-A: lợi ích của B1 phụ thuộc chất lượng bước trích xuất, và cần so sánh với B0e cùng model.
4. **Lỗi định dạng của model nhỏ:** nháy kép không escape trong JSON (2/22 ảnh); lẫn nhãn kỹ thuật vào diễn giải (`flow_diagram` xuất hiện như một "thành phần"); nhầm `image_type` (sơ đồ vòng bị gọi là flow_diagram). Đã bổ sung bộ khôi phục JSON và đánh dấu trong `uncertainties`.
5. **Ảnh mờ:** B0e (mọi model) vẫn trả `status="ok"` kèm nói trong văn bản rằng ảnh mờ; chỉ B1 trả `unreadable` có cấu trúc (cả nemotron lẫn qwen, 2/2 ảnh). Đây là lợi ích về hợp đồng, chưa phải độ chính xác.
6. **Bản đồ vẫn ≈2/12 ở mọi điều kiện** do mệnh đề ground truth viết theo hướng tương đối; chỉ số này đang đánh giá thấp. Không sửa GT sau khi xem kết quả (v0.3).
7. **Giới hạn gói miễn phí:** Google `gemini-3.8-flash` 5 RPM / 250K TPM / 20 RPD không đủ cho 22 ảnh/ngày; `gemini-3.1-flash-lite` chạy liền được. OpenRouter free Gemma bị 429.

## Giới hạn

n = 1 lần chạy/ảnh, ảnh tổng hợp sạch, chỉ số từ khóa (phạt cách diễn đạt khác, không bắt bịa thêm), chưa chấm rubric bằng người, các model chạy ở thời điểm và nhà cung cấp khác nhau. Điểm bằng nhau ở hai model (123/141) nằm trong nhiễu một lần chạy.

## Việc tiếp theo (đề xuất)

1. Chạy lại `gemini-3.8-flash` ở ngày khác theo đợt nhỏ (≤15 ảnh/ngày) nếu muốn đưa vào so sánh.
2. Lặp ≥3 lần/ảnh cho `qwen3-vl-4b` B0e (chạy cục bộ nên rẻ) để ước lượng nhiễu.
3. Thử các model Qwen3-VL lớn hơn chạy cục bộ nếu VRAM cho phép (8B Q4), cho B1.
4. Chấm tay rubric_v1 cho các mẫu lỗi; chạy tập test khi cố định cấu hình.

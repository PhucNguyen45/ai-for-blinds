# Thực nghiệm B0 trên tập dev của benchmark v0.2.0 — 2026-11-17

> **Trạng thái:** thăm dò trên tập **dev** (mẫu tổng hợp). **Không** phải đánh giá chính thức,
> **không** dùng để chọn mô hình hay kết luận phương pháp. Tập test chưa được chạy.

## Cấu hình

| Trường | Giá trị |
|---|---|
| Benchmark | v0.2.0, tập dev (22 mẫu mới; 2 mẫu legacy đã chạy ngày 24/10 không chạy lại) |
| Model | `nvidia/nemotron-3.5-super-vl:free` qua OpenRouter ($0) |
| Prompt | `b0_v1` (sha256 trong file session) |
| Tham số | temperature 0.2, max_tokens 600, reasoning tắt, 1 lần chạy / ảnh |
| Session | `20261117T045818_607dc710` (10), `20261117T050131_679bd3a6` (10), `20261117T050132_14acae30` (2) |
| Kết quả kỹ thuật | 22/22 task hoàn tất, HTTP 200, `finish_reason=stop`; độ trễ 2,6–5 s (1 ngoại lệ 25,7 s: `table_01`) |

## Chỉ số thô: phủ mệnh đề `critical` (từ khóa)

Công cụ: `ai/evaluation/reporting/proposition_check.py`. Chỉ kiểm tra số/tên có xuất hiện trong câu trả lời;
**không đo độ đúng, không đo bịa đặt, không thay thế rubric_v1**. n = 1 lần chạy mỗi ảnh.

| Loại | Chặt | Bỏ qua dấu | Ghi chú |
|---|---:|---:|---|
| bar_chart | 20/20 | – | |
| line_chart | 17/19 | – | Chỉ thiếu mệnh đề "mức tăng lớn nhất giữa hai điểm liên tiếp" |
| pie_chart | 8/12 | 12/12 | Số đúng; sai dấu tiếng Việt ở nhãn |
| table | 20/33 | – | `table_03`: không đọc ô nào (5/18) |
| flow_diagram | 11/13 | 13/13 | Sai dấu/chính tả nhãn (vd "Thủ gom rác") |
| cycle_diagram | 3/13 | 6/13 | Xem phát hiện 3 |
| geometry | 7/9 | – | |
| schematic_map | 2/12 | – | Xem phát hiện 4 (chỉ số đánh giá thấp) |
| biến thể `_hard` | 10/10 | – | Xoay/tối/mờ nhẹ không ảnh hưởng ở n=2 |

Tổng chuỗi 3 session: 98/141 (70%) chặt (gồm 70/91 của session 1 và 28/50 của session 2).

## Phát hiện (cần chấm tay và lặp lại trước khi coi là kết luận)

1. **Sai dấu/chính tả tiếng Việt khi chép nhãn:** "Trống lúa", "Rau máu", "Thủ gom rác", "tại chê", "Rạ hoa",
   "khu phó", "hướng Bác". Dạng lỗi này đổi nghĩa từ khóa trong học liệu. Cần chỉ số CER/WER cho vùng chữ
   (đã có trong kế hoạch Mảng A) và so sánh sau khi thử ảnh độ phân giải cao hơn.
2. **Bỏ qua dữ liệu bảng:** `table_03` chỉ mô tả cấu trúc bảng, không đọc giá trị ô nào; `table_01` đọc đủ.
   B0 không yêu cầu rõ "đọc toàn bộ số liệu" nên chưa rõ lỗi do prompt hay do model.
3. **Bịa thành phần ở sơ đồ vòng:** `cycle_03` thêm giai đoạn "Hạt mọc" không có trong ảnh và bỏ "Hạt mới".
   Đây là loại lỗi "nội dung không có căn cứ", cần theo dõi bằng tiêu chí C5 của rubric.
4. **Bản đồ — chỉ số thấp do cách viết mệnh đề:** model nêu vị trí tuyệt đối (hàng/cột) đúng, nhưng
   không nêu hướng tương đối so với Trường học (mệnh đề dạng suy ra). Ngoài ra nói "sáu ô" khi có 5 nhãn.
   Không sửa ground truth sau khi xem kết quả; cân nhắc v0.3 thêm mệnh đề vị trí tuyệt đối.
5. **Ảnh không đọc được:** cả 2 ảnh `_unreadable` được báo là không đọc được nhãn/số liệu (đúng hành vi mong muốn).
   Tuy vậy model vẫn khẳng định "năm ô" (thực tế 4) và mô tả xu hướng đường mờ: cần chấm tay mức bịa.
6. **Hành vi tuân thủ prompt:** cả 22 phản hồi đều theo 4 mục; không thấy ký tự CJK như ở lần thăm dò 24/10
   (n nhỏ, không kết luận).

## Giới hạn

- Một model miễn phí, một prompt, một lần chạy mỗi ảnh; không có khoảng tin cậy.
- Ảnh tổng hợp sạch; không suy ra được chất lượng trên học liệu thật.
- Chỉ số từ khóa phạt cả cách diễn đạt khác và không bắt được lỗi bịa thêm.
- Ground truth do mã sinh nên không do VLM tạo (đúng quy ước), nhưng chưa có người thứ hai rà soát.

## Việc tiếp theo

- Chấm tay theo rubric_v1 (kèm bằng chứng) cho ít nhất các mẫu lỗi: `cycle_03`, `table_03`, `pie_03`, `map_01`.
- Thử B0 với yêu cầu rõ hơn về "đọc toàn bộ số liệu" như **B1 riêng biệt** (không sửa lại B0 trên dev rồi báo như cùng điều kiện).
- Lặp lại ≥3 lần/ảnh cho các mẫu quan trọng để ước lượng độ ổn định.
- Chỉ chạy tập test sau khi đóng băng prompt, model và rubric.

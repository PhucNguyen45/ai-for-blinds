# Chấm rubric_v1 (mẫu): Gemma 4 E4B, reasoning tắt và bật, 2000 token, lần r01

> **Trạng thái:** thăm dò. **Ngày:** 2026-11-26 · **Mảng:** A
> **Người đánh giá:** trợ lý AI (Claude), **không phải người chấm**. Rubric `rubric_v1` yêu cầu chấm tay bởi hai người; kết quả này chỉ là bản chấm sơ bộ để chọn ca cần người xem lại.
> **Căn cứ:** ground truth (`truth_v0.2`) và văn bản trả lời. **Chưa đối chiếu ảnh gốc.** Các điểm "1" ở C5 và C3 cần người xác nhận trên ảnh.

## 1. Phạm vi

Bốn ca lỗi đã nêu trong [báo cáo reasoning](reasoning_gemma4_dev_20261126.md): `cycle_03`, `pie_03`, `table_03`, `map_01`; lần lặp r01 của hai điều kiện (tắt và bật reasoning, 2000 token). Đây không phải toàn bộ tập dev. Mỗi bản ghi nằm trong `ai/evaluation/records_b0e__lmstudio__google-gemma-4-e4b__{reasoning-off,reasoning-on}-mt2000__reps/`.

## 2. Điểm (C1–C6, mỗi tiêu chí 0–2)

| Ca | Điều kiện | C1 | C2 | C3 | C4 | C5 | C6 | Tổng/12 |
|---|---|---|---|---|---|---|---|---|
| cycle_03 | tắt | 2 | 1 | 0 | 1 | 1 | 2 | **7** |
| cycle_03 | bật | 2 | 1 | 0 | 1 | 1 | 2 | **7** |
| pie_03 | tắt | 2 | 2 | 2 | 1 | 2 | 2 | **11** |
| pie_03 | bật | 2 | 2 | 2 | 1 | 1 | 2 | **10** |
| table_03 | tắt | 2 | 2 | 2 | 1 | 2 | 2 | **11** |
| table_03 | bật | 2 | 2 | 2 | 1 | 2 | 2 | **11** |
| map_01 | tắt | 2 | 2 | 1 | 1 | 2 | 2 | **10** |
| map_01 | bật | 2 | 2 | 1 | 1 | 1 | 2 | **9** |

## 3. Lý do trừ điểm

- **cycle_03 (cả hai):** nêu đúng năm giai đoạn nhưng **sai chiều các mũi tên**: ground truth là Gieo hạt → Hạt nảy mầm → Cây con → Ra hoa, kết quả → Hạt mới → Gieo hạt; câu trả lời nối theo thứ tự khác và nói chắc chắn. Đây là lỗi quan hệ (C3 = 0). Cùng lỗi có trong báo cáo định lượng.
- **pie_03 (bật):** giá trị và thứ tự đúng, nhưng thêm nhận định "phân bổ chủ yếu vào mục đích sản xuất nông nghiệp và sinh hoạt", không có trong ground truth (C5 = 1, chưa rõ có trên ảnh không).
- **table_03 (cả hai):** đủ 15 giá trị ô, các phép so sánh cực đại đúng; C4 = 1 vì phần diễn giải chung chung.
- **map_01 (tắt):** năm địa điểm đúng; quan hệ theo hướng tuyệt đối trên sơ đồ, không nêu quan hệ với "Trường học" như ground truth (C3 = 1).
- **map_01 (bật):** cùng vấn đề C3; thêm khẳng định "ba hàng ngang và ba cột dọc" chưa rõ có trên ảnh không (C5 = 1).

## 4. Nhận xét

- Trong bốn ca, hai điều kiện cho điểm gần như giống nhau. Chênh 1 điểm (pie_03, map_01) đến từ diễn đạt, không phải từ số liệu.
- Lỗi lớn nhất là **quan hệ/chiều** (cycle_03, map_01), không phải số liệu. Chỉ số từ khóa không bắt được lỗi này, nên cần người chấm hoặc chỉ số riêng cho quan hệ.
- Để có kết quả đủ tin cậy: hai người chấm độc lập trên ảnh gốc, cả 22 ảnh dev, ít nhất một lần chạy mỗi điều kiện.

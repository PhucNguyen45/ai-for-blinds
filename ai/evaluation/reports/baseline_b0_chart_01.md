# Nhật ký thực nghiệm B0-002

## Thông tin thử nghiệm

- Ngày: 24/10/2026
- Mô hình: nvidia/nemotron-3.5-super-vl:free
- Ảnh: data/local/chart_01.png
- Loại ảnh: Biểu đồ cột
- Dữ liệu: Tổng hợp, giả lập
- Chế độ reasoning: Tắt
- Temperature: 0.2
- Max tokens: 600
- Run ID: 20261024T012514_e8133560

## Kết quả kỹ thuật

- HTTP: 200
- Finish reason: stop
- Độ trễ: 7.904 giây
- Prompt tokens: 926
- Completion tokens: 200
- Tổng tokens: 1126
- Chi phí báo cáo: 0 USD

## Đáp án chuẩn

| Lớp | Số cây |
|---|---:|
| 3A | 12 |
| 3B | 18 |
| 3C | 15 |
| 3D | 9 |

- Lớn nhất: 3B, 18 cây
- Nhỏ nhất: 3D, 9 cây
- Chênh lệch: 9 cây
- Tổng: 54 cây

## Kết quả đối chiếu

- Đọc đúng 4/4 giá trị.
- Xác định đúng lớp cao nhất và thấp nhất.
- Tính đúng chênh lệch và tổng.
- Không phát hiện dữ kiện số bị bịa.
- Câu trả lời hoàn chỉnh, bằng tiếng Việt.

## Hạn chế

- Chỉ thử một ảnh tổng hợp.
- Biểu đồ có nhãn số phía trên từng cột.
- Chưa kiểm chứng khả năng đọc chiều cao cột khi không có nhãn.
- Chưa đánh giá chất lượng sử dụng thực tế với học sinh khiếm thị.

## Kết luận sơ bộ

Nemotron 3.5 Super VL Free hoàn thành chính xác
bài thử đọc và diễn giải biểu đồ cột đơn giản.

Kết quả này chưa đủ để kết luận mô hình có độ chính xác
cao trên các loại biểu đồ hoặc học liệu thực tế.

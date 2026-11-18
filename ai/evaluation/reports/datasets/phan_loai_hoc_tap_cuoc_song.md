# Dữ liệu ngoài: phân theo mục HỌC TẬP và CUỘC SỐNG

Không di chuyển dữ liệu. Khung nhìn bằng liên kết mềm: `data/external/1_hoc_tap/` và `data/external/2_cuoc_song/` (ViInfographicVQA có mặt ở cả hai vì chia theo chủ đề).
Số mẫu là số dòng/ảnh trong lớp phủ train/val/test (`splits_overlay.csv`), gồm cả mẫu bị loại (`excluded`). Phân loại dựa trên nội dung đã xem, xem cột lý do.

## 1. HỌC TẬP

| Bộ dữ liệu | Thư mục | Số mẫu | train | val | test | bị loại | Dung lượng (GB) | Nội dung |
|---|---|---|---|---|---|---|---|---|
| bbdontcry/ViSGKCap | `ViSGKCap/` | 1229 | 976 | 123 | 125 | 5 | 1.3 | Trang sách giáo khoa Cánh Diều lớp 1-3 (Toán, Tiếng Việt, Tự nhiên và Xã hội, Đạo đức). |
| D-Truong/ViEduVQA | `D-Truong__ViEduVQA/` | 18838 | 16985 | 999 | 854 | 0 | 6.8 | Hỏi đáp trên tranh minh họa tiểu học; đã xác nhận có trang SGK Cánh Diều (trùng ViSGKCap). Nội dung tranh là cảnh đời thường vẽ trong SGK. |
| VLAI-AIVN/ViInfographicVQA (một phần) | `VLAI-AIVN__ViInfographicVQA/` | 1768 | 1594 | 0 | 174 | 0 | 19.5 (cả bộ) | Infographic tin tức; chủ đề 'Giáo dục - Khoa Học' vào HỌC TẬP, 8 chủ đề còn lại (kinh tế, y tế, văn hóa, thiên tai, thể thao, thời tiết, quốc phòng, nhân vật) vào CUỘC SỐNG. |
| **Tổng** | | **21835** | 19555 | 1122 | 1153 | 5 | | |

## 2. CUỘC SỐNG

| Bộ dữ liệu | Thư mục | Số mẫu | train | val | test | bị loại | Dung lượng (GB) | Nội dung |
|---|---|---|---|---|---|---|---|---|
| VLAI-AIVN/ViInfographicVQA (một phần) | `VLAI-AIVN__ViInfographicVQA/` | 25388 | 22311 | 0 | 2487 | 590 | 19.5 (cả bộ) | Infographic tin tức; chủ đề 'Giáo dục - Khoa Học' vào HỌC TẬP, 8 chủ đề còn lại (kinh tế, y tế, văn hóa, thiên tai, thể thao, thời tiết, quốc phòng, nhân vật) vào CUỘC SỐNG. |
| uitnlp/OpenViVQA-dataset | `uitnlp__OpenViVQA-dataset/` | 11200 | 9045 | 1068 | 1000 | 87 | 1.7 | Ảnh đời thường ở Việt Nam (phố, quán, nhà, ghe), hỏi đáp mở. |
| Ouyangxuelili/vlsp2023-vqa-dataset | `Ouyangxuelili__vlsp2023-vqa-dataset/` | 9129 | 0 | 0 | 0 | 9129 | 1.4 | Bản sao một phần của OpenViVQA (cảnh đời thường); đã bị loại khỏi vai trò huấn luyện vì trùng. |
| huyhuy123/ViOCRVQA | `huyhuy123__ViOCRVQA/` | 28251 | 19394 | 4195 | 4238 | 424 | 6.5 | Ảnh bìa sách (không phải SGK): hỏi tên sách, tác giả, nhà xuất bản, thể loại. |
| 5CD-AI/Viet-Table-Markdown | `5CD-AI__Viet-Table-Markdown/` | 64901 | 58324 | 3329 | 3247 | 1 | 16.1 | Ảnh bảng/biểu mẫu trong báo cáo, tin tức, hành chính; từ khóa học đường chỉ ~5% (mẫu 400). |
| **Tổng** | | **138869** | 109074 | 8592 | 10972 | 10231 | | |

## Chủ đề của ViInfographicVQA (số Q/A trong parquet)

| Chủ đề | Mục | Số Q/A |
|---|---|---|
| Kinh tế - Hội nhập | CUỘC SỐNG | 5528 |
| Y tế - Cộng đồng | CUỘC SỐNG | 4214 |
| Văn hóa - Xã hội | CUỘC SỐNG | 2522 |
| Thiên tai - Tai nạn | CUỘC SỐNG | 2027 |
| Thể thao - Nghệ thuật | CUỘC SỐNG | 1686 |
| Dự báo thời tiết | CUỘC SỐNG | 1584 |
| Giáo dục - Khoa Học | HỌC TẬP | 1320 |
| Quốc phòng - An ninh | CUỘC SỐNG | 1027 |
| Nhân vật - Sự kiện | CUỘC SỐNG | 501 |

## Lưu ý

- Phân loại theo nội dung, không theo giấy phép. ViEduVQA CC BY-NC; các bộ khác phần lớn không khai báo giấy phép; ảnh SGK có bản quyền, chỉ dùng nghiên cứu nội bộ.
- ViEduVQA xếp HỌC TẬP vì có trang SGK; hình ảnh bên trong là cảnh đời thường vẽ cho trẻ em. Tỉ lệ ảnh thuộc SGK trong bộ chưa đo hết.
- Khoảng trống: chưa có SGK lớp 4-5, chưa có biểu đồ/bản đồ SGK thật; mục HỌC TẬP hiện chủ yếu là lớp 1-3.

# Dữ liệu ngoài: ba mục HỌC TẬP / CUỘC SỐNG / HỖN HỢP

Các thư mục bộ dữ liệu nằm thật trong `data/external/1_hoc_tap/`, `2_cuoc_song/`, `3_hon_hop/` (khai báo ở `hf.GROUPS`). `_index/`, `_reports/`, `_sft/` ở cấp trên.
Số mẫu là số dòng/ảnh trong lớp phủ train/val/test (`splits_overlay.csv`), gồm cả mẫu bị loại (`excluded`). Phân loại dựa trên nội dung đã xem, xem cột nội dung.

## 1. HỌC TẬP (`1_hoc_tap/`)

| Bộ dữ liệu | Thư mục | Số mẫu | train | val | test | bị loại | Dung lượng (GB) | Nội dung |
|---|---|---|---|---|---|---|---|---|
| bbdontcry/ViSGKCap | `ViSGKCap/` | 1229 | 976 | 123 | 125 | 5 | 1.3 | Trang sách giáo khoa Cánh Diều lớp 1-3 (Toán, Tiếng Việt, Tự nhiên và Xã hội, Đạo đức). |
| D-Truong/ViEduVQA | `D-Truong__ViEduVQA/` | 18838 | 16985 | 999 | 854 | 0 | 6.8 | Hỏi đáp trên tranh minh họa tiểu học; đã xác nhận có trang SGK Cánh Diều (trùng ViSGKCap). Nội dung tranh là cảnh đời thường vẽ trong SGK. |
| **Tổng** | | **20067** | 17961 | 1122 | 979 | 5 | | |

## 2. CUỘC SỐNG (`2_cuoc_song/`)

| Bộ dữ liệu | Thư mục | Số mẫu | train | val | test | bị loại | Dung lượng (GB) | Nội dung |
|---|---|---|---|---|---|---|---|---|
| uitnlp/OpenViVQA-dataset | `uitnlp__OpenViVQA-dataset/` | 11200 | 9045 | 1068 | 1000 | 87 | 1.7 | Ảnh đời thường ở Việt Nam (phố, quán, nhà, ghe), hỏi đáp mở. |
| Ouyangxuelili/vlsp2023-vqa-dataset | `Ouyangxuelili__vlsp2023-vqa-dataset/` | 9129 | 0 | 0 | 0 | 9129 | 1.4 | Bản sao một phần của OpenViVQA (cảnh đời thường); đã bị loại khỏi vai trò huấn luyện vì trùng. |
| huyhuy123/ViOCRVQA | `huyhuy123__ViOCRVQA/` | 28251 | 19394 | 4195 | 4238 | 424 | 6.5 | Ảnh bìa sách (không phải SGK): hỏi tên sách, tác giả, nhà xuất bản, thể loại. |
| 5CD-AI/Viet-Table-Markdown | `5CD-AI__Viet-Table-Markdown/` | 64901 | 58324 | 3329 | 3247 | 1 | 16.1 | Ảnh bảng/biểu mẫu trong báo cáo, tin tức, hành chính; từ khóa học đường chỉ ~5% (mẫu 400). |
| **Tổng** | | **113481** | 86763 | 8592 | 8485 | 9641 | | |

## 3. HỖN HỢP (`3_hon_hop/`)

| Bộ dữ liệu | Thư mục | Số mẫu | train | val | test | bị loại | Dung lượng (GB) | Nội dung |
|---|---|---|---|---|---|---|---|---|
| VLAI-AIVN/ViInfographicVQA | `VLAI-AIVN__ViInfographicVQA/` | 27156 | 23905 | 0 | 2661 | 590 | 19.5 | Infographic tin tức, 9 chủ đề; chỉ 'Giáo dục - Khoa Học' liên quan học tập, 8 chủ đề còn lại (kinh tế, y tế, văn hóa, thiên tai, thể thao, thời tiết, quốc phòng, nhân vật) là đời sống. Không tách vật lý được. |
| **Tổng** | | **27156** | 23905 | 0 | 2661 | 590 | | |

### Bên trong ViInfographicVQA (chia theo chủ đề, ánh xạ từng mẫu ở `_reports/phan_loai_infographic.csv`)

| Chủ đề | Thuộc | Số Q/A (parquet) |
|---|---|---|
| Kinh tế - Hội nhập | đời sống | 5528 |
| Y tế - Cộng đồng | đời sống | 4214 |
| Văn hóa - Xã hội | đời sống | 2522 |
| Thiên tai - Tai nạn | đời sống | 2027 |
| Thể thao - Nghệ thuật | đời sống | 1686 |
| Dự báo thời tiết | đời sống | 1584 |
| Giáo dục - Khoa Học | học tập | 1320 |
| Quốc phòng - An ninh | đời sống | 1027 |
| Nhân vật - Sự kiện | đời sống | 501 |

Tính cả ảnh jpg bổ sung: nội dung học tập 1768 mẫu (train 1594, test 174), đời sống 25388 mẫu (train 22311, test 2487, bị loại 590).

## Lưu ý

- Phân loại theo nội dung, không theo giấy phép. ViEduVQA CC BY-NC; các bộ khác phần lớn không khai báo giấy phép; ảnh SGK có bản quyền, chỉ dùng nghiên cứu nội bộ.
- ViEduVQA xếp HỌC TẬP vì có trang SGK; hình bên trong là cảnh đời thường vẽ cho trẻ em. Tỉ lệ ảnh thuộc SGK trong bộ chưa đo hết.
- Khoảng trống: chưa có SGK lớp 4-5, chưa có biểu đồ/bản đồ SGK thật; mục HỌC TẬP hiện chủ yếu là lớp 1-3.

# Lớp phủ phân vai train/val/test cho dữ liệu ngoài (overlay)

Giữ nguyên dữ liệu và split gốc; bảng ánh xạ nằm cục bộ ở `data/external/_reports/splits_overlay.csv`. Cụm ảnh = SHA-256 giống hệt, pHash cách <= 4 bit, hoặc cặp mức nội dung đã xác nhận bằng NCC >= 0.6 (cùng tranh, khác khung cắt); xuyên mọi bộ và benchmark của nhóm.

- Mẫu có vai trò: 160704; ảnh benchmark của nhóm tham gia gom cụm: 47; số cụm: 113220 (có nhiều mẫu: 18185).
- Cụm quá lớn bị tách và gắn cờ đáng ngờ: 7.
- **Kiểm tra bất biến (không cụm nào có cả train và val/test; cụm trùng benchmark không còn train/val/test):** ĐẠT.

| Bộ dữ liệu | Split gốc | Vai trò | Lý do | Số mẫu |
|---|---|---|---|---|
| 5CD-AI/Viet-Table-Markdown | train | excluded | leak_to_val | 1 |
| 5CD-AI/Viet-Table-Markdown | train | test | group_split | 3247 |
| 5CD-AI/Viet-Table-Markdown | train | train | group_split | 58316 |
| 5CD-AI/Viet-Table-Markdown | train | train | origin | 8 |
| 5CD-AI/Viet-Table-Markdown | train | val | group_split | 3329 |
| D-Truong/ViEduVQA | train | test | group_split | 854 |
| D-Truong/ViEduVQA | train | train | group_split | 16960 |
| D-Truong/ViEduVQA | train | train | origin | 25 |
| D-Truong/ViEduVQA | train | val | group_split | 999 |
| Ouyangxuelili/vlsp2023-vqa-dataset | khong_ro | excluded | duplicate_of_uitnlp/OpenViVQA-dataset | 9129 |
| VLAI-AIVN/ViInfographicVQA | train | excluded | leak_to_test | 590 |
| VLAI-AIVN/ViInfographicVQA | test | test | origin | 2661 |
| VLAI-AIVN/ViInfographicVQA | train | train | origin | 23905 |
| bbdontcry/ViSGKCap | train | excluded | leak_to_test | 1 |
| bbdontcry/ViSGKCap | train | excluded | leak_to_val | 4 |
| bbdontcry/ViSGKCap | test | test | origin | 125 |
| bbdontcry/ViSGKCap | train | train | origin | 976 |
| bbdontcry/ViSGKCap | val | val | origin | 123 |
| huyhuy123/ViOCRVQA | train | excluded | leak_to_test | 200 |
| huyhuy123/ViOCRVQA | val | excluded | leak_to_test | 42 |
| huyhuy123/ViOCRVQA | train | excluded | leak_to_val | 181 |
| huyhuy123/ViOCRVQA | khong_ro | excluded | origin_khong_ro | 1 |
| huyhuy123/ViOCRVQA | test | test | origin | 4238 |
| huyhuy123/ViOCRVQA | train | train | origin | 19394 |
| huyhuy123/ViOCRVQA | val | val | origin | 4195 |
| uitnlp/OpenViVQA-dataset | train | excluded | leak_to_test | 49 |
| uitnlp/OpenViVQA-dataset | val | excluded | leak_to_test | 2 |
| uitnlp/OpenViVQA-dataset | train | excluded | leak_to_val | 35 |
| uitnlp/OpenViVQA-dataset | khong_ro | excluded | origin_khong_ro | 1 |
| uitnlp/OpenViVQA-dataset | test | test | origin | 1000 |
| uitnlp/OpenViVQA-dataset | train | train | origin | 9045 |
| uitnlp/OpenViVQA-dataset | val | val | origin | 1068 |

Ghi chú: `group_split` = chia nội bộ theo cụm (5% val, 5% test) cho bộ chỉ có train, KHÔNG so sánh được với số liệu công bố; `leak_to_test/val` = ảnh trùng với tập đánh giá của bộ khác nên loại khỏi huấn luyện;
`benchmark_overlap` = trùng với benchmark dev/test của nhóm; `duplicate_of_*` = bản sao của bộ khác. Mức `content` (pHash 5-10 bit) chỉ được nối khi NCC >= 0.6; các ca NCC 0.5-0.6 (`review`) chưa xử lý, cần xem tay.

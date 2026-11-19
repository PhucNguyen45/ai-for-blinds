# Dữ liệu ngoài tiếng Việt cho VLM: khảo sát, tải, trùng lặp, phân mục và phân vai

> **Trạng thái:** thăm dò. **Ngày:** 2026-11-18 · **Cập nhật:** 2026-11-19 · **Mảng:** A
> **Kết luận ngắn:** đã tải và xác minh 7 bộ (~47 GB, 0 lỗi); 6 bộ bị khóa tạm bỏ qua. Có trùng đáng kể giữa các bộ (vlsp2023 là tập con của OpenViVQA; ViEduVQA chứa trang SGK của ViSGKCap; OpenViVQA rò rỉ giữa split),
> nên đã lập lớp phủ train/val/test theo cụm ảnh, không sửa dữ liệu gốc. Mục HỌC TẬP vẫn nhỏ và lệch (chủ yếu lớp 1-3); chưa có SGK lớp 4-5 hay biểu đồ/bản đồ SGK thật. Chú thích do máy sinh, chưa phải ground truth.

Nguyên tắc: không giả định giấy phép của bộ dữ liệu áp dụng cho ảnh SGK gốc; không trộn train/test giữa các nguồn; không xóa dữ liệu trùng khỏi bản gốc. Dữ liệu nằm ở `data/external/` (không có trong repo); công cụ ở `ai/external_data/`.

## 1. Thống kê theo bộ

Ảnh gốc = số bản ghi ảnh; ảnh duy nhất = theo SHA-256; ảnh trùng = ảnh gốc trừ ảnh duy nhất (với bộ nhiều Q/A mỗi ảnh, phần lớn là CÙNG ẢNH hỏi nhiều lần, không phải rác). Tải có resume, kiểm SHA-256 (tệp LFS), không ghi đè.

| Nhóm | Bộ dữ liệu | Truy cập | Giấy phép khai báo | Q/A hoặc chú thích | Split gốc | Ảnh gốc | Ảnh duy nhất | Ảnh trùng | Dung lượng thực (GB) | Tệp tải OK/tổng | Quyết định |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | bbdontcry/ViSGKCap | truy cập được | không khai báo | 1229 chú thích (không có Q/A) | train 981 / validation 123 / test 125 | 1229 | 1227 | 2 | 1.31 | 5/5 (tải trước đó) (lỗi 0) | da_crawl_truoc |
| A | D-Truong/ViEduVQA | truy cập được | cc-by-nc-4.0 | 18838 Q/A | chỉ train (không có test) | 18838 | 3915 | 14923 | 6.76 | 14/15 (lỗi 0) | tai |
| A | 5CD-AI/Viet-Doc-VQA-flash2 | bị khóa (gated=manual) | không khai báo |  |  |  |  |  | 0.0 | - (lỗi 0) | khong_tai_duoc |
| A | 5CD-AI/Viet-Doc-VQA-II-flash2 | bị khóa (gated=manual) | không khai báo |  |  |  |  |  | 0.0 | - (lỗi 0) | khong_tai_duoc |
| A | 5CD-AI/Viet-Doc-VQA-verIII | bị khóa (gated=manual) | không khai báo |  |  |  |  |  | 0.0 | - (lỗi 0) | khong_tai_duoc |
| B | 5CD-AI/Viet-OCR-VQA-flash2 | bị khóa (gated=manual) | không khai báo |  |  |  |  |  | 0.0 | - (lỗi 0) | khong_tai_duoc |
| B | 5CD-AI/Viet-Handwriting-OCR-v2 | bị khóa (gated=manual) | cc-by-nc-nd-4.0 |  |  |  |  |  | 0.0 | - (lỗi 0) | khong_tai_duoc |
| B | huyhuy123/ViOCRVQA | truy cập được | không khai báo | 123780 Q/A (train 86592 / dev 18587 / test 18601) | train / dev / test trong data/*.json của zip | 28251 | 28101 | 150 | 6.5 | 3/4 (lỗi 0) | tai |
| B | VLAI-AIVN/ViInfographicVQA | truy cập được | không khai báo | 20409 Q/A (đơn ảnh 13895, đa ảnh 6514) | single_train / single_test / multi_train / multi_test | 27156 | 6745 | 20411 | 19.54 | 6755/6756 (lỗi 0) | tai |
| B | minhquan6203/ViTextVQA |  | không khai báo |  |  |  |  |  | 0.0 | - (lỗi 0) | khong_tai_duoc |
| B | Ouyangxuelili/vlsp2023-vqa-dataset | truy cập được | không khai báo | 34378 Q/A (train 30833 / dev 3545) | train / dev (không có test) | 9129 | 9072 | 57 | 1.36 | 9132/9133 (lỗi 0) | tai |
| B | uitnlp/OpenViVQA-dataset | truy cập được | mit | 48413 Q/A theo tệp vlsp2023_* (train 30833 / dev 3545 / test 14035) | train 9129 / validation 1070 / test 1000 ảnh | 11200 | 11115 | 85 | 1.67 | 8/9 (lỗi 0) | tai |
| B | 5CD-AI/Viet-Table-Markdown | truy cập được | không khai báo | 64902 dòng (ảnh bảng + markdown + hội thoại); số Q/A chưa đếm | chỉ train (không có test) | 64901 | 64901 | 0 | 16.1 | 104/105 (lỗi 0) | tai |

Bộ không tải được và lý do:

- **5CD-AI/Viet-Doc-VQA-flash2**: bị khóa (gated=manual): cần đăng nhập Hugging Face và được chủ bộ dữ liệu duyệt; không có token nên không truy cập, không tải được
- **5CD-AI/Viet-Doc-VQA-II-flash2**: bị khóa (gated=manual): cần đăng nhập Hugging Face và được chủ bộ dữ liệu duyệt; không có token nên không truy cập, không tải được
- **5CD-AI/Viet-Doc-VQA-verIII**: bị khóa (gated=manual): cần đăng nhập Hugging Face và được chủ bộ dữ liệu duyệt; không có token nên không truy cập, không tải được. Yêu cầu gốc: chỉ tải nếu xác minh nguồn và giá trị bổ sung, chưa xác minh được.
- **5CD-AI/Viet-OCR-VQA-flash2**: bị khóa (gated=manual): cần đăng nhập Hugging Face và được chủ bộ dữ liệu duyệt; không có token nên không truy cập, không tải được
- **5CD-AI/Viet-Handwriting-OCR-v2**: bị khóa (gated=manual): cần đăng nhập Hugging Face và được chủ bộ dữ liệu duyệt; không có token nên không truy cập, không tải được (khai báo CC BY-NC-ND 4.0: cấm tạo tác phẩm phái sinh, cần cân nhắc nếu dùng để huấn luyện).
- **minhquan6203/ViTextVQA**: Kho chính thức tìm được (liên kết bài báo arXiv 2404.10652, CC BY-NC 3.0) nhưng gated=auto: cần đăng nhập và đồng ý điều khoản; không có token. Các bản sao khác (nhonhoccode, xuandin, 5CD-AI/Viet-ViTextVQA-gemini-VQA) chưa xác minh nên không đưa vào danh sách tải.

Ứng viên tìm thêm, chưa xác minh nên **không** tải:

- `Zenng2812/vqa-vietnamese-charts`: VQA biểu đồ tiếng Việt, 0,24 GB, không card, chưa xác minh nguồn
- `LuminarAI/vietnamese-ms-hs-textbook-math-300K`: văn bản toán THCS/THPT, chưa xác minh
- `5CD-AI/Viet-ViTextVQA-gemini-VQA`: bản chú thích lại ViTextVQA bằng Gemini, chưa xác minh
- `nhonhoccode/ViTextVQA`: bản sao không chính thức, chưa xác minh
- `xuandin/ViTextVQA`: bản sao không chính thức, chưa xác minh

## 2. Phân mục: học tập, cuộc sống, hỗn hợp


Các thư mục bộ dữ liệu nằm thật trong `data/external/1_hoc_tap/`, `2_cuoc_song/`, `3_hon_hop/` (khai báo ở `hf.GROUPS`). `_index/`, `_reports/`, `_sft/` ở cấp trên.
Số mẫu là số dòng/ảnh trong lớp phủ train/val/test (`splits_overlay.csv`), gồm cả mẫu bị loại (`excluded`). Phân loại dựa trên nội dung đã xem, xem cột nội dung.

### Mục HỌC TẬP (`1_hoc_tap/`)

| Bộ dữ liệu | Thư mục | Số mẫu | train | val | test | bị loại | Dung lượng (GB) | Nội dung |
|---|---|---|---|---|---|---|---|---|
| bbdontcry/ViSGKCap | `ViSGKCap/` | 1229 | 976 | 123 | 125 | 5 | 1.3 | Trang sách giáo khoa Cánh Diều lớp 1-3 (Toán, Tiếng Việt, Tự nhiên và Xã hội, Đạo đức). |
| D-Truong/ViEduVQA | `D-Truong__ViEduVQA/` | 18838 | 16985 | 999 | 854 | 0 | 6.8 | Hỏi đáp trên tranh minh họa tiểu học; đã xác nhận có trang SGK Cánh Diều (trùng ViSGKCap). Nội dung tranh là cảnh đời thường vẽ trong SGK. |
| **Tổng** | | **20067** | 17961 | 1122 | 979 | 5 | | |

### Mục CUỘC SỐNG (`2_cuoc_song/`)

| Bộ dữ liệu | Thư mục | Số mẫu | train | val | test | bị loại | Dung lượng (GB) | Nội dung |
|---|---|---|---|---|---|---|---|---|
| uitnlp/OpenViVQA-dataset | `uitnlp__OpenViVQA-dataset/` | 11200 | 9045 | 1068 | 1000 | 87 | 1.7 | Ảnh đời thường ở Việt Nam (phố, quán, nhà, ghe), hỏi đáp mở. |
| Ouyangxuelili/vlsp2023-vqa-dataset | `Ouyangxuelili__vlsp2023-vqa-dataset/` | 9129 | 0 | 0 | 0 | 9129 | 1.4 | Bản sao một phần của OpenViVQA (cảnh đời thường); đã bị loại khỏi vai trò huấn luyện vì trùng. |
| huyhuy123/ViOCRVQA | `huyhuy123__ViOCRVQA/` | 28251 | 19394 | 4195 | 4238 | 424 | 6.5 | Ảnh bìa sách (không phải SGK): hỏi tên sách, tác giả, nhà xuất bản, thể loại. |
| 5CD-AI/Viet-Table-Markdown | `5CD-AI__Viet-Table-Markdown/` | 64901 | 58324 | 3329 | 3247 | 1 | 16.1 | Ảnh bảng/biểu mẫu trong báo cáo, tin tức, hành chính; từ khóa học đường chỉ ~5% (mẫu 400). |
| **Tổng** | | **113481** | 86763 | 8592 | 8485 | 9641 | | |

### Mục HỖN HỢP (`3_hon_hop/`)

| Bộ dữ liệu | Thư mục | Số mẫu | train | val | test | bị loại | Dung lượng (GB) | Nội dung |
|---|---|---|---|---|---|---|---|---|
| VLAI-AIVN/ViInfographicVQA | `VLAI-AIVN__ViInfographicVQA/` | 27156 | 23905 | 0 | 2661 | 590 | 19.5 | Infographic tin tức, 9 chủ đề; chỉ 'Giáo dục - Khoa Học' liên quan học tập, 8 chủ đề còn lại (kinh tế, y tế, văn hóa, thiên tai, thể thao, thời tiết, quốc phòng, nhân vật) là đời sống. Không tách vật lý được. |
| **Tổng** | | **27156** | 23905 | 0 | 2661 | 590 | | |

#### Bên trong ViInfographicVQA (chia theo chủ đề, ánh xạ từng mẫu ở `_reports/phan_loai_infographic.csv`)

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

### Lưu ý

- Phân loại theo nội dung, không theo giấy phép. ViEduVQA CC BY-NC; các bộ khác phần lớn không khai báo giấy phép; ảnh SGK có bản quyền, chỉ dùng nghiên cứu nội bộ.
- ViEduVQA xếp HỌC TẬP vì có trang SGK; hình bên trong là cảnh đời thường vẽ cho trẻ em. Tỉ lệ ảnh thuộc SGK trong bộ chưa đo hết.
- Khoảng trống: chưa có SGK lớp 4-5, chưa có biểu đồ/bản đồ SGK thật; mục HỌC TẬP hiện chủ yếu là lớp 1-3.

## 3. Trùng lặp

- exact: SHA-256 ảnh giống hệt; near: pHash cách nhau tối đa 4 bit (resize, nén lại, quét lại); content: pHash 5 đến 10 bit hoặc cùng nội dung chữ; annotation: cùng văn bản chú thích/câu hỏi sau chuẩn hóa (>= 25 ký tự) nhưng ảnh khác.
- Hạn chế: pHash không bền với ảnh bị cắt mạnh; không có OCR (chưa cài engine), nên trùng nội dung chữ chỉ dò qua văn bản chú thích đi kèm; bộ bị khóa không so sánh được.

### 3.1. So với ViSGKCap và trong nội bộ từng bộ (quét toàn bộ)

`content` (pHash 5-10 bit) là ỨNG VIÊN: ngưỡng lỏng, ảnh thưa thớt hay bị báo nhầm. Đã kiểm lại bằng NCC (tương quan chuẩn hóa) trên toàn bộ ~1.700 cặp: 9 trùng thật (cùng tranh, khác khung cắt; pHash ≤ 4 bit bỏ sót loại này), 37 cần xem tay, còn lại bác bỏ; 9 cặp đã nối vào lớp phủ. Đã xác nhận bằng mắt: ViEduVQA `near` (cùng trang SGK, khác kích thước).

| Bộ dữ liệu | Mức | So với | Số bản ghi |
|---|---|---|---|
| 5CD-AI/Viet-Table-Markdown | content | ViSGKCap | 1483 |
| 5CD-AI/Viet-Table-Markdown | near | nội bộ | 3 |
| D-Truong/ViEduVQA | content | ViSGKCap | 73 |
| D-Truong/ViEduVQA | exact | nội bộ | 14923 |
| D-Truong/ViEduVQA | near | ViSGKCap | 15 |
| Ouyangxuelili/vlsp2023-vqa-dataset | content | ViSGKCap | 3 |
| Ouyangxuelili/vlsp2023-vqa-dataset | exact | nội bộ | 57 |
| Ouyangxuelili/vlsp2023-vqa-dataset | near | ViSGKCap | 1 |
| Ouyangxuelili/vlsp2023-vqa-dataset | near | nội bộ | 87 |
| VLAI-AIVN/ViInfographicVQA | content | ViSGKCap | 72 |
| VLAI-AIVN/ViInfographicVQA | exact | nội bộ | 16479 |
| VLAI-AIVN/ViInfographicVQA | near | nội bộ | 1111 |
| bbdontcry/ViSGKCap | exact | nội bộ | 2 |
| bbdontcry/ViSGKCap | near | nội bộ | 4 |
| huyhuy123/ViOCRVQA | content | ViSGKCap | 250 |
| huyhuy123/ViOCRVQA | exact | nội bộ | 150 |
| huyhuy123/ViOCRVQA | near | nội bộ | 148 |
| uitnlp/OpenViVQA-dataset | content | ViSGKCap | 8 |
| uitnlp/OpenViVQA-dataset | exact | nội bộ | 85 |
| uitnlp/OpenViVQA-dataset | near | ViSGKCap | 1 |
| uitnlp/OpenViVQA-dataset | near | nội bộ | 127 |

### 3.2. So sánh chéo giữa các bộ (ảnh duy nhất; exact = SHA-256 giống hệt, near = pHash <= 4)

| Bộ A | Bộ B | Mức | Số cặp |
|---|---|---|---|
| 5CD-AI/Viet-Table-Markdown | huyhuy123/ViOCRVQA | near | 2 |
| D-Truong/ViEduVQA | bbdontcry/ViSGKCap | near | 3 |
| Ouyangxuelili/vlsp2023-vqa-dataset | VLAI-AIVN/ViInfographicVQA | near | 1 |
| Ouyangxuelili/vlsp2023-vqa-dataset | bbdontcry/ViSGKCap | near | 1 |
| Ouyangxuelili/vlsp2023-vqa-dataset | uitnlp/OpenViVQA-dataset | exact | 9072 |
| VLAI-AIVN/ViInfographicVQA | uitnlp/OpenViVQA-dataset | near | 1 |
| bbdontcry/ViSGKCap | uitnlp/OpenViVQA-dataset | near | 1 |

### 3.3. Rủi ro rò rỉ giữa split (chỉ báo cáo, không xóa)

- **OpenViVQA, ảnh trùng giữa các split gốc:** exact cùng split: 57; exact dev / test: 1; exact dev / train: 8; exact test / train: 19; near cùng split: 87; near dev / train: 22; near test / train: 18. Nên loại các ảnh trùng chéo split khi dùng test gốc để đánh giá.
- **5CD-AI/Viet-Table-Markdown** so với ViSGKCap, mức `content`: 269 trang ViSGKCap, theo split của ViSGKCap {'train': 210, 'validation': 31, 'test': 28} (ứng viên chưa xác nhận)
- **D-Truong/ViEduVQA** so với ViSGKCap, mức `near`: 3 trang ViSGKCap, theo split của ViSGKCap {'train': 3} (đã xác nhận bằng mắt)
- **D-Truong/ViEduVQA** so với ViSGKCap, mức `content`: 15 trang ViSGKCap, theo split của ViSGKCap {'validation': 3, 'train': 12} (ứng viên chưa xác nhận)
- **Ouyangxuelili/vlsp2023-vqa-dataset** so với ViSGKCap, mức `near`: 1 trang ViSGKCap, theo split của ViSGKCap {'train': 1}
- **Ouyangxuelili/vlsp2023-vqa-dataset** so với ViSGKCap, mức `content`: 3 trang ViSGKCap, theo split của ViSGKCap {'train': 3} (ứng viên chưa xác nhận)
- **VLAI-AIVN/ViInfographicVQA** so với ViSGKCap, mức `content`: 15 trang ViSGKCap, theo split của ViSGKCap {'train': 12, 'test': 1, 'validation': 2} (ứng viên chưa xác nhận)
- **huyhuy123/ViOCRVQA** so với ViSGKCap, mức `content`: 172 trang ViSGKCap, theo split của ViSGKCap {'train': 137, 'validation': 20, 'test': 15} (ứng viên chưa xác nhận)
- **uitnlp/OpenViVQA-dataset** so với ViSGKCap, mức `near`: 1 trang ViSGKCap, theo split của ViSGKCap {'train': 1}
- **uitnlp/OpenViVQA-dataset** so với ViSGKCap, mức `content`: 8 trang ViSGKCap, theo split của ViSGKCap {'train': 6, 'test': 1, 'validation': 1} (ứng viên chưa xác nhận)

## 4. Lớp phủ train/val/test (overlay)


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

## 5. Kết luận và khuyến nghị

- **Không trộn train/test giữa nguồn:** loại khỏi huấn luyện mọi ảnh trùng hoặc gần trùng với test/validation của ViSGKCap và với benchmark dev/test của nhóm; tạo danh sách loại trừ riêng, không sửa dữ liệu gốc.
- **vlsp2023-vqa là tập con của OpenViVQA** (chú thích và ảnh trùng chính xác): chỉ giữ OpenViVQA để tránh đếm hai lần.
- **ViEduVQA** có trang SGK Cánh Diều; bộ có nhiều Q/A cho mỗi ảnh (3.915 ảnh cho 18.838 Q/A) nên chia theo ảnh, không theo dòng.
- **Khoảng trống chưa được phủ:** lớp 4-5 và biểu đồ/bản đồ SGK thật vẫn thiếu (ViSGKCap chỉ lớp 1-3; ViInfographicVQA là infographic báo chí, không phải SGK).
- Chú thích do AI sinh chưa phải ground truth; giấy phép của bộ dữ liệu không mặc nhiên áp dụng cho ảnh SGK gốc; dữ liệu chỉ dùng nghiên cứu nội bộ.
- Giới hạn: không OCR; pHash không bền với ảnh cắt mạnh; mức `content` chỉ là ứng viên; với ViInfographicVQA, quét so với ViSGKCap ở mức `content` chỉ gồm ảnh trong parquet (6.747 ảnh jpg bổ sung chỉ được so ở mức exact/near qua so sánh chéo).


## 6. Ghi chú nguồn gốc theo từng bộ

- **bbdontcry/ViSGKCap**: 1229 trang SGK Cánh Diều lớp 1-3; chú thích do máy sinh (chưa kiểm chứng); không khai báo giấy phép.
- **D-Truong/ViEduVQA**: Không có dataset card: nguồn ảnh và cách sinh Q/A chưa xác minh. ĐÃ XÁC NHẬN bằng mắt: có chứa trang SGK Cánh Diều (vd Tự nhiên và Xã hội 2, tr.53) trùng với ViSGKCap ở độ phân giải khác (799x1070 so với 558x783); nhiều Q/A cho mỗi ảnh (18.838 Q/A, 3.915 ảnh duy nhất).
- **5CD-AI/Viet-Doc-VQA-flash2**: Cùng họ 5CD-AI/Viet-Doc-VQA; hậu tố flash2 gợi ý chú thích sinh bằng Gemini Flash 2 (suy ra từ tên, chưa xác minh vì thẻ bị khóa).
- **5CD-AI/Viet-Doc-VQA-II-flash2**: Họ Viet-Doc-VQA-II; 64.516 mẫu: quan hệ với flash2 (51.672 mẫu) và verIII (205.346 mẫu) chưa xác minh được do bị khóa.
- **5CD-AI/Viet-Doc-VQA-verIII**: 205.346 mẫu, 28 GB: có thể là tập lớn hơn bao gồm các bản kia (chưa xác minh).
- **5CD-AI/Viet-OCR-VQA-flash2**: Họ Viet-OCR-VQA; 136.654 mẫu.
- **5CD-AI/Viet-Handwriting-OCR-v2**: Tùy chọn theo yêu cầu.
- **huyhuy123/ViOCRVQA**: Bài báo ViOCRVQA (ảnh bìa sách có chữ kèm Q/A). Nhãn Q/A nằm trong zip: data/train.json, dev.json, test.json (split gốc).
- **VLAI-AIVN/ViInfographicVQA**: Không khai báo giấy phép; mục 'source' trong card.
- **minhquan6203/ViTextVQA**: ViTextVQA: VQA đọc chữ trong ảnh cảnh.
- **Ouyangxuelili/vlsp2023-vqa-dataset**: Không phải kho chính thức của cuộc thi (do cá nhân duy trì). TỆP CHÚ THÍCH vlsp2023_train_data.json và vlsp2023_dev_data.json có SHA-256 GIỐNG HỆT hai tệp cùng tên trong uitnlp/OpenViVQA-dataset: đây là bản sao một phần (train+dev) của OpenViVQA, không phải dữ liệu mới.
- **uitnlp/OpenViVQA-dataset**: Kho của nhóm UIT-NLP; ảnh đời thường, VQA mở tiếng Việt.
- **5CD-AI/Viet-Table-Markdown**: Không có card và không khai báo giấy phép: nguồn ảnh chưa xác minh.

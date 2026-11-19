# Tổng quan các bộ dữ liệu tiếng Việt cho VLM (khảo sát 18/11/2026)

Nguyên tắc: không giả định giấy phép của bộ dữ liệu áp dụng cho ảnh SGK gốc; chú thích do AI sinh không phải ground truth đã kiểm chứng; không trộn train/test giữa các nguồn; không xóa dữ liệu trùng khỏi bản gốc.

## Thống kê theo bộ

Ảnh gốc = số bản ghi ảnh; ảnh duy nhất = theo SHA-256; ảnh trùng = ảnh gốc trừ ảnh duy nhất (với bộ nhiều Q/A mỗi ảnh, phần lớn là CÙNG ẢNH hỏi nhiều lần, không phải rác).

| Nhóm | Bộ dữ liệu | Truy cập | Giấy phép khai báo | Q/A hoặc chú thích | Split gốc | Ảnh gốc | Ảnh duy nhất | Ảnh trùng | Dung lượng thực (GB) | Quyết định |
|---|---|---|---|---|---|---|---|---|---|---|
| A | bbdontcry/ViSGKCap | truy cập được | không khai báo | 1229 chú thích (không có Q/A) | train 981 / validation 123 / test 125 | 1229 | 1227 | 2 | 1.31 | da_crawl_truoc |
| A | D-Truong/ViEduVQA | truy cập được | cc-by-nc-4.0 | 18838 Q/A | chỉ train (không có test) | 18838 | 3915 | 14923 | 6.76 | tai |
| A | 5CD-AI/Viet-Doc-VQA-flash2 | bị khóa (gated=manual) | không khai báo |  |  |  |  |  | 0.0 | khong_tai_duoc |
| A | 5CD-AI/Viet-Doc-VQA-II-flash2 | bị khóa (gated=manual) | không khai báo |  |  |  |  |  | 0.0 | khong_tai_duoc |
| A | 5CD-AI/Viet-Doc-VQA-verIII | bị khóa (gated=manual) | không khai báo |  |  |  |  |  | 0.0 | khong_tai_duoc |
| B | 5CD-AI/Viet-OCR-VQA-flash2 | bị khóa (gated=manual) | không khai báo |  |  |  |  |  | 0.0 | khong_tai_duoc |
| B | 5CD-AI/Viet-Handwriting-OCR-v2 | bị khóa (gated=manual) | cc-by-nc-nd-4.0 |  |  |  |  |  | 0.0 | khong_tai_duoc |
| B | huyhuy123/ViOCRVQA | truy cập được | không khai báo | 123780 Q/A (train 86592 / dev 18587 / test 18601) | train / dev / test trong data/*.json của zip | 28251 | 28101 | 150 | 6.5 | tai |
| B | VLAI-AIVN/ViInfographicVQA | truy cập được | không khai báo | 20409 Q/A (đơn ảnh 13895, đa ảnh 6514) | single_train / single_test / multi_train / multi_test | 27156 | 6745 | 20411 | 19.54 | tai |
| B | minhquan6203/ViTextVQA |  | không khai báo |  |  |  |  |  | 0.0 | khong_tai_duoc |
| B | Ouyangxuelili/vlsp2023-vqa-dataset | truy cập được | không khai báo | 34378 Q/A (train 30833 / dev 3545) | train / dev (không có test) | 9129 | 9072 | 57 | 1.36 | tai |
| B | uitnlp/OpenViVQA-dataset | truy cập được | mit | 48413 Q/A theo tệp vlsp2023_* (train 30833 / dev 3545 / test 14035) | train 9129 / validation 1070 / test 1000 ảnh | 11200 | 11115 | 85 | 1.67 | tai |
| B | 5CD-AI/Viet-Table-Markdown | truy cập được | không khai báo | 64902 dòng (ảnh bảng + markdown + hội thoại); số Q/A chưa đếm | chỉ train (không có test) | 64901 | 64901 | 0 | 16.1 | tai |

## Mức trùng lặp (so với ViSGKCap và trong nội bộ từng bộ)

- exact: SHA-256 ảnh giống hệt; near: pHash cách nhau tối đa 4 bit (resize, nén lại, quét lại); content: pHash 5 đến 10 bit hoặc cùng nội dung chữ; annotation: cùng văn bản chú thích/câu hỏi sau chuẩn hóa (>= 25 ký tự) nhưng ảnh khác.
- Hạn chế: pHash không bền với ảnh bị cắt mạnh; không có OCR (chưa cài engine), nên trùng nội dung chữ chỉ dò qua văn bản chú thích đi kèm; bộ bị khóa không so sánh được.

### So với ViSGKCap và trong nội bộ từng bộ (quét toàn bộ)

`content` (pHash 5-10 bit) là ỨNG VIÊN chưa xác nhận: ngưỡng lỏng, ảnh thưa thớt hay bị báo nhầm. Đã xác nhận bằng mắt: ViEduVQA `near` (cùng trang SGK, khác kích thước).

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

### So sánh chéo giữa các bộ (ảnh duy nhất; exact = SHA-256 giống hệt, near = pHash <= 4)

| Bộ A | Bộ B | Mức | Số cặp |
|---|---|---|---|
| 5CD-AI/Viet-Table-Markdown | huyhuy123/ViOCRVQA | near | 2 |
| D-Truong/ViEduVQA | bbdontcry/ViSGKCap | near | 3 |
| Ouyangxuelili/vlsp2023-vqa-dataset | VLAI-AIVN/ViInfographicVQA | near | 1 |
| Ouyangxuelili/vlsp2023-vqa-dataset | bbdontcry/ViSGKCap | near | 1 |
| Ouyangxuelili/vlsp2023-vqa-dataset | uitnlp/OpenViVQA-dataset | exact | 9072 |
| VLAI-AIVN/ViInfographicVQA | uitnlp/OpenViVQA-dataset | near | 1 |
| bbdontcry/ViSGKCap | uitnlp/OpenViVQA-dataset | near | 1 |

## Rủi ro rò rỉ giữa split (chỉ báo cáo, không xóa)

- **OpenViVQA, ảnh trùng giữa các split gốc:** exact cùng split: 57; exact dev / test: 1; exact dev / train: 8; exact test / train: 19; near cùng split: 87; near dev / train: 22; near test / train: 18. Nên loại các ảnh trùng chéo split khi dùng test gốc để đánh giá.
- **5CD-AI/Viet-Table-Markdown** so với ViSGKCap, mức `content`: 269 trang ViSGKCap, theo split của ViSGKCap {'train': 210, 'validation': 31, 'test': 28} (ứng viên chưa xác nhận)
- **D-Truong/ViEduVQA** so với ViSGKCap, mức `near`: 3 trang ViSGKCap, theo split của ViSGKCap {'train': 3} (đã xác nhận bằng mắt)
- **D-Truong/ViEduVQA** so với ViSGKCap, mức `content`: 15 trang ViSGKCap, theo split của ViSGKCap {'train': 12, 'validation': 3} (ứng viên chưa xác nhận)
- **Ouyangxuelili/vlsp2023-vqa-dataset** so với ViSGKCap, mức `near`: 1 trang ViSGKCap, theo split của ViSGKCap {'train': 1}
- **Ouyangxuelili/vlsp2023-vqa-dataset** so với ViSGKCap, mức `content`: 3 trang ViSGKCap, theo split của ViSGKCap {'train': 3} (ứng viên chưa xác nhận)
- **VLAI-AIVN/ViInfographicVQA** so với ViSGKCap, mức `content`: 15 trang ViSGKCap, theo split của ViSGKCap {'train': 12, 'validation': 2, 'test': 1} (ứng viên chưa xác nhận)
- **huyhuy123/ViOCRVQA** so với ViSGKCap, mức `content`: 172 trang ViSGKCap, theo split của ViSGKCap {'train': 137, 'validation': 20, 'test': 15} (ứng viên chưa xác nhận)
- **uitnlp/OpenViVQA-dataset** so với ViSGKCap, mức `near`: 1 trang ViSGKCap, theo split của ViSGKCap {'train': 1}
- **uitnlp/OpenViVQA-dataset** so với ViSGKCap, mức `content`: 8 trang ViSGKCap, theo split của ViSGKCap {'train': 6, 'validation': 1, 'test': 1} (ứng viên chưa xác nhận)

## Kết luận và khuyến nghị

- **Không trộn train/test giữa nguồn:** loại khỏi huấn luyện mọi ảnh trùng hoặc gần trùng với test/validation của ViSGKCap và với benchmark dev/test của nhóm; tạo danh sách loại trừ riêng, không sửa dữ liệu gốc.
- **vlsp2023-vqa là tập con của OpenViVQA** (chú thích và ảnh trùng chính xác): chỉ giữ OpenViVQA để tránh đếm hai lần.
- **ViEduVQA** có trang SGK Cánh Diều; bộ có nhiều Q/A cho mỗi ảnh (3.915 ảnh cho 18.838 Q/A) nên chia theo ảnh, không theo dòng.
- **Khoảng trống chưa được phủ:** lớp 4-5 và biểu đồ/bản đồ SGK thật vẫn thiếu (ViSGKCap chỉ lớp 1-3; ViInfographicVQA là infographic báo chí, không phải SGK).
- Chú thích do AI sinh chưa phải ground truth; giấy phép của bộ dữ liệu không mặc nhiên áp dụng cho ảnh SGK gốc; dữ liệu chỉ dùng nghiên cứu nội bộ.
- Giới hạn: không OCR; pHash không bền với ảnh cắt mạnh; mức `content` chỉ là ứng viên; với ViInfographicVQA, quét so với ViSGKCap ở mức `content` chỉ gồm ảnh trong parquet (6.747 ảnh jpg bổ sung chỉ được so ở mức exact/near qua so sánh chéo).


## Lớp phủ train/val/test (overlay)

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

## Ghi chú nguồn gốc theo từng bộ

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

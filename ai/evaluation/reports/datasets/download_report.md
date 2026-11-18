# Báo cáo tải dữ liệu

Mọi dữ liệu nằm ở `data/external/` (không có trong repo). Tải có resume, kiểm tra SHA-256 (tệp LFS), không ghi đè.

| Bộ dữ liệu | Quyết định | Dung lượng khai báo (GB) | Đã có trên đĩa (GB) | Tệp OK / tổng | Lỗi |
|---|---|---|---|---|---|
| bbdontcry/ViSGKCap | da_crawl_truoc | 1.31 | 1.31 | 5/5 (tải trước đó) (tải mới 0) | 0 |
| D-Truong/ViEduVQA | tai | 6.76 | 6.76 | 14/15 (tải mới 14) | 0 |
| 5CD-AI/Viet-Doc-VQA-flash2 | khong_tai_duoc | 4.82 | 0.0 | - (tải mới 0) | 0 |
| 5CD-AI/Viet-Doc-VQA-II-flash2 | khong_tai_duoc | 9.16 | 0.0 | - (tải mới 0) | 0 |
| 5CD-AI/Viet-Doc-VQA-verIII | khong_tai_duoc | 28.1 | 0.0 | - (tải mới 0) | 0 |
| 5CD-AI/Viet-OCR-VQA-flash2 | khong_tai_duoc | 14.7 | 0.0 | - (tải mới 0) | 0 |
| 5CD-AI/Viet-Handwriting-OCR-v2 | khong_tai_duoc | 1.27 | 0.0 | - (tải mới 0) | 0 |
| huyhuy123/ViOCRVQA | tai | 6.5 | 6.5 | 3/4 (tải mới 3) | 0 |
| VLAI-AIVN/ViInfographicVQA | tai | 19.53 | 19.54 | 6755/6756 (tải mới 6755) | 0 |
| minhquan6203/ViTextVQA | khong_tai_duoc | 0.0 | 0.0 | - (tải mới 0) | 0 |
| Ouyangxuelili/vlsp2023-vqa-dataset | tai | 1.35 | 1.36 | 9132/9133 (tải mới 9132) | 0 |
| uitnlp/OpenViVQA-dataset | tai | 1.67 | 1.67 | 8/9 (tải mới 8) | 0 |
| 5CD-AI/Viet-Table-Markdown | tai | 16.1 | 16.1 | 104/105 (tải mới 104) | 0 |

## Bộ không tải được và lý do

- **5CD-AI/Viet-Doc-VQA-flash2**: bị khóa (gated=manual): cần đăng nhập Hugging Face và được chủ bộ dữ liệu duyệt; không có token nên không truy cập, không tải được
- **5CD-AI/Viet-Doc-VQA-II-flash2**: bị khóa (gated=manual): cần đăng nhập Hugging Face và được chủ bộ dữ liệu duyệt; không có token nên không truy cập, không tải được
- **5CD-AI/Viet-Doc-VQA-verIII**: bị khóa (gated=manual): cần đăng nhập Hugging Face và được chủ bộ dữ liệu duyệt; không có token nên không truy cập, không tải được. Yêu cầu gốc: chỉ tải nếu xác minh nguồn và giá trị bổ sung, chưa xác minh được.
- **5CD-AI/Viet-OCR-VQA-flash2**: bị khóa (gated=manual): cần đăng nhập Hugging Face và được chủ bộ dữ liệu duyệt; không có token nên không truy cập, không tải được
- **5CD-AI/Viet-Handwriting-OCR-v2**: bị khóa (gated=manual): cần đăng nhập Hugging Face và được chủ bộ dữ liệu duyệt; không có token nên không truy cập, không tải được (khai báo CC BY-NC-ND 4.0: cấm tạo tác phẩm phái sinh, cần cân nhắc nếu dùng để huấn luyện).
- **minhquan6203/ViTextVQA**: Kho chính thức tìm được (liên kết bài báo arXiv 2404.10652, CC BY-NC 3.0) nhưng gated=auto: cần đăng nhập và đồng ý điều khoản; không có token. Các bản sao khác (nhonhoccode, xuandin, 5CD-AI/Viet-ViTextVQA-gemini-VQA) chưa xác minh nên không đưa vào danh sách tải.

## Ứng viên tìm thêm, chưa xác minh nên KHÔNG tải

- `Zenng2812/vqa-vietnamese-charts`: VQA biểu đồ tiếng Việt, 0,24 GB, không card, chưa xác minh nguồn
- `LuminarAI/vietnamese-ms-hs-textbook-math-300K`: văn bản toán THCS/THPT, chưa xác minh
- `5CD-AI/Viet-ViTextVQA-gemini-VQA`: bản chú thích lại ViTextVQA bằng Gemini, chưa xác minh
- `nhonhoccode/ViTextVQA`: bản sao không chính thức, chưa xác minh
- `xuandin/ViTextVQA`: bản sao không chính thức, chưa xác minh

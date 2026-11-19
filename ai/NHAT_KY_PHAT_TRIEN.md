# Nhật ký phát triển phần AI (Mảng A)

Mỗi ngày một mục: việc làm, số đo chính (kèm điều kiện), kết luận, việc còn lại. Chi tiết và bảng số liệu nằm ở `evaluation/reports/` (chỉ liên kết, không chép lại).
Mọi số đo là thăm dò, chỉ số từ khóa thô; tập test chưa chạy.

## 2026-11-17

- **Làm:** benchmark v0.2.0 (47 ảnh tổng hợp, 8 loại hình, dev 24 / test 23, ground truth theo mệnh đề); hợp đồng đầu ra v0.1 (nháp); module `describe_image`; phương pháp B0, B0e (đối chứng), B1 (hai bước);
  nhà cung cấp OpenRouter / Google / LM Studio; công cụ nạp SGK; bộ sinh tập huấn luyện tổng hợp; dữ liệu chỉ giữ ở máy (repo công khai).
- **Số đo** ([so sánh phương pháp và model](evaluation/reports/so_sanh_phuong_phap_va_model_dev_20261117.md)): nemotron B0 70% / B0e 75% / B1 82%; `qwen3-vl-4b` cục bộ B0e 123/141, ngang `gemini-3.1-flash-lite`, hơn nemotron (106); B1 không giúp 4B (92/141, lan truyền lỗi).
- **Kết luận:** `qwen3-vl-4b` là ứng viên baseline (cục bộ, miễn phí, ~6 s mỗi ảnh); chưa kết luận B1 hơn B0.

## 2026-11-18

- **Khảo sát model** ([báo cáo](evaluation/reports/survey_qwen3vl_q4_20261117.md)): 4B Q4 phủ 83,3% / 86,2% / 87,2% ở x0,5 / x1 / x1,5 (chênh x1–x1,5 trong dao động), bản đồ chỉ 16,7%. **8B Q4 loại**: không nạp đủ lên GPU 8 GB (30–34/36 lớp), 20–230 s mỗi mô tả, chưa thấy hơn 4B. Giữ 4B Q4, parallel 1, ctx 16384.
- **Mô-đun hệ thống** ([báo cáo](evaluation/reports/system_modules_4b_20261118.md)): cổng ảnh `capture/quality.py` (tối 33/33, mờ 21/21, 0/1045 báo nhầm trên ảnh tổng hợp); prompt `b0g_v1` báo đúng 4/4 ảnh mờ (trước 0/4);
  hỏi đáp `vlm/ask.py` tăng 68% → 90% (dev) nhờ để mã tính toán (`vlm/calc.py`, tính toán 8/15 → 15/15); bộ lọc ký tự ngoài tiếng Việt (`chat_vi`) chưa được kích hoạt thật; kèm lời mô tả cũ làm câu hỏi về hướng tệ hơn (4/16 so với 12–13/16). Rủi ro quá khớp dev.
- **Trang SGK thật (ViSGKCap, 32 trang test):** `b0g_v1` **báo nhầm "không đọc được" 5/32 trang sạch** (15,6%); 3/32 bị cắt cụt; ~15 s mỗi trang. Chú thích ViSGKCap chép đúng chữ nhưng có lỗi mô tả cảnh; ảnh có hình mờ `hoc10.vn` (nguồn bên thứ ba). Cần hiệu chỉnh cổng "không đọc được" trên ảnh thật.
- **Dọn nhánh:** tách `describer.py` thành `common.py`/`describer.py`/`b1.py`, đổi `openrouter_client.py` → `client.py`, đưa quy trình B0 cũ vào `evaluation/legacy_b0/`; `docs/` chỉ giữ tài liệu của phần AI (phần còn lại chuyển ra `ai-for-blinds_docs_khac/`).
- **Dữ liệu ngoài** ([báo cáo](evaluation/reports/du_lieu_ngoai_20261118.md)): khảo sát, tải và xác minh SHA-256 7 bộ Hugging Face (~47 GB, 0 lỗi) bằng `external_data/`; 6 bộ khóa tạm bỏ qua (Phúc quyết). Phát hiện: vlsp2023 là tập con của OpenViVQA (9.072 ảnh trùng); ViEduVQA chứa trang SGK của ViSGKCap (cùng tranh, khác khung cắt: pHash ≤ 4 bỏ sót, NCC bắt được); OpenViVQA rò rỉ giữa split.
  Lớp phủ train/val/test theo cụm ảnh (giữ nguyên split gốc, không sửa dữ liệu gốc); `to_sft.py` xuất 29.177 Q/A vai trò train (đáp án do máy sinh, chưa dùng được ngay để dạy hệ thống).
- **Chưa làm được:** thu thập SGK từ nền tảng sách điện tử NXBGDVN (API bị chặn; chưa rõ yêu cầu kích hoạt và điều khoản; chấp thuận của thầy mới có qua lời kể).

## 2026-11-19

- **Dữ liệu:** dọn `data/local/` (4 tệp trùng benchmark xóa, `test.png` chuyển sang `data/benchmark/_legacy/`); chuyển **thật** các bộ dữ liệu ngoài vào `data/external/1_hoc_tap/` (ViSGKCap, ViEduVQA), `2_cuoc_song/` (OpenViVQA, vlsp2023, ViOCRVQA, Viet-Table-Markdown), `3_hon_hop/` (ViInfographicVQA, 9 chủ đề; chủ đề giáo dục đánh dấu ở `_reports/phan_loai_infographic.csv`);
  số tệp và dung lượng khớp trước/sau; mã tìm thư mục qua `hf.dataset_dir()`.
- **Fine-tune:** thử dựng môi trường huấn luyện riêng nhưng Phúc dừng (LM Studio chỉ chạy suy luận, không huấn luyện được); đã gỡ hết. Còn lại trong mã: prompt `ft_describe_v1`, định dạng xuất `--format spoken` của `finetune/export_sft.py`. Hướng fine-tune chờ Phúc quyết.
- **Tài liệu:** giảm .md từ 26 xuống 13: gộp báo cáo (ba báo cáo dev → một; cổng ảnh vào báo cáo mô-đun; bốn báo cáo dữ liệu → một), bỏ báo cáo B0 tháng 10, chuyển hai ghi chú dự án cũ ra ngoài repo, gộp README `evaluation/` vào `ai/README.md`, rút gọn nhật ký, viết lại README gốc.

## Việc tiếp theo

Hiệu chỉnh cổng "không đọc được" trên trang SGK thật rồi đo lại; chấm tay (hai người) các câu hỏi đáp "sai" và 37 ca trùng cần xem tay; chọn hướng thu thập SGK lớp 4–5 và biểu đồ/bản đồ thật; quyết định hướng fine-tune; thống nhất API v1 với hợp đồng v0.1 (Phúc, Nam, Toàn).

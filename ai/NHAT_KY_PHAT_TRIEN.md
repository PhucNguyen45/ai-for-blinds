# Nhật ký phát triển phần AI (Mảng A)

Mỗi ngày làm thêm được ghi một mục: việc đã làm, số đo (kèm điều kiện), kết luận và việc còn lại. Số liệu chi tiết nằm ở
`evaluation/reports/`. Mọi số đo là thăm dò trên tập **dev** tổng hợp, chỉ số từ khóa thô; tập test chưa chạy.

## 17/11/2026

**Làm:** benchmark v0.2.0 (47 ảnh tổng hợp, 8 loại hình, dev 24 / test 23, ground truth theo mệnh đề); hợp đồng đầu ra v0.1 (nháp);
module `describe_image`; phương pháp B0, B0e (đối chứng), B1 (hai bước); chọn nhà cung cấp OpenRouter / Google / LM Studio; công cụ nạp SGK;
bộ sinh tập huấn luyện tổng hợp; chuyển dữ liệu về chỉ giữ ở máy (repo công khai).

**Số đo:** (nemotron, 22 ảnh dev) phủ mệnh đề B0 70%, B0e 75%, B1 82%; so sánh model miễn phí: qwen3-vl-4b cục bộ ngang gemini-3.1-flash-lite
(123/141), hơn nemotron (106/141); B1 không giúp 4B (92/141, lan truyền lỗi giữa hai bước). Chi tiết: `dev_b0_b0e_b1_20261117.md`, `dev_model_comparison_20261117.md`.

**Kết luận:** qwen3-vl-4b là ứng viên baseline (chạy cục bộ, miễn phí, khoảng 6 s mỗi ảnh); chưa kết luận B1 hơn B0.

## 18/11/2026

**Làm:**
- Khảo sát Qwen3-VL Q4 trên LM Studio (4B và 8B) theo độ phóng ảnh x0,5 / x1 / x1,5: `survey_qwen3vl_q4_20261117.md`.
- Cổng chất lượng ảnh `capture/quality.py`; prompt `b0g_v1` (báo ảnh không đọc được); hỏi đáp `vlm/ask.py` + `AnswerResult`; chuẩn hóa văn bản cho TTS;
  `pipeline.py` (`describe_page`, `ask_page`). Đo: `capture_gate_20261118.md`, `system_modules_4b_20261118.md`.
- Dọn nhánh: tách `describer.py`, đổi tên `client.py`, đưa quy trình B0 cũ vào `evaluation/legacy_b0/`, thêm README, ruff sạch.

**Số đo:**
- 4B Q4: phủ 83,3% / 86,2% / 87,2% ở x0,5 / x1 / x1,5 (chênh x1–x1,5 nằm trong dao động); bản đồ sơ đồ chỉ 16,7% mọi mức.
- 8B Q4: chậm 20 đến 118 s mỗi mô tả do offload GPU từng phần (30 đến 34 trên 36 lớp), chất lượng chưa thấy hơn 4B. Loại.
- Cổng ảnh: tối 33/33, mờ 21/21, 0/1045 báo nhầm (ảnh tổng hợp); chói 37%; hình bị cắt 0% (giao VLM).
- `b0g_v1`: báo đúng 4/4 ảnh mờ (trước 0/4), 0/40 báo nhầm, phủ ngang, nhanh hơn (4,5 s so với 7,6 s).
- Hỏi đáp 59 câu: 40/59 chỉ ảnh, 41/59 kèm mô tả; model cộng sai (computation 8/15, lên 13/15 khi có mô tả).

**Kết luận:** điểm cần cải thiện ở tầng hệ thống: tính toán, cách nói hướng, lọc ký tự ngoài tiếng Việt. Giữ 4B Q4, parallel 1, ctx 16384.

**Làm thêm cuối ngày (cải thiện hỏi đáp, đo trên dev):**
- Bước tính bằng mã (`vlm/calc.py`, prompt `ask_calc_v1`; chỉ nhận số, + - * / ngoặc, `sqrt`): hỏi đáp chỉ ảnh từ 40/59 lên 53/59 (89,8%); tính toán 8/15 lên 15/15.
- Bộ lọc ký tự ngoài tiếng Việt (`chat_vi`): gọi lại một lần, nếu vẫn còn thì loại ký tự; chưa được kích hoạt thật trong các lần chạy (0/162 bản ghi còn CJK).
- Gộp mã gọi model của `describe_image` vào `chat_vi`; kiểm tra hồi quy `b0g_v1`: phủ 84,0% (trước 85,5%, trong dao động), vẫn báo đúng 4/4 ảnh mờ.
- Phát hiện: kèm lời mô tả cũ làm câu hỏi về vị trí/hướng tệ hơn (4/16 so với 12–13/16 khi chỉ ảnh), nhất quán qua 3 lần chạy.
- Tăng relation 7 → 13/16 chưa quy được cho bước tính (prompt JSON đổi cả câu chữ). Rủi ro quá khớp dev. Báo cáo: `system_modules_4b_20261118.md` mục 4.

**Việc tiếp theo (đề xuất):** chấm tay các câu "sai" bằng hai người; kiểm tra cổng ảnh và `b0g_v1` trên ảnh chụp thật (SGK); thử mờ nhẹ, chói, bị cắt; quyết định có giữ khuyến nghị "hỏi vị trí chỉ bằng ảnh"; đưa API v1 và hợp đồng v0.1 về một (Phúc, Nam, Toàn).

**Kiểm tra nhánh (đề xuất dọn dẹp, chưa thực hiện):** `.git` nặng 82 MB do lịch sử cũ (slide 11,5 MB, ảnh ứng viên Wikimedia, benchmark cũ); `ruff` không còn lỗi
logic (F, E9) nhưng còn 709 dòng dài quá 88 ký tự (33 dòng quá 120), 29 `zip` thiếu `strict`; `vulture` không thấy mã chết thật; `prepare_for_speech` và
`split_for_streaming` chưa được `pipeline.py` gọi; `proposition_check.py` và `qa_score.py` trùng hàm `norm`; `docs/` công khai chứa biểu mẫu của Học viện và
phiếu đăng ký đề tài; slide `SGBEyes_Slide...pptx` nằm trong lịch sử cũ của nhánh. Chi tiết và đề xuất theo mức rủi ro: xem câu trả lời ngày 18/11.

## 18/11/2026 (tiếp): dọn `docs/`, thu thập dữ liệu SGK

- Phúc yêu cầu tạm dừng phần xử lý ảnh thật và tập trung thu thập SGK Việt Nam từ mạng; `docs/` chỉ giữ tài liệu liên quan trực tiếp đến phần AI.
- `docs/` đã dọn: chỉ còn `bao_cao/` (A01 nháp, báo cáo Mảng A, lộ trình cá nhân Mảng A, báo cáo tiến độ lần 1) và `ghi_chu_du_an/`. Các tài liệu còn lại
  (biểu mẫu/công văn của Học viện, dự án tiền thân SgBe, slide giảng viên, phiếu đăng ký, thuyết minh, lộ trình nhóm, PDF học tập cá nhân) được **chuyển ra ngoài repo**
  sang thư mục `ai-for-blinds_docs_khac/` (không xóa). Lịch sử git cũ vẫn chứa bản cũ của một số tệp.
- **Thu thập SGK từ nền tảng sách điện tử của NXB Giáo dục Việt Nam (`hanhtrangso.nxbgd.vn`):** tôi mới kiểm tra `robots.txt` (không có quy định riêng) và tệp JavaScript công khai của trang
  (thấy địa chỉ API riêng và các hàm liên quan đến mã kích hoạt sách). Khi tôi thử gọi một điểm cuối API thì hệ thống phân quyền chặn thao tác. **Chưa tải trang SGK nào.**
  Lý do cần dừng và hỏi: chưa xác nhận sách có yêu cầu kích hoạt/đăng nhập hay không, điều khoản sử dụng chưa đọc, và chấp thuận của thầy mới có qua lời kể, chưa có văn bản.
- Làm thêm được: mở rộng bộ tải ảnh Wikimedia Commons với truy vấn tiếng Việt (`--queries vi`); chỉ nhận giấy phép tự do.

**Bộ dữ liệu ngoài do Phúc tìm trên HuggingFace (đánh giá và tải về, chỉ ở máy `data/external/`, đã chặn trong `.gitignore`):**
- `bbdontcry/ViSGKCap`: **đã tải và xác minh** (5 tệp parquet, 1,3 GB, kích thước và sha256 khớp API HuggingFace). 1229 trang SGK **Cánh Diều lớp 1 đến 3** (train 981, val 123, test 125),
  10 đầu sách (Toán, Tiếng Việt, Tự nhiên và Xã hội, Đạo đức), chú thích ngắn (trung vị 29 từ) và chi tiết (272 từ) bằng tiếng Việt, **không khai báo giấy phép**, ảnh là trang SGK có bản quyền.
  Hạn chế đối với đề tài: **không có lớp 4 đến 5; gần như không có biểu đồ (0,2%) hay bản đồ (0%)**; bảng 9,9%, sơ đồ 5,2%, hình học 3,5%, phép tính 10,7%. Chú thích có vẻ do máy sinh, chưa kiểm chứng; văn phong tả bố cục, không phải văn nói.
  Giá trị: trang SGK thật, chữ in tiếng Việt thật, kích thước 558×783 đến 1700×2200. Thống kê: `evaluation/reporting/visgkcap_stats.py` (cần `uv run --with pyarrow`).
- `D-Truong/ViEduVQA` (CC BY-NC 4.0, 18.838 cặp hỏi đáp trên ảnh minh họa đời thường, 6,2 GB): **chưa tải**, ít hợp đề tài.
- `5CD-AI/Viet-Doc-VQA-flash2` (51.672 mẫu, khóa, cần xin quyền bằng tài khoản HuggingFace): chưa truy cập được.
- Thu thập từ nền tảng sách điện tử NXBGDVN: chưa thực hiện (xem mục trên), chờ quyết định của Phúc.

## 18/11/2026 (tối): khảo sát, tải và kiểm tra trùng các bộ dữ liệu tiếng Việt (yêu cầu của Phúc)

**Công cụ mới `external_data/`:** `survey.py` (khảo sát qua API công khai của Hugging Face), `download.py` (resume, SHA-256 theo Hub, không ghi đè, từ chối bộ khóa và ViSGKCap, đa luồng),
`dedup.py` (SHA-256, pHash 64 bit, băm văn bản; lập chỉ mục, thăm dò mẫu, quét toàn bộ, so sánh chéo), `report.py` (5 báo cáo). Dữ liệu ở `data/external/` (không có trong repo).

**Đã tải (đều xác minh SHA-256 với Hub, 0 lỗi):** ViSGKCap (trước đó), OpenViVQA (tải lại lần hai, giống hệt bản đầu), vlsp2023-vqa, ViEduVQA, ViOCRVQA, ViInfographicVQA (parquet + 6747 ảnh jpg bổ sung), Viet-Table-Markdown; tổng khoảng 47 GB.
**Không tải được:** `5CD-AI/Viet-Doc-VQA-flash2`, `-II-flash2`, `-verIII`, `Viet-OCR-VQA-flash2`, `Viet-Handwriting-OCR-v2` (khóa thủ công), `minhquan6203/ViTextVQA` (khóa tự động, cần đăng nhập); Phúc quyết định tạm bỏ qua.
Giữ nguyên split gốc của từng bộ, không tự chia, không xóa mẫu trùng.

**Phát hiện:**
- **ViEduVQA chứa trang SGK Cánh Diều trùng với ViSGKCap** (đối chiếu bằng mắt trang Tự nhiên và Xã hội 2 tr.53: cùng trang, 799×1070 so với 558×783); 3 trang gần trùng ở train ViSGKCap, 15 trang ứng viên ở mức nội dung (3 ở validation). 18.838 Q/A nhưng chỉ 3.915 ảnh duy nhất.
- **vlsp2023-vqa là bản sao một phần của OpenViVQA**: hai tệp chú thích train/dev có SHA-256 giống hệt tệp cùng tên trong OpenViVQA.
- **OpenViVQA rò rỉ giữa split gốc**: 19 ảnh giống hệt nằm ở cả train và test, 8 ở train và dev, 1 ở dev và test, thêm khoảng 40 cặp gần trùng chéo split.
- ViInfographicVQA: tập đa ảnh tham chiếu ảnh jpg riêng nên phải tải thêm ngoài parquet; chỉ 3.930 ảnh duy nhất trong 20.409 Q/A.
- Ngưỡng pHash 5 đến 10 bit ("nội dung") báo nhầm nhiều với ảnh thưa thớt (ViOCRVQA 250, Viet-Table-Markdown 1483 ca so với ViSGKCap); chỉ coi là ứng viên cần kiểm bằng mắt.
- Hạn chế: chưa có OCR; pHash không bền với ảnh bị cắt mạnh.
- **So sánh chéo giữa các bộ (ảnh duy nhất):** vlsp2023-vqa so với OpenViVQA: **9.072 ảnh trùng chính xác** (toàn bộ ảnh duy nhất của vlsp2023); ViEduVQA so với ViSGKCap: 3 cặp gần trùng; các cặp còn lại không có trùng chính xác và chỉ 1 đến 2 ca gần trùng.
  ViInfographicVQA sau khi bổ sung jpg: 27.156 ảnh, 6.745 ảnh duy nhất (các jpg đa ảnh phần lớn đã nằm trong parquet).
- 5 báo cáo ở `data/external/_reports/` (`dataset_inventory.csv`, `dataset_manifest.json`, `duplicate_report.csv`, `download_report.md`, `dataset_overview.md`); bản `.md` (không chứa nội dung dữ liệu) ở `ai/evaluation/reports/datasets/`.

**Lớp phủ train/val/test cho dữ liệu ngoài (overlay), theo quyết định của Phúc:** giữ nguyên dữ liệu và split gốc; thêm bảng ánh xạ vai trò theo **cụm ảnh** (SHA-256 giống hệt hoặc pHash ≤ 4 bit, xuyên mọi bộ và benchmark của nhóm).
Mã: `external_data/clusters.py` (thuần Python, 14 kiểm thử), `external_data/make_splits.py`. Kết quả (160.704 mẫu, 116.051 ảnh duy nhất, 113.229 cụm):
- Bộ chỉ có train (ViEduVQA, Viet-Table-Markdown): chia nội bộ theo cụm 5% val / 5% test (`group_split`), không so sánh được với số liệu công bố.
- Loại khỏi huấn luyện (`excluded`, vẫn giữ nguyên trong dữ liệu gốc): vlsp2023 (9.129, bản sao OpenViVQA); ViInfographicVQA 590; ViOCRVQA 421; OpenViVQA 86; ViSGKCap 3 (ảnh train trùng với ảnh val/test của chính nó hoặc bộ khác).
- Không cụm nào lẫn train với val/test (đã kiểm tra bằng hai cách độc lập); không trùng benchmark dev/test của nhóm; 0 tệp dữ liệu gốc bị sửa (kiểm bằng mốc thời gian). 7 cụm quá lớn bị tách và gắn cờ đáng ngờ.
- Chưa xử lý tự động: mức `content` (pHash 5 đến 10 bit); 2 mẫu không rõ split gốc bị loại (`origin_khong_ro`).

## 18/11/2026 (đêm khuya): kiểm nhãn ViSGKCap, kiểm tra lại các ca trùng mức "nội dung"

**Kiểm nhãn ViSGKCap (xem trực tiếp 2 trang test, chưa chạy 4B vì LM Studio chưa nạp model):**
- `Toan_3_Tap1_page_072` và `TiengViet_2_Tap1_page_063`: **chữ trên trang được chép đúng gần như tuyệt đối** (mọi câu trích dẫn, phép tính, số trang khớp ảnh). Sai sót nằm ở mô tả cảnh: gọi học sinh là "người lớn", coi một bong bóng lời nói là bong bóng suy nghĩ, coi cảnh trong bong bóng tưởng tượng là cảnh thật.
- **Mã trang lệch 1 so với số in trên trang** (`page_072` in là 71; `page_063` in là 62).
- **Nguồn ảnh:** trang có hình mờ "Đọc sách tại hoc10.vn" và "Cánh Diều": ảnh lấy từ một trang web bên thứ ba đăng lại SGK, không phải từ nhà xuất bản. Cần ghi chú khi nói về nguồn gốc và bản quyền.
- Mới xem 2 trong 125 trang test: **chưa đủ để kết luận tỉ lệ sai**.

**Kiểm lại ca trùng mức "nội dung" bằng tương quan chuẩn hóa NCC (`external_data/verify_content.py`):** hiệu chỉnh: cặp ngẫu nhiên NCC trung vị 0,12, tối đa 0,40; 3 cặp `near` ViEduVQA-ViSGKCap có NCC 0,62 đến 0,88.
- Trong 1.700 cặp ứng viên: **9 xác nhận trùng thật (NCC ≥ 0,6)**, 37 cần xem tay (0,5 đến 0,6), còn lại bác bỏ. Tức **hơn 99% ca "nội dung" là báo nhầm**, nhưng có vài ca là **cùng tranh, khác khung cắt** (đã xem bằng mắt hai cặp ViEduVQA-ViSGKCap: tr.129 "thả diều", tr.67 "cây xoài"): pHash ≤ 4 bit **bỏ sót** loại này.
- Đã nối 9 cạnh xác nhận vào gom cụm; chạy lại lớp phủ (113.229 → 113.220 cụm), bất biến vẫn đạt. 37 ca `review` chưa xử lý.

**Xuất Q/A có sẵn sang định dạng hội thoại (`external_data/to_sft.py`):** chỉ mẫu vai trò `train` của lớp phủ, hiện cho ViEduVQA (16.985 dòng) và ViInfographicVQA đơn ảnh (12.192 dòng), tổng 29.177 dòng, 5.265 ảnh duy nhất (2,5 GB, `data/external/_sft/`, cục bộ).
Kiểm tra: số dòng khớp lớp phủ; 100% vai trò `train`; 0 cụm lẫn val/test/benchmark. Mỗi dòng mang nguồn, giấy phép khai báo, `answer_source: ai_generated_unverified`.
**Chưa dùng được ngay để dạy hệ thống:** đáp án do máy sinh, dài, không theo văn nói/JSON của hệ thống; chưa xuất OpenViVQA, ViOCRVQA (cần nối chú thích từ JSON), ViInfographicVQA đa ảnh; chú thích ViSGKCap không xuất vì văn phong tả bố cục không khớp mục tiêu.
**Còn lại của kế hoạch:** chạy 4B (`b0g_v1`) trên ~30 trang ViSGKCap (cần nạp `qwen/qwen3-vl-4b` trong LM Studio); xem tay 37 ca `review`.

**Dọn `data/local/` (19/11):** 4 tệp (`chart_01`, `chart_02_no_labels` và nhãn) giống hệt bản trong `benchmark/synthetic/` theo SHA-256 nên đã xóa; `test.png` (ảnh vòng tuần hoàn nước tiếng Anh dùng làm đầu vào thử nghiệm B0 đầu tiên, không rõ nguồn, không trùng ứng viên hay benchmark) **chuyển**, không xóa, sang `data/benchmark/_legacy/test.png` và sửa đường dẫn trong `baseline_b0_notes.md`.
Hai bộ sinh cũ `generate_chart*.py` giờ ghi vào `data/benchmark/_legacy/regen` để không tạo lại `data/local/`.

**Phân loại dữ liệu ngoài thành HỌC TẬP / CUỘC SỐNG (yêu cầu của Phúc):** `external_data/categorize.py`. Không di chuyển dữ liệu: tạo liên kết mềm `data/external/1_hoc_tap/` (ViSGKCap, ViEduVQA, một phần ViInfographicVQA) và `2_cuoc_song/` (OpenViVQA, vlsp2023, ViOCRVQA, Viet-Table-Markdown, phần còn lại ViInfographicVQA);
bảng ở `ai/evaluation/reports/datasets/phan_loai_hoc_tap_cuoc_song.md` (lần làm đầu này đã được thay bằng chuyển thật, xem mục kế tiếp). ViInfographicVQA chia theo chủ đề ("Giáo dục - Khoa Học" 1.320 Q/A vào học tập).
Số mẫu: học tập 21.835 (train 19.555), cuộc sống 138.869 (train 109.074). Căn cứ: nội dung đã xem (câu hỏi, ảnh mẫu, chủ đề), không theo tên bộ.

**Sửa lại việc phân loại: chuyển THẬT thư mục (19/11/2026):** Phúc muốn chuyển các thư mục bộ dữ liệu vào hai mục; lần trước tôi hiểu sai và chỉ tạo liên kết mềm kèm `PHAN_LOAI.md`, nên `data/external/` vừa có thư mục bộ dữ liệu lẻ vừa có hai thư mục chỉ chứa liên kết.
Đã làm đúng ý: `data/external/1_hoc_tap/` (ViSGKCap, ViEduVQA), `2_cuoc_song/` (OpenViVQA, vlsp2023, ViOCRVQA, Viet-Table-Markdown), `3_hon_hop/` (ViInfographicVQA: một bộ 9 chủ đề không tách vật lý được, Phúc chọn đặt ở mục thứ ba).
- Chuyển bằng đổi tên trong cùng ổ đĩa (không sao chép). Kiểm chứng: số tệp và dung lượng của cả 7 bộ khớp bản chụp trước khi chuyển; 16.016 tệp trong `MANIFEST.json` khớp kích thước trên đĩa; 0 liên kết mềm còn lại.
- Mã tìm thư mục qua `hf.dataset_dir()` / `hf.GROUPS` (nguồn duy nhất cho việc xếp mục), nên chạy được cả bố cục cũ lẫn mới; `categorize.py` mặc định chỉ in kế hoạch, `--apply` mới chuyển.
- **Đã bỏ hai tệp thừa:** `data/external/PHAN_LOAI.md` (bản sao giống hệt từng byte của báo cáo trong repo, không ai đọc) và `_reports/phan_loai_mau.csv` (13 MB, không ai đọc); thông tin riêng của ViInfographicVQA (chủ đề từng mẫu) giữ ở `_reports/phan_loai_infographic.csv`.
- Chạy lại sau khi chuyển: `make_splits.py` cho đúng kết quả cũ (160.704 mẫu, 113.220 cụm, bất biến đạt); `report.py`, `to_sft.py`, `verify_content.py`, `download.py` đều tìm đúng thư mục mới.

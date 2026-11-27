# Nhật ký phát triển phần AI (Mảng A)

Mỗi ngày một mục: việc làm, số đo chính (kèm điều kiện), kết luận, việc còn lại. Chi tiết và bảng số liệu nằm ở `evaluation/reports/` (chỉ liên kết, không chép lại).
Mọi số đo là thăm dò, chỉ số từ khóa thô; tập test của benchmark tổng hợp chưa chạy (VMMU test chạy một lần ngày 27/11).

## 2026-11-17

- **Làm:** benchmark v0.2.0 (47 ảnh tổng hợp, 8 loại hình, dev 24 / test 23, ground truth theo mệnh đề); hợp đồng đầu ra v0.1 (nháp); module `describe_image`; phương pháp B0, B0e (đối chứng), B1 (hai bước);
  nhà cung cấp OpenRouter / Google / LM Studio; công cụ nạp SGK; bộ sinh tập huấn luyện tổng hợp; dữ liệu chỉ giữ ở máy (repo công khai).
- **Số đo** ([so sánh phương pháp và model](evaluation/reports/danh_gia_model.md)): nemotron B0 70% / B0e 75% / B1 82%; `qwen3-vl-4b` cục bộ B0e 123/141, ngang `gemini-3.1-flash-lite`, hơn nemotron (106); B1 không giúp 4B (92/141, lan truyền lỗi).
- **Kết luận:** `qwen3-vl-4b` là ứng viên baseline (cục bộ, miễn phí, ~6 s mỗi ảnh); chưa kết luận B1 hơn B0.

## 2026-11-18

- **Khảo sát model** ([báo cáo](evaluation/reports/danh_gia_model.md)): 4B Q4 phủ 83,3% / 86,2% / 87,2% ở x0,5 / x1 / x1,5 (chênh x1–x1,5 trong dao động), bản đồ chỉ 16,7%. **8B Q4 loại**: không nạp đủ lên GPU 8 GB (30–34/36 lớp), 20–230 s mỗi mô tả, chưa thấy hơn 4B. Giữ 4B Q4, parallel 1, ctx 16384.
- **Mô-đun hệ thống** ([báo cáo](evaluation/reports/danh_gia_model.md)): cổng ảnh `capture/quality.py` (tối 33/33, mờ 21/21, 0/1045 báo nhầm trên ảnh tổng hợp); prompt `b0g_v1` báo đúng 4/4 ảnh mờ (trước 0/4);
  hỏi đáp `vlm/ask.py` tăng 68% → 90% (dev) nhờ để mã tính toán (`vlm/calc.py`, tính toán 8/15 → 15/15); bộ lọc ký tự ngoài tiếng Việt (`chat_vi`) chưa được kích hoạt thật; kèm lời mô tả cũ làm câu hỏi về hướng tệ hơn (4/16 so với 12–13/16). Rủi ro quá khớp dev.
- **Trang SGK thật (ViSGKCap, 32 trang test):** `b0g_v1` **báo nhầm "không đọc được" 5/32 trang sạch** (15,6%); 3/32 bị cắt cụt; ~15 s mỗi trang. Chú thích ViSGKCap chép đúng chữ nhưng có lỗi mô tả cảnh; ảnh có hình mờ `hoc10.vn` (nguồn bên thứ ba). Cần hiệu chỉnh cổng "không đọc được" trên ảnh thật.
- **Dọn nhánh:** tách `describer.py` thành `common.py`/`describer.py`/`b1.py`, đổi `openrouter_client.py` → `client.py`, đưa quy trình B0 cũ vào `evaluation/legacy_b0/`; `docs/` chỉ giữ tài liệu của phần AI (phần còn lại chuyển ra `ai-for-blinds_docs_khac/`).
- **Dữ liệu ngoài** ([báo cáo](evaluation/reports/du_lieu_ngoai_20261118.md)): khảo sát, tải và xác minh SHA-256 7 bộ Hugging Face (~47 GB, 0 lỗi) bằng `external_data/`; 6 bộ khóa tạm bỏ qua (Phúc quyết). Phát hiện: vlsp2023 là tập con của OpenViVQA (9.072 ảnh trùng); ViEduVQA chứa trang SGK của ViSGKCap (cùng tranh, khác khung cắt: pHash ≤ 4 bỏ sót, NCC bắt được); OpenViVQA rò rỉ giữa split.
  Lớp phủ train/val/test theo cụm ảnh (giữ nguyên split gốc, không sửa dữ liệu gốc); `to_sft.py` xuất 29.177 Q/A vai trò train (đáp án do máy sinh, chưa dùng được ngay để dạy hệ thống).
- **Chưa làm được:** thu thập SGK từ nền tảng sách điện tử NXBGDVN (API bị chặn; chưa rõ yêu cầu kích hoạt và điều khoản; chấp thuận của thầy mới có qua lời kể).

## 2026-11-19

- **Dữ liệu:** dọn `data/local/` (4 tệp trùng benchmark xóa, `test.png` chuyển sang `data/benchmark/_legacy/`); chuyển **thật** các bộ dữ liệu ngoài vào `data/external/1_hoc_tap/` (ViSGKCap, ViEduVQA), `2_cuoc_song/` (OpenViVQA, vlsp2023, ViOCRVQA, Viet-Table-Markdown), `3_hon_hop/` (ViInfographicVQA, 9 chủ đề; chủ đề giáo dục đánh dấu ở `_reports/phan_loai_infographic.csv`);
  số tệp và dung lượng khớp trước/sau; mã tìm thư mục qua `hf.dataset_dir()`.
- **Fine-tune:** thử dựng môi trường huấn luyện riêng nhưng Phúc dừng (LM Studio chỉ chạy suy luận, không huấn luyện được); đã gỡ hết môi trường và hoàn tác phần mã chuẩn bị (prompt `ft_describe_v1`, định dạng xuất `--format spoken`). Hướng fine-tune chờ Phúc quyết.
- **Tài liệu:** giảm .md từ 26 xuống 13: gộp báo cáo (ba báo cáo dev → một; cổng ảnh vào báo cáo mô-đun; bốn báo cáo dữ liệu → một), bỏ báo cáo B0 tháng 10, chuyển hai ghi chú dự án cũ ra ngoài repo, gộp README `evaluation/` vào `ai/README.md`, rút gọn nhật ký, viết lại README gốc.

## 2026-11-23

- **Model nền:** Phúc chốt chuyển sang `google/gemma-4-e4b` (Q4_K_M, 7,5B, có thị giác, LM Studio, ctx 16384, parallel 1), chấp nhận chậm hơn.
- **Số đo** (B0e, dev 22 ảnh, 141 mệnh đề, 2 lần lặp, từ khóa thô): Gemma phủ 84,8% / 85,1% / 85,5% ở x0,5 / x1 / x1,5, Qwen 4B 83,3% / 86,2% / 87,2%: ngang nhau, trong dao động. Gemma 10,9–13,7 s mỗi ảnh (Qwen 7–9 s), VRAM đỉnh ~5 GiB (Qwen ~7,5). `schematic_map` ~0%; báo ảnh không đọc được 0/4 với prompt b0e (Qwen cũng 0/4).
- **Lưu ý kỹ thuật:** Gemma 4 mặc định bật suy nghĩ, dùng hết 600 token nên không trả nội dung (`empty_response`). Gửi `reasoning_effort=none` trong request (biến môi trường `LMSTUDIO_REASONING_EFFORT`, không đổi cài đặt LM Studio); Qwen không bị ảnh hưởng khi không đặt.
- **Dữ liệu:** tìm thêm bộ VQA tiếng Việt và tiếng Anh (biểu đồ, bảng, sơ đồ khoa học, hình học, bản đồ, VizWiz); tải xong VMMU (MIT, 1,6 GB, chỉ ở máy), xếp vào `1_hoc_tap/`, chia split theo cụm như các bộ khác (train 3.269 / val 165 / test 164, 0 trùng với bộ khác); 210 câu hỏi có 5 ảnh (nguyên trang, cắt khung, chỉ chữ) mà pHash không nối được nên nối theo mã câu hỏi (`external_data/vmmu_groups.py`) để tránh rò rỉ; dừng tải phần còn lại vì mạng hạn chế. Giấy phép GPL/NC (ChartQA, TabMWP, TQA, MapVerse) cần hỏi thầy trước khi dùng huấn luyện.
- **Chưa làm:** đo `b0g_v1` và hỏi đáp 59 câu cho Gemma; chọn cách huấn luyện cho Gemma (QLoRA trên 8 GiB VRAM chưa kiểm chứng).

## 2026-11-26

- **Làm:** thêm `--max-tokens` vào `evaluation/runner/run_b1_dev.py` (mặc định 600) và `--method b0g` (cổng "không đọc được"); chạy Gemma 4 E4B dev, B0e, 3 lần lặp, reasoning tắt/bật, ở 600 và 2000 token; sửa `proposition_check.py` (dấu "phẩy" và nhãn "Thứ Hai" ↔ "Thứ 2"); chấm rubric mẫu 4 ca lỗi; kiểm tra các bộ dữ liệu ngoài.
- **Số đo** ([báo cáo](evaluation/reports/danh_gia_model.md), bộ chấm đã sửa): tắt 121,3/141 (86,1%) ở cả 600 và 2000 token; bật 0/141 ở 600 token (`empty_response`), 120,0/141 (85,1%) ở 2000 token.
- **Kết luận:** reasoning bật và tắt ngang nhau ở 2000 token (chênh 1,3 điểm, trong dao động), reasoning bật tốn ~4 lần token đầu ra. Giữ reasoning tắt. Kết luận "tắt tốt hơn rõ rệt" của bản đầu là sai do lỗi bộ chấm, đã đính chính trong báo cáo.
- **Chấm rubric mẫu** ([báo cáo](evaluation/reports/danh_gia_model.md)): 4 ca lỗi × 2 điều kiện; do trợ lý AI chấm, không phải người, chưa đối chiếu ảnh gốc.
- **Kiểm tra dữ liệu ngoài** (xem [báo cáo dữ liệu](evaluation/reports/du_lieu_ngoai_20261118.md), mục 7): các bộ đọc được; bộ VizWiz chưa có trong báo cáo cũ.
- **Cổng và hỏi đáp (Gemma, dev):** `b0g_v1` báo đúng 6/6 lượt ảnh mờ, 0/60 báo nhầm trên ảnh đọc được (chỉ 2 ảnh mờ tổng hợp); hỏi đáp ảnh-only 42/59 (71%) so với Qwen 40/59 (68%), trong nhiễu ([báo cáo](evaluation/reports/danh_gia_model.md)).
- **Việc còn lại:** điều tra đầy đủ lỗi quan hệ (chiều mũi tên) bằng người; chấm rubric hai người; trang SGK thật với Gemma (chưa có script tương ứng trong repo); hỏi đáp có mô tả; tập test.

## 2026-11-27

- **Làm:** hiệu chỉnh cổng chất lượng ảnh trên ảnh thật (VizWiz-VQA train, 10.400 ảnh tốt; SGK 6.774 trang quét); chỉ chặn ảnh gần như đen, nhòe nặng và cháy sáng; ảnh hơi tối/mờ chuyển sang cảnh báo. Ghép `toan/tich-hop` vào `phuc` (fast-forward, không xung đột). Cập nhật `ai/README.md` (cổng, cây thư mục, mục điểm yếu đã biết) và `ai/contract/README.md` (trạng thái `unreadable`, số test, timeout, `meta.provider`).
- **Số đo** ([báo cáo](evaluation/reports/capture_gate_anh_that_20261127.md)): chặn nhầm ảnh tốt 15,1% → 1,3%; bắt ảnh tối 19,1% → 13,2%; bắt ảnh mờ 36,5% → 10,7%; 0 trang SGK bị chặn vì tối hoặc mờ. Đây là đánh đổi có chủ ý: ngưỡng mới bỏ sót nhiều ảnh xấu hơn, để VLM xử lý phần còn lại.
- **Kiểm tra:** `uv run pytest -q` trong `ai/`: 188 test đạt (không gọi mạng).
- **Chưa làm:** cổng vẫn chặn `glare` (có test), nhưng docstring và báo cáo chưa nêu, cần sửa cho khớp; chưa có ảnh bảng đen và màn hình điện thoại (khoảng 20 ảnh); chưa đo lại trang SGK với `b0g_v1` trên Gemma; các mục còn lại trong "Điểm yếu đã biết" của `ai/README.md`.

- **Benchmark dữ liệu ngoài** (Gemma 4 E4B, LM Studio, reasoning tắt, `ask_about_image` mặc định `calc=True`, chỉ ảnh; script mới `evaluation/runner/run_vmmu_val.py`, `run_openvivqa_dev.py`, `reporting/watch_progress.py`; bản ghi chỉ ở máy):
  - **Đính chính prompt:** bản ghi đầu nói đo bằng `ask_v1` là sai. Mọi ca gửi `ask_calc_v1` trước (trả JSON, phép tính do mã làm), chỉ quay về `ask_v1` khi JSON không dùng được. Đếm trong log LM Studio ngày 27/11: khoảng 573 request `ask_calc_v1`, 54 request `ask_v1` (số đếm gần đúng: 579 ca đáng ra có ít nhất 579 request đầu). Không biết từng ca đi đường nào. Thông số: temperature 0,2, max_tokens 400, reasoning_effort none; Q4_K_M, ctx 16384, parallel 1, flash attention; top_p, top_k, seed không gửi; mỗi ca chạy một lần.
  - VMMU trắc nghiệm: val 17/133 (12,8%), test 21/138 (15,2%); không tách được đáp án 82 và 80 ca; trong số ca tách được đáp án: 17/51 và 21/58; lỗi vận hành 5 và 3 ca (chưa rõ nguyên nhân, bản ghi VMMU không lưu mã lỗi). **VMMU test đã dùng một lần.**
  - OpenViVQA: file test không có đáp án nên đo trên 300 ảnh dev (mẫu cố định, mỗi ảnh một câu), 0 lỗi, khoảng 2,4 s mỗi ca. Chứa nguyên cụm đáp án 28/300 (9,3%), phủ từ trung bình 64,0%. **Không dùng 9,3% làm độ chính xác:** đáp án chuẩn thường là cả câu nhắc lại câu hỏi, model diễn đạt khác thì bị tính sai (34 ca có đủ mọi từ của đáp án mà vẫn bị tính sai). Trợ lý AI đọc 25 ca bị tính sai (không phải người chấm, không xem ảnh): khoảng 6 ca đúng rõ, thêm 3 ca đúng một phần.
  - Giả thuyết chưa kiểm chứng: `ask_calc_v1` và `ask_v1` đều viết cho hỏi đáp trang sách (chỉ dựa vào ảnh, không thấy thì nói không thấy, đọc số bằng chữ, không ký hiệu), trái với yêu cầu ghi `{X}` của VMMU và có thể làm model không chịu giải đề; riêng `ask_calc_v1` còn yêu cầu không tự tính, câu trả lời có thể thành câu mẫu kèm số do mã tính, không có chữ cái đáp án.
  - **Chấm lại** (trợ lý AI đọc từ câu trả lời đã lưu, không gọi model, không xem ảnh, người chấm thấy đáp án chuẩn; không phải chấm bởi người): OpenViVQA 300 ca: đúng 129 (43,0%), một phần 38 (12,7%), sai 133. VMMU, nhận thêm đáp án model nêu rõ bằng lời mà bộ tách bỏ sót: val 23/133 (17,3%), test 30/138 (21.7%). Điểm tự động giữ nguyên để so sánh; phán quyết lưu ở các file `records_*__cham_lai.jsonl`, `records_*__cuu_dap_an.jsonl` (chỉ ở máy).
  - **VLM gốc so với qua hệ thống** (30 ca VMMU val đầu theo SHA-256; script `evaluation/runner/run_vmmu_raw.py`; gốc: không system prompt, temperature 0, max_tokens 4096, reasoning tắt, 1 lần): gốc 17/30; qua hệ thống (bản ghi cũ, đã chấm lại) 4/29, 1 ca lỗi. Cùng ca: chỉ gốc đúng 13, chỉ hệ thống đúng 1, cả hai đúng 3, cả hai sai 12, và 1 ca gốc đúng mà hệ thống lỗi. Gốc không ca nào bị cắt hay bỏ trống đáp án; 21/30 câu trả lời dài hơn 400 token; trung bình 27 s/ca (hệ thống 3,9 s). Nhiều thứ khác nhau cùng lúc (prompt, JSON và tính hộ, temperature, max_tokens) nên chưa tách được nguyên nhân. Gốc hay chọn bừa kèm lý do không có cơ sở khi không giải được (vd. "theo quy ước của nguồn đề bài").
- **Baseline Qwen gốc** (`unsloth/Qwen3-VL-4B-Instruct-GGUF` Q4_K_M, mmproj F32, ctx 16384, parallel 1; cùng 30 ca và cùng thiết lập gốc): 15/30, Gemma gốc 17/30; chỉ Qwen đúng 7, chỉ Gemma đúng 9, cả hai đúng 8, cả hai sai 6: chưa phân định. Qwen 3 ca bị cắt ở 4096 token (không chốt đáp án); 18/30 ca chỉ trả `{X}` (đúng 6/18), 12 ca còn lại đúng 9/12 (hai nhóm khác loại câu hỏi, không suy ra nhân quả). Trung bình 15,3 s/ca, trung vị 6,9 s (Gemma 27,0 và 22,5). Không có chữ Hán/Kirin trong 30 câu trả lời. VRAM sau khi nạp: 7021/8192 MiB.
- **Lỗi phát hiện:** `speech/tts_text.py::prepare_for_speech` đọc số điện thoại như số nguyên và mất số 0 đầu; chưa thấy `pipeline.py` hay backend gọi hàm này. Chưa sửa.
- **Chưa làm (benchmark):** thử prompt riêng cho trắc nghiệm trên val; bộ chấm OpenViVQA tốt hơn (chấm tay mẫu hoặc người/mô hình làm giám khảo); xem nguyên nhân ca lỗi VMMU.

- **Định hướng và quy cách đầu ra (sau khi Phúc và Toàn hỏi lại thầy):** không giải bài tập, chỉ trả lời điều được hỏi, bài giải mẫu được đọc, ảnh bài tập đọc đề trước; xem [`README.md`](README.md#quy-cách-đầu-ra-chốt-ngày-27112026). Hệ quả: các phép đo VMMU ở trên đo khả năng chọn đáp án, không phải chất lượng sản phẩm; so sánh gốc và qua hệ thống chỉ đúng cho việc chọn đáp án; Qwen chỉ để thử quy trình hoặc đối chứng. Đã cập nhật tài liệu; **chưa sửa** prompt, `calc`, bộ sinh dữ liệu, rubric.

- **Chốt thêm:** được nói chênh lệch hai cột; ảnh không kèm câu hỏi chỉ nói ngắn phần nổi bật nhất hoặc đọc đề mục lớn; ảnh không đọc được thì báo và hướng dẫn chụp lại. Sau khi đọc đề: được giải nghĩa từ ngữ, khái niệm trong đề, không chỉ cách làm.

- **Chốt thêm:** trang đánh dấu bài kiểm tra hoặc bài thi chỉ được mô tả theo hình ảnh có sẵn; chấm bài viết tay của người dùng nằm ngoài phạm vi hiện tại. Còn mở: cách xét phép tính theo đề bài, câu hỏi trùng bài tập trên trang, kiến thức ngoài ảnh ở trang thường.

- **Chốt thêm:** câu hỏi cần kiến thức không có trong ảnh thì nói trang không ghi rồi dừng.

- **Chốt thêm:** câu hỏi trùng bài tập trên trang thì chỉ đọc dữ kiện; không trùng hoặc không có bài tập thì được trả lời (kể cả chênh lệch hai cột). Phép tính khác tạm thời không làm (mặc định).

- **Luồng và format trả lời:** chốt luồng mô tả ngắn → app hỏi câu cố định → hỏi đáp; format A (xem `ai/README.md`).
- **Hướng dẫn chụp trên app** (Nam đề nghị; phần app của Toàn): đo tối, chói, mờ, rung trên khung xem trước và trên ảnh vừa chụp (`frontend/lib/capture/`), không dùng thư viện ngoài mới; có công tắc và số đếm trên máy. `flutter test` 124 đạt, 3 bỏ qua (trước 84 đạt), `flutter analyze` sạch, Flutter 3.44.1 như CI. So với cổng máy chủ trên 121 ảnh trên máy: cùng kết luận 118. **Chưa build APK, chưa chạy trên thiết bị, ngưỡng chưa hiệu chỉnh, phần nối camera không có test.** Canh khung và tự chụp chưa làm.
- **Xác nhận lỗi:** cổng máy chủ vẫn chặn nhầm hình nền đen rõ nét (chưa sửa).

- **Gộp báo cáo:** sáu báo cáo đánh giá model gộp thành [`danh_gia_model.md`](evaluation/reports/danh_gia_model.md); giữ riêng báo cáo dữ liệu ngoài và cổng ảnh. Link ở các mục cũ trỏ sang báo cáo gộp.
- **Đính chính mục 26/11:** câu "hỏi đáp ảnh-only Gemma 42/59 so với Qwen 40/59, trong nhiễu" **so lệch điều kiện**: lượt Gemma có mã tính hộ (`ask_calc_v1`), 40/59 của Qwen là lượt không tính hộ. Qwen có tính hộ: 51/59 và 53/59.

## Việc tiếp theo

Xem mục "Việc tiếp theo" của `README.md` gốc (một danh sách duy nhất).

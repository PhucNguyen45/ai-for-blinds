# Đánh giá model và mô-đun hệ thống (17/11 – 26/11/2026)

> **Trạng thái:** thăm dò, **chưa phải kết luận khoa học**. **Mảng:** A.
> Gộp ngày 27/11/2026 từ sáu báo cáo (so sánh phương pháp và model 17/11; khảo sát Qwen3-VL Q4 17–18/11; mô-đun hệ thống 18–19/11; reasoning Gemma 4, cổng và hỏi đáp Gemma, chấm rubric mẫu 26/11). Bản đầy đủ của từng báo cáo nằm trong lịch sử git (trước commit gộp, ví dụ `a0cdcd9`).
>
> **Điều kiện chung** (trừ khi ghi khác): benchmark v0.2.0, tập **dev** gồm 22 ảnh tổng hợp (20 đọc được, 2 `_unreadable`), 141 mệnh đề `critical`; tập test chưa chạy. Chỉ số phủ mệnh đề và chấm hỏi đáp là **từ khóa thô** (`reporting/proposition_check.py`, `qa_score.py`): chỉ kiểm số và tên có xuất hiện, **không đo độ đúng, độ bịa, chiều quan hệ**, không thay rubric bằng người. Ground truth do mã sinh, chưa có người thứ hai rà. Model cục bộ chạy trên LM Studio, RTX 2070 Max-Q 8 GB.
>
> Các phép đo này làm **trước khi có [Quy cách đầu ra](../../README.md#quy-cách-đầu-ra-chốt-ngày-27112026)**; câu hỏi tính toán trong đó không nói lên việc sản phẩm được phép tính.

## Tóm tắt

| Câu hỏi | Kết quả trên dev | Mục |
|---|---|---|
| Phương pháp hai bước B1 có hơn một bước B0e không? | Với nemotron: 115 so với 106; với Qwen 4B: **kém** (92 so với 123) | 1 |
| Phóng ảnh có giúp Qwen 4B không? | 83,3% → 86,2% → 87,2% (x0,5, x1, x1,5); chênh x1–x1,5 trong dao động | 2 |
| Qwen 8B Q4 có dùng được trên máy 8 GB không? | Không: không nạp đủ lên GPU, chậm | 2 |
| `b0g_v1` báo ảnh không đọc được | Đúng trên ảnh mờ tổng hợp, nhưng **báo nhầm 5/32 trang SGK sạch** (Qwen) | 3, 5 |
| Gemma 4 E4B bật hay tắt reasoning? | Ngang nhau ở 2000 token; bật ở 600 token không trả nội dung | 4 |
| Gemma 4 E4B so với Qwen 4B | Mô tả: ngang nhau trong dao động. **Hỏi đáp có tính hộ: Gemma 42/59, Qwen 51–53/59** (xem đính chính ở mục 5) | 4, 5 |

## 1. Phương pháp B0, B0e, B1 và model (17/11)

temperature 0,2, reasoning tắt, 1 lần mỗi ảnh. Prompt B0e, B1 đóng băng trước khi chạy.

| Điều kiện | Mô tả | Prompt |
|---|---|---|
| B0 | Diễn giải trực tiếp, `max_tokens` 600 | `b0_v1` |
| B0e | B0 thêm dòng "nêu đủ mọi nhãn và giá trị số"; đối chứng thêm **sau khi** thấy B1 cải thiện bảng | `b0e_v1` |
| B1 | Ảnh → JSON dữ kiện, rồi JSON → diễn giải (không gửi lại ảnh); 2 request | `b1_extract_v1`, `b1_describe_v1` |

| Loại | Mệnh đề | nemotron B0 | nemotron B0e | nemotron B1 | gemini-3.1-flash-lite B0e | qwen3-vl-4b B0e | qwen3-vl-4b B1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| bar_chart | 27 | 27 | 26 | 27 | 27 | 27 | 26 |
| line_chart | 19 | 17 | 17 | 17 | 17 | 17 | 10 |
| pie_chart | 12 | 8 | 10 | 8 | 12 | 12 | 9 |
| table | 33 | 20 | 23 | 33 | 33 | 33 | 33 |
| flow_diagram | 13 | 11 | 13 | 12 | 13 | 13 | 7 |
| cycle_diagram | 13 | 3 | 5 | 6 | 9 | 9 | 0* |
| geometry | 12 | 10 | 11 | 10 | 10 | 10 | 6 |
| schematic_map | 12 | 2 | 1 | 2 | 2 | 2 | 1 |
| **Tổng** | **141** | 98 (70%) | 106 (75%) | 115 (82%) | 123 (87%) | 123 (87%) | 92 (65%) |

\* Hai ảnh sơ đồ vòng trả JSON hỏng (`invalid_output`) nên tính 0; khôi phục offline vẫn còn cạnh đọc sai.

- Model: `nvidia/nemotron-3.5-super-vl:free` (OpenRouter), `gemini-3.1-flash-lite` (Google gói miễn phí), `qwen/qwen3-vl-4b` (cục bộ, trung vị B0e 6,3 s, B1 6,8 s). `gemini-3.8-flash` chỉ có 19/22 ảnh (20 request mỗi ngày) nên không so; `gemma-4-31b-it:free` bị 429.
- Chi phí nemotron (trung vị): B0e khoảng 3,1 s và 1,35 nghìn token; B1 khoảng 7,3 s và 2,16 nghìn token.
- **Chạy lặp 3 lần, Qwen 4B B0e:** 123, 123, 123/141 (độ lệch chuẩn 0; ổn định 20/20 ảnh), dù không câu trả lời nào giống nhau từng ký tự (0/22). Độ lệch 0 là **hiệu ứng trần** của chỉ số.
- **Quan sát cần chấm tay mới kết luận được:**
  - Nemotron hay chép sai dấu nhãn ("Trống lúa", "Rau máu"); Qwen 4B và Gemini gần như không (pie 12/12). Với nemotron B0, nếu **bỏ qua dấu** khi chấm: pie 12/12 (so với 8/12 khi chấm chặt), flow 13/13, cycle 6/13, tức phần lớn khác biệt là sai dấu hoặc chính tả.
  - Bảng: B1 giúp nemotron đọc đủ, nhưng B0e của Qwen và Gemini cũng đạt 33/33; chỉ có 2 bảng.
  - B1 với model nhỏ bị lan truyền lỗi (bước diễn giải không nhìn lại ảnh), ví dụ `line_01` còn 1/6 điểm.
  - `cycle_03` bịa giai đoạn "Hạt mọc"; B1 vẫn mắc, lỗi nằm ngay trong `facts`.
  - Bản đồ khoảng 2/12 ở mọi điều kiện: ground truth viết hướng tương đối, model nêu vị trí tuyệt đối, nên chỉ số đánh giá thấp.
  - B0 và B0e nói ảnh mờ trong văn bản nhưng vẫn trả `ok`; chỉ B1 trả `unreadable` có cấu trúc (2/2). Đó là lợi ích về hợp đồng, chưa phải độ chính xác: model vẫn có thể bịa chi tiết.
  - Model nhỏ còn lỗi định dạng: nháy kép không thoát trong JSON (2/22), lẫn nhãn kỹ thuật vào lời diễn giải, nhầm `image_type`; đã thêm bộ khôi phục JSON.
- 26/11: bộ chấm được sửa (mục 4). Chấm lại Qwen B0e 3 lần vẫn 123/141; số của nemotron và Gemini chưa chấm lại.

## 2. Khảo sát Qwen3-VL Q4 (17–18/11)

Prompt `b0e_v1`, ctx 16384, parallel 1, Flash Attention bật, mã git `47aaa02`.

### 2.1. 4B Q4_K_M (132 request, 2 lần lặp mỗi mức)

| Mức | Cỡ ảnh | Phủ trung bình | Từng lần | Token vào | Token ra | Thời gian TB / p95 (s) |
|---|---|---|---|---:|---:|---|
| x0,5 | 550×360 | 117,5/141 (83,3%) | 119, 116 | 444 | 413 | 7,2 / 10,0 |
| x1 | 1100×720 | 121,5/141 (86,2%) | 123, 120 | 1005 | 395 | 7,6 / 10,3 |
| x1,5 | 1650×1080 | 123,0/141 (87,2%) | 123, 123 | 2025 | 379 | 9,1 / 11,7 |

| Loại hình | x0,5 | x1 | x1,5 |
|---|---|---|---|
| bar_chart | 92,6% | 100% | 100% |
| line_chart | 89,5% | 89,5% | 89,5% |
| pie_chart | 95,8% | 87,5% | 100% |
| table | 100% | 100% | 100% |
| flow_diagram | 100% | 100% | 100% |
| cycle_diagram | 46,2% | 69,2% | 69,2% |
| geometry | 83,3% | 83,3% | 83,3% |
| schematic_map | **16,7%** | **16,7%** | **16,7%** |

- VRAM đỉnh khoảng 7452/8192 MiB ở cả ba mức; sinh chữ khoảng 52 token/s. Hai lần bị cắt ở 600 token đều ở x0,5.
- Ảnh không đọc được: 0/4 lần báo ở mỗi mức; prompt `b0e_v1` không hướng dẫn việc này.
- Phóng bằng nội suy không thêm chi tiết thật nên **chưa biết** có giúp trên ảnh thật không. temperature thấp vẫn không cho kết quả giống hệt giữa hai lần.

### 2.2. 8B Q4_K_M (dở dang: 63/132 request, 1 lần lặp; Phúc dừng vì chậm)

- Mỗi mô tả trung bình **61 s (x0,5), 97 s (x1), 118 s (x1,5)**, p95 tới 160 s; sinh 3–14 token/s. Hai request quá 300 s. VRAM 7839 MiB ngay khi nạp, đỉnh 7963.
- Chẩn đoán từ log: chỉ 30–34 trong 36 lớp ở trên GPU, phần còn lại chạy CPU (4 luồng). Nạp lại với ctx 8192 và 34 lớp: 21–31 s mỗi mô tả (3 ảnh), vẫn chậm khoảng 3 lần so với 4B. Không phải quá nhiệt (52–58 °C), có giới hạn công suất của dòng Max-Q. Đổi hai thứ cùng lúc nên chưa tách được đóng góp.
- So cùng ảnh, lần lặp 1:

| Mức | Số ảnh | Mệnh đề | 8B | 4B |
|---|---:|---:|---:|---:|
| x0,5 | 18 | 108 | 91 | 86 |
| x1 | 20 | 141 | 125 | 123 |
| x1,5 | 19 | 138 | 120 | 120 |

Chênh nằm trong dao động đã thấy ở 4B: **không kết luận được 8B tốt hơn**. Bản đồ sơ đồ của 8B vẫn thấp (16,7–33,3%); 8B cũng không báo "unreadable" lần nào (0/2 ở x0,5 và x1).

## 3. Mô-đun hệ thống với Qwen3-VL 4B (18–19/11)

### 3.1. Prompt `b0g_v1` báo ảnh không đọc được (22 ảnh × 2 lần)

| Chỉ tiêu | `b0e_v1` | `b0g_v1` |
|---|---|---|
| Ảnh mờ được báo `unreadable` | 0/4 | 4/4 |
| Ảnh đọc được bị báo nhầm | — | 0/40 |
| Phủ mệnh đề (x1) | 121,5/141 (86,2%) | 120,5/141 (85,5%) |
| Thời gian / token ra mỗi mô tả | 7,6 s / 395 | 4,5 s / 277 |

Chỉ 2 ảnh mờ tổng hợp rất nặng; chưa thử mờ nhẹ, chói một phần, hình bị cắt. Sau khi gộp mã gọi model, chạy lại phủ 118,5/141 (84,0%), vẫn 4/4.

### 3.2. Hỏi đáp theo hình (59 câu dev, mỗi điều kiện 1 lần)

| Phiên bản | Chỉ ảnh | Ảnh + mô tả cũ | computation (chỉ ảnh) | relation (chỉ ảnh / kèm mô tả) |
|---|---|---|---|---|
| `ask_v1`, model tự tính | 40/59 (67,8%) | 41/59 (69,5%) | 8/15 | 7/16 / 4/16 |
| `ask_calc_v1`, mã tính (`vlm/calc.py`) | 51/59 (86,4%) | 42/59 (71,2%) | 13/15 | 12/16 / 4/16 |
| thêm `sqrt` và lọc ký tự ngoài tiếng Việt | **53/59 (89,8%)** | 44/59 (74,6%) | 15/15 | 13/16 / 4/16 |

- Chỉ ảnh, `ask_v1`: lookup 15/16, comparison 10/12. Lỗi thật chủ yếu là cộng sai (40+35+5+19+6 bị nói thành 51 hoặc 55).
- Đọc tay (một người đọc, chưa rà lại): khoảng một phần ba câu "sai" là do cách chấm (thiếu đơn vị, cách nói hướng).
- Mức tăng ở `relation` **chưa quy được cho bước tính**: prompt đổi cả câu chữ, model chuyển sang nói hướng la bàn.
- Kèm mô tả cũ làm `relation` tệ hơn, nhất quán qua ba lần: nên hỏi vị trí, hướng chỉ bằng ảnh.
- Ký tự CJK lẫn trong 2/548 bản ghi cũ; 0/162 bản ghi mới. Bộ lọc **chưa từng được kích hoạt trên đầu ra thật**.
- **Rủi ro quá khớp:** các thay đổi được chọn sau khi xem lỗi của chính 59 câu này.

### 3.3. Cổng ảnh trên 1.200 ảnh huấn luyện tổng hợp (ngưỡng cũ)

Bắt `blur` 21/21, `dark` 33/33, `glare` 10/27, cắt mép 0/74 (không bắt, theo thiết kế); báo nhầm ảnh đạt 0/1045. **Ngưỡng này đã được thay** sau khi đo trên ảnh thật: xem [báo cáo cổng ảnh](capture_gate_anh_that_20261127.md).

### 3.4. 32 trang SGK thật (ViSGKCap, tập test, lớp 1–3, trang sạch)

`b0g_v1`, `max_tokens` 800; trang chọn xác định (mỗi 4 trang theo id).

| Chỉ tiêu | Kết quả |
|---|---|
| Báo nhầm "không đọc được" | **5/32 (15,6%)** (lý do model nêu: bị cắt, mờ, che khuất) |
| Bị cắt cụt (hết 800 token) | 3/32 |
| Đọc bình thường | 24/32 |
| Thời gian mỗi trang | 14,6 s (khoảng 2.950 token vào) |
| Câu trích trong chú thích ViSGKCap có trong mô tả | 131/395 (33%): Toán 57%, Tiếng Việt 23%, Tự nhiên và Xã hội 19%, Đạo đức 12% |

Chỉ số trích dẫn rất thô và đánh giá thấp. Chú thích ViSGKCap do máy sinh, chưa phải ground truth; hai trang xem bằng mắt cho thấy chữ chép gần đúng hết, mô tả cảnh có lỗi (đếm sai, gọi học sinh là người lớn). **Chưa đo lại với Gemma.**

## 4. Gemma 4 E4B: reasoning bật hay tắt (26/11)

`google/gemma-4-e4b` Q4_K_M, ctx 16384, parallel 1, prompt `b0e_v1`, temperature 0,2, **3 lần lặp** mỗi ảnh. Tắt bằng `LMSTUDIO_REASONING_EFFORT=none`; lệnh: `run_b1_dev.py --method b0e --provider lmstudio --model google/gemma-4-e4b --reps 3 --max-requests 100 --max-tokens 2000 --execute`.

| Điều kiện | r01, r02, r03 | Trung bình (/141) | Ghi chú |
|---|---|---|---|
| Tắt, 600 token | 121, 121, 122 | 121,3 (86,1%) | độ lệch chuẩn 0,6; ổn định 16/20 ảnh |
| Tắt, 2000 token | 121, 120, 123 | 121,3 (86,1%) | độ lệch chuẩn 1,5; ổn định 15/20 ảnh |
| Bật, 600 token | 0, 0, 0 | 0 | 18, 16, 19 request `empty_response` (suy nghĩ dùng hết token); ổn định 20/20 ảnh vì đều trống |
| Bật, 2000 token | 119, 121, 120 | 120,0 (85,1%) | độ lệch chuẩn 1,0; ổn định 18/20; ví dụ một mẫu: khoảng 1.311 token ra so với 332 khi tắt |

- Kết luận: **giữ reasoning tắt**. Muốn bật phải đặt `max_tokens` ≥ 2000.
- **Đính chính (26/11):** bản đầu kết luận "tắt tốt hơn rõ rệt" (121 so với 111) là **sai**: bộ chấm bỏ sót dạng "8 phẩy 5" và nhãn "Thứ Hai" khi ground truth ghi "Thứ 2". Số trên là sau khi sửa bộ chấm (lỗi từng làm `table_01` còn 3/15). Bản ghi khảo sát và hỏi đáp cũ của Qwen cũng có nhãn thứ viết chữ nên điểm có thể đổi nhẹ; **chưa chấm lại**.
- So với Qwen 4B B0e ở mục 1 và 2 (123/141; 121,5/141 ở khảo sát x1), mức phủ mô tả của Gemma **ngang trong dao động**. Gemma chậm hơn: 11–14 s so với 7–9 s mỗi mô tả (số đo 23/11 trong nhật ký).

## 5. Gemma 4 E4B: cổng `b0g_v1` và hỏi đáp (26/11)

Reasoning tắt. `run_b1_dev.py --method b0g --reps 3`; `run_qa_dev.py --tag gemma_off_img --description none`.

**Cổng:** ảnh đọc được 60 lượt, báo nhầm **0**; ảnh mờ báo đúng **6/6**. Chỉ có 2 ảnh mờ tổng hợp; chưa chạy trang SGK với Gemma.

**Hỏi đáp, chỉ ảnh (59 câu, 1 lần):**

> **Đính chính (27/11):** báo cáo ngày 26/11 so Gemma 42/59 với Qwen **40/59** và kết luận hai model ngang nhau. **Kết luận đó sai vì khác điều kiện:** kiểm `meta.prompt_id` trong bản ghi, lượt Gemma dùng `ask_calc_v1` (48 câu) và rơi về `ask_v1` (11 câu), tức **có mã tính hộ**; còn 40/59 của Qwen là lượt `ask_v1` **không tính hộ**. Các lượt Qwen có tính hộ đạt 51/59 và 53/59.

| Loại | Gemma (`ask_calc_v1`, có dự phòng) | Qwen `ask_calc_v1` (18/11) | Qwen, thêm `sqrt` và lọc (18/11) | Qwen `ask_v1`, **khác điều kiện** |
|---|---|---|---|---|
| lookup | 15/16 | 16/16 | 16/16 | 15/16 |
| comparison | 10/12 | 10/12 | 9/12 | 10/12 |
| computation | 11/15 | 13/15 | 15/15 | 8/15 |
| relation | 6/16 | 12/16 | 13/16 | 7/16 |
| **Tổng** | **42/59 (71,2%)** | **51/59 (86,4%)** | **53/59 (89,8%)** | 40/59 (67,8%) |

- Trên bộ này, **Qwen hơn Gemma 9–11 câu**, chênh nhiều nhất ở `relation`.
- Vẫn chưa phải so sánh đối đầu sạch: hai model chạy khác ngày và khác phiên bản mã (cơ chế dự phòng về `ask_v1` không thấy trong lượt Qwen); prompt tính hộ được **chỉnh sau khi xem lỗi của Qwen trên chính 59 câu này**, nên có lợi cho Qwen; mỗi bên 1 lần.
- Hỏi đáp có kèm mô tả và với reasoning bật: chưa chạy cho Gemma.

## 6. Chấm rubric_v1 mẫu, Gemma (26/11)

**Người chấm là trợ lý AI, không phải người**; không đối chiếu ảnh gốc, chỉ dựa trên ground truth và văn bản trả lời. Bốn ca lỗi, lần r01, reasoning tắt và bật (2000 token).

| Ca | Điều kiện | C1 | C2 | C3 | C4 | C5 | C6 | Tổng/12 |
|---|---|---|---|---|---|---|---|---|
| cycle_03 | tắt | 2 | 1 | 0 | 1 | 1 | 2 | 7 |
| cycle_03 | bật | 2 | 1 | 0 | 1 | 1 | 2 | 7 |
| pie_03 | tắt | 2 | 2 | 2 | 1 | 2 | 2 | 11 |
| pie_03 | bật | 2 | 2 | 2 | 1 | 1 | 2 | 10 |
| table_03 | tắt | 2 | 2 | 2 | 1 | 2 | 2 | 11 |
| table_03 | bật | 2 | 2 | 2 | 1 | 2 | 2 | 11 |
| map_01 | tắt | 2 | 2 | 1 | 1 | 2 | 2 | 10 |
| map_01 | bật | 2 | 2 | 1 | 1 | 1 | 2 | 9 |

- `cycle_03`: nêu đúng năm giai đoạn nhưng **sai chiều mũi tên** và nói chắc chắn (cả hai điều kiện); chỉ số từ khóa không bắt được.
- `map_01`: đúng năm địa điểm, không nêu quan hệ với "Trường học". Hai ca bị trừ C5 vì nhận định chưa rõ có trên ảnh.
- Lỗi lớn nhất là **quan hệ và chiều**, không phải số liệu. Cần hai người chấm độc lập trên ảnh gốc.

## 7. Tái lập và việc còn lại

- Công cụ (chạy trong `ai/`): `evaluation/runner/run_b1_dev.py`, `run_qa_dev.py`, `survey_lmstudio.py`; `evaluation/reporting/proposition_check.py`, `repeat_stats.py`, `survey_report.py`, `qa_score.py`, `capture_gate_eval.py`. Bản ghi ở `evaluation/records*` chỉ có ở máy tác giả. Bảng chi tiết của 8B sinh lại được bằng `survey_report.py evaluation/records_survey__baseline_8b_q4_ctx16k_p1`.
- Còn lại: chấm tay hai người; hiệu chỉnh và đo lại "không đọc được" trên trang SGK thật (cả Gemma); so lại hỏi đáp Gemma và Qwen **cùng phiên bản mã, cùng ngày, nhiều lần lặp**; chỉ số cho lỗi bịa và chiều quan hệ; tập test chỉ chạy khi đã đóng băng cấu hình.

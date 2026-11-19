# Đo các mô-đun hệ thống với Qwen3-VL-4B Q4

> **Trạng thái:** thăm dò. **Ngày:** 2026-11-18 · **Cập nhật:** 2026-11-19 · **Mảng:** A
> **Kết luận ngắn:** trên ảnh tổng hợp, cổng ảnh bắt 100% ảnh tối/mờ không báo nhầm, prompt `b0g_v1` báo đúng 4/4 ảnh mờ, và hỏi đáp tăng từ 68% lên 90% nhờ để mã tính toán.
> **Nhưng trên 32 trang SGK thật (mục 6), `b0g_v1` báo nhầm "không đọc được" 5/32 trang sạch**: kết quả trên ảnh tổng hợp không khái quát được. Một model, 1–2 lần lặp, chỉ số từ khóa thô; tập test chưa chạy.

**Cấu hình:** `qwen/qwen3-vl-4b` Q4_K_M trên LM Studio, context 16384, parallel 1, Flash Attention bật (đọc từ API LM Studio, lưu trong
`qa_meta.json` / `survey_meta.json` của từng đợt). Benchmark v0.2.0, tập **dev** (ảnh tổng hợp), trừ mục 6.

## 1. Prompt `b0g_v1` — báo "ảnh không đọc được" (22 ảnh dev × 2 lần lặp, ảnh gốc)

| Chỉ tiêu | `b0e_v1` (đợt khảo sát trước) | `b0g_v1` |
|---|---|---|
| Ảnh mờ được báo `unreadable` | 0/4 | **4/4** |
| Ảnh đọc được bị báo nhầm | — | **0/40** |
| Phủ mệnh đề critical (x1) | 121,5/141 (86,2%) | 120,5/141 (85,5%) |
| Thời gian mỗi mô tả | 7,6 s | 4,5 s |
| Token ra trung bình | 395 | 277 |

Lời hướng dẫn model sinh ra là câu chụp lại tự nhiên (mờ → giữ yên máy, thêm sáng, đổi góc). Dữ liệu: `records_survey__b0g_prompt_4b_ctx16k_p1/`.

**Hạn chế:** chỉ 2 ảnh không đọc được (mờ tổng hợp rất nặng), nên 4/4 là 2 ảnh × 2 lần; chưa thử mờ nhẹ, chói che một phần, hình bị cắt, hay ảnh thật.
Phủ mệnh đề tương đương (chênh nằm trong dao động giữa các lần lặp) nhưng câu trả lời ngắn hơn nhiều (277 so với 395 token); chỉ số từ khóa không cho
thấy mất chi tiết, cần đọc tay để chắc.

## 2. Hỏi đáp theo hình (`ask_v1`, 59 câu hỏi dev, một lần chạy mỗi điều kiện)

| Điều kiện | Tổng | lookup | comparison | computation | relation |
|---|---|---|---|---|---|
| Chỉ ảnh | 40/59 (67,8%) | 15/16 | 10/12 | 8/15 | 7/16 |
| Ảnh + lời mô tả đã sinh trước đó | 41/59 (69,5%) | 15/16 | 9/12 | **13/15** | 4/16 |

Thời gian mỗi câu trả lời chỉ khoảng 0,6 đến 0,7 s vì LM Studio tái dùng bộ nhớ đệm của ảnh khi các câu hỏi liên tiếp cùng một ảnh (không phải số đo cho ảnh mới).

**Chỉ số này là từ khóa thô và đánh giá thấp:** tôi đọc từng câu "sai" (ước lượng của riêng tôi, chưa có người thứ hai rà) và thấy khoảng một phần ba
là sai do cách chấm, không phải sai thật: đáp án có đơn vị ("5 cuốn") nhưng câu trả lời chỉ nêu số; "giữa tháng 3 và tháng 4" so với "Tháng 3 đến Tháng 4";
"phía dưới, bên trái" so với "Tây Nam"; "chiều kim đồng hồ" so với "cùng chiều kim đồng hồ". Cần chấm tay mới có điểm đáng tin.

**Các sai sót thật, theo loại (chỉ ảnh):**
- **Tính toán:** cộng sai ở 4 trong 5 câu tổng của biểu đồ cột/bảng, ví dụ 40 + 35 + 5 + 19 + 6 = 105 nhưng model nói 51 hoặc 55; diện tích tam giác 3 × 4 / 2 = 6 nhưng model nói "ba phần tư chục cm vuông".
  Khi có lời mô tả kèm theo (đã liệt kê giá trị), tính toán tăng từ 8/15 lên 13/15. Một lần chạy, nhưng hướng khá rõ.
- **Quan hệ:** sơ đồ vòng sai thứ tự ở một số câu; ở bản đồ model hay nói "phía dưới, bên trái" thay vì dùng hướng la bàn như đáp án.
  Có lời mô tả kèm theo thì quan hệ **giảm** từ 7/16 xuống 4/16 (phần lớn là cách diễn đạt hướng, cần chấm tay).

**Phát hiện phụ:** lẫn ký tự ngoài tiếng Việt: câu trả lời `table_01` có chữ Hán "零" và "zero"; một bản ghi B1 cũ có "知". Trong 548 bản ghi lưu có chữ, chỉ 2 bản
(0,4%) chứa ký tự CJK, nhưng với người dùng khiếm thị mỗi lần xảy ra là một âm thanh lạ khi đọc.

## 3. Hệ quả cho thiết kế hệ thống (đề xuất, chưa thực hiện)

1. **Tính toán không nên để model làm một mình.** Đưa các giá trị đã đọc vào một bước tính bằng mã (hoặc công cụ tính) rồi để model diễn đạt kết quả; hướng này đã được gợi ý bởi bước tăng 8/15 → 13/15 khi có lời mô tả.
2. **Chuẩn hóa cách nói hướng** (la bàn hay "trên, dưới, trái, phải") trong `ask_v1` và đánh giá, rồi chấm lại.
3. **Bộ lọc ngôn ngữ đầu ra:** phát hiện ký tự ngoài tiếng Việt, thử lại hoặc loại bỏ trước khi đưa cho TTS.
4. **Chấm tay** (rubric hoặc ít nhất hai người rà các câu "sai") trước khi đưa số liệu hỏi đáp vào báo cáo chính thức.

## 4. Cải thiện sau lần đo đầu (2026-11-18, cùng cấu hình, tập dev)

Ba thay đổi: (a) prompt `ask_calc_v1`: model viết biểu thức số học, **mã** (`vlm/calc.py`) tính kết quả rồi điền vào câu mẫu; (b) `calc.py` cho phép thêm `sqrt(...)` (cạnh huyền);
(c) `chat_vi` (`vlm/common.py`): câu trả lời có chữ Hán/Nhật/Hàn/Kirin/Ả Rập thì gọi lại một lần, nếu vẫn còn thì loại ký tự đó và ghi vào `uncertainties`.

| Phiên bản hỏi đáp (59 câu dev, 1 lần chạy) | Chỉ ảnh | Ảnh + lời mô tả | computation (chỉ ảnh) | relation (chỉ ảnh / kèm mô tả) |
|---|---|---|---|---|
| `ask_v1`, model tự tính | 40/59 (67,8%) | 41/59 (69,5%) | 8/15 | 7/16 / 4/16 |
| `ask_calc_v1`, mã tính | 51/59 (86,4%) | 42/59 (71,2%) | 13/15 | 12/16 / 4/16 |
| + `sqrt` + lọc ngôn ngữ | **53/59 (89,8%)** | 44/59 (74,6%) | **15/15** | 13/16 / 4/16 |

- **Tính toán đúng hết 15/15** (tổng, diện tích, chu vi, cạnh huyền, cộng phần trăm). Đây là cải thiện có nguyên nhân rõ: model không còn tự cộng.
- **Cải thiện ở `relation` (7 → 12 → 13/16) chưa quy được cho bước tính toán**: prompt JSON đổi cả câu chữ, và model chuyển sang dùng hướng la bàn ("phía Nam", "Đông nam") thay cho "phía dưới". Hai thay đổi gộp lại, chưa tách được.
- **Kèm lời mô tả làm `relation` tệ hơn rõ rệt (4/16 so với 12–13/16)**, nhất quán qua cả ba lần chạy. Khuyến nghị tạm: hỏi về vị trí/hướng chỉ bằng ảnh, không đưa lời mô tả cũ vào ngữ cảnh. Một dataset, một model: cần kiểm lại.
- **Bộ lọc ngôn ngữ:** sau thay đổi, 0/162 bản ghi mới còn ký tự CJK (trước: 2/548 bản ghi cũ); chưa gặp ca nào cần gọi lại trong các lần chạy này nên **chưa được kích hoạt thật**, chỉ kiểm thử bằng bản giả.
- **Hồi quy `b0g_v1` sau khi gộp mã gọi model:** phủ 118,5/141 (84,0%) so với 120,5/141 trước đó (nằm trong dao động giữa hai lần lặp, 117–121), vẫn báo đúng 4/4 ảnh mờ, 0 lỗi.

**Các câu còn sai (53/59, 6 câu, đọc tay):** `cycle_03` ×2 (sai thứ tự giai đoạn; mô tả chiều quay không nêu "cùng chiều kim đồng hồ"); `line_03` Q3 (trả về giá trị "mười" thay vì khoảng tuần cần tìm: sai thật);
`pie_03` Q1 (đọc nhãn "Trồng lúa" thành "Trống lúa": lỗi dấu); `map_03` Q4 (mơ hồ); `line_01` Q3 đúng về nghĩa nhưng lệch cách chấm.

**Rủi ro quá khớp:** các thay đổi trên được chọn sau khi xem lỗi của chính 59 câu dev này, nên mức tăng có thể lạc quan. Tập test (chưa chạy) mới là phép thử độc lập.

## 5. Cổng kiểm tra chất lượng ảnh (`ai/capture/quality.py`; đo trên 1.200 ảnh huấn luyện tổng hợp)

Ngưỡng: `dark_mean=60`, `blur_laplacian=40`, `overexposed_mean=235`, `overexposed_std=15`, phân tích ở cạnh dài 640. Công cụ: `ai/evaluation/reporting/capture_gate_eval.py`.

| Nhãn thật | Số ảnh | Cổng báo `dark` | `blur` | `glare` | Cho qua | Bắt đúng |
|---|---|---|---|---|---|---|
| blur | 21 | 0 | 21 | 0 | 0 | 21/21 (100%) |
| dark | 33 | 33 | 0 | 0 | 0 | 33/33 (100%) |
| glare | 27 | 0 | 0 | 10 | 17 | 10/27 (37%) |
| cropped_* (4 loại) | 74 | 0 | 0 | 0 | 74 | 0/74 (không bắt, theo thiết kế) |
| ok | 683 | 0 | 0 | 0 | 683 | 683/683 (100%) |
| ok_mild | 362 | 0 | 0 | 0 | 362 | 362/362 (100%) |

**Báo nhầm trên ảnh đạt: 0/1045.** Lỗi cắt mép và phần lớn chói che một phần phụ thuộc nội dung nên giao cho VLM (`b0g_v1`). Giới hạn: lỗi do bộ sinh tạo rất rõ rệt; ngưỡng **chưa hiệu chỉnh trên ảnh chụp thật** (cổng chưa chạy trên trang SGK ở mục 6).

## 6. Kiểm tra trên 32 trang SGK thật (ViSGKCap, tập test, 2026-11-18)

32 trang chọn xác định (mỗi 4 trang theo id, Toán 7 / Tiếng Việt 8 / Tự nhiên và Xã hội 11 / Đạo đức 6; lớp 1–3), ảnh 1700×2200 hoặc nhỏ hơn, prompt `b0g_v1`, `max_tokens` 800. Các trang đều **sạch, nguyên vẹn**.

| Chỉ tiêu | Kết quả |
|---|---|
| Báo "không đọc được" (báo nhầm) | **5/32 (15,6%)**: lý do model nêu: "bị cắt mất phần bên phải/dưới", "bị mờ", "bị che khuất" |
| Bị cắt cụt (`partial`, hết 800 token) | 3/32 |
| Đọc bình thường (`ok`) | 24/32 |
| Thời gian mỗi trang | 14,6 s (≈ 2.950 token vào) |
| Câu trích dẫn trong chú thích ViSGKCap xuất hiện trong mô tả | 131/395 (33%): Toán 57%, Tiếng Việt 23%, Tự nhiên và Xã hội 19%, Đạo đức 12% |

**Cách đọc:** chỉ số trích dẫn là từ khóa rất thô và **đánh giá thấp** (ví dụ trang Toán 72: chú thích viết "43 x 2", model viết "43 × 2" nên bị tính sai dù đúng; nhưng model cũng nói "bốn chú thỏ" khi có năm và đặt sai vị trí vài phép tính). Chú thích của ViSGKCap do máy sinh, chưa phải ground truth;
trên hai trang đã xem bằng mắt, chữ trên trang được chép đúng gần như hoàn toàn, còn mô tả cảnh có lỗi nhỏ (gọi học sinh là "người lớn"). Hệ quả: cần **hiệu chỉnh cổng "không đọc được" trên ảnh thật** (yêu cầu bằng chứng cụ thể trước khi từ chối, kiểm tra thêm cổng ảnh) rồi đo lại; chưa kiểm tra mờ nhẹ, chói và ảnh chụp bằng điện thoại.

## 7. Tái lập

`ai/evaluation/runner/survey_lmstudio.py --prompt b0g_v1`, `run_qa_dev.py`, `reporting/survey_report.py`, `reporting/capture_gate_eval.py`; bản ghi ở `evaluation/records_survey__*` và `records_qa__*` (cục bộ, không có trong git).

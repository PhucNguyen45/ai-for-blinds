# So sánh phương pháp (B0, B0e, B1) và model trên tập dev

> **Trạng thái:** thăm dò. **Ngày:** 2026-11-17 · **Cập nhật:** 2026-11-17 · **Mảng:** A
> **Kết luận ngắn:** trên 22 ảnh dev tổng hợp, `qwen3-vl-4b` chạy cục bộ (miễn phí) đạt 123/141 mệnh đề critical, ngang `gemini-3.1-flash-lite` và hơn nemotron (106); B1 giúp bảng với nemotron
> nhưng không giúp model 4B. Một lần chạy mỗi ảnh, chỉ số từ khóa thô, tập test chưa chạy: **không đủ để kết luận model hay phương pháp nào tốt hơn**.
> (Báo cáo này gộp ba báo cáo cùng ngày: B0 trên nemotron, so sánh B0/B0e/B1, so sánh model miễn phí.)
> **Cập nhật 2026-11-26:** bộ chấm `proposition_check.py` đã sửa (số "8 phẩy 5" và nhãn "Thứ Hai" ↔ "Thứ 2"). Chấm lại Qwen B0e 3 lần lặp: vẫn 123/141 mỗi lần, nên các số trong báo cáo này không đổi. Các số của nemotron và Gemini chưa chấm lại; có thể thay đổi nhẹ nếu bản ghi có các dạng viết trên.

## 1. Điều kiện

Benchmark v0.2.0, tập dev (22 ảnh tổng hợp: 20 đọc được, 2 `_unreadable`; hai mẫu legacy đã chạy ngày 2026-10-24 không chạy lại). temperature 0,2, reasoning tắt, 1 lần chạy mỗi ảnh. Prompt B0e và B1 được đóng băng trước khi chạy, không chỉnh sau khi xem kết quả.

| Điều kiện | Mô tả | Prompt | Request/ảnh |
|---|---|---|---|
| **B0** | Diễn giải trực tiếp, max_tokens 600 | `b0_v1` | 1 |
| **B0e** | B0 + một dòng "nêu đủ mọi nhãn và giá trị số của từng cột, điểm, phần hoặc ô"; **đối chứng** thêm *sau khi* thấy B1 cải thiện bảng, để tách tác động của "nêu đủ giá trị" khỏi "trích xuất có cấu trúc" | `b0e_v1` | 1 |
| **B1** | Bước 1: ảnh → JSON dữ kiện; bước 2: JSON → diễn giải (không gửi lại ảnh) | `b1_extract_v1`, `b1_describe_v1` | 2 |

| Model | Nhà cung cấp | Điều kiện đã chạy | Ảnh có kết quả |
|---|---|---|---|
| `nvidia/nemotron-3.5-super-vl:free` | OpenRouter | B0, B0e, B1 | 22/22 (độ trễ B0 2,6–5 s) |
| `gemini-3.1-flash-lite` | Google AI Studio (gói miễn phí) | B0e | 22/22 |
| `qwen/qwen3-vl-4b` | LM Studio cục bộ, RTX 2070 Max-Q 8 GB | B0e, B1 | 22/22 (B1: 2 lỗi `invalid_output`); trung vị B0e 6,3 s, B1 6,8 s |
| `gemini-3.8-flash` | Google | B0e | 19/22: **không dùng để so** (5 RPM / 20 RPD, bản ghi lỗi đã xóa để chạy lại sau) |
| `gemma-4-31b-it:free` | OpenRouter | B0e | 0/22: 429 liên tục |

## 2. Kết quả: mệnh đề `critical` được phủ

Chỉ số từ khóa chặt (`ai/evaluation/reporting/proposition_check.py`): chỉ kiểm tra số/tên có xuất hiện trong câu trả lời; **không đo độ đúng, không đo bịa, không thay rubric_v1**. 20 ảnh đọc được, 141 mệnh đề.

| Loại | Số mệnh đề | nemotron B0 | nemotron B0e | nemotron B1 | gemini-3.1-flash-lite B0e | **qwen3-vl-4b B0e** | qwen3-vl-4b B1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| bar_chart | 27 | 27 | 26 | 27 | 27 | 27 | 26 |
| line_chart | 19 | 17 | 17 | 17 | 17 | 17 | 10 |
| pie_chart | 12 | 8 | 10 | 8 | 12 | 12 | 9 |
| table | 33 | 20 | 23 | **33** | 33 | 33 | 33 |
| flow_diagram | 13 | 11 | 13 | 12 | 13 | 13 | 7 |
| cycle_diagram | 13 | 3 | 5 | 6 | 9 | 9 | 0* |
| geometry | 12 | 10 | 11 | 10 | 10 | 10 | 6 |
| schematic_map | 12 | 2 | 1 | 2 | 2 | 2 | 1 |
| **Tổng** | **141** | 98 (70%) | 106 (75%) | 115 (82%) | **123 (87%)** | **123 (87%)** | 92 (65%) |

\* Hai ảnh sơ đồ vòng bị `invalid_output` (JSON hỏng) nên tính 0; khôi phục offline bằng bộ phân tích mới vẫn còn cạnh đọc sai, nên không coi là chênh lệch do lỗi cú pháp thuần túy.

Chi phí (trung vị, nemotron): B0e ≈ 3,1 s và 1,35 nghìn token/ảnh; B1 ≈ 7,3 s và 2,16 nghìn token/ảnh (≈ 2,3 lần độ trễ).
Với B0 trên nemotron, khi bỏ qua dấu: pie_chart 12/12 (so với 8/12 chặt), flow_diagram 13/13, cycle_diagram 6/13: phần lớn khác biệt là sai dấu/chính tả nhãn.

## 3. Phát hiện (cần chấm tay và lặp lại trước khi coi là kết luận)

1. **`qwen3-vl-4b` cục bộ ngang `gemini-3.1-flash-lite` (123/141) và hơn nemotron (106/141)** ở B0e, cùng điều kiện (n = 1, chỉ số thô): model 4B miễn phí, trung vị ≈ 6 s mỗi ảnh; ứng viên baseline hợp lý cho hướng tự triển khai. Điểm bằng nhau nằm trong nhiễu một lần chạy.
2. **Sai dấu/chính tả khi chép nhãn là đặc trưng của model**: nemotron ("Trống lúa", "Rau máu", "Thủ gom rác", "khu phó", "hướng Bác") còn Qwen3-VL-4B và Gemini gần như hết (pie 12/12). Dạng lỗi này đổi nghĩa từ khóa học liệu; cần chỉ số CER/WER cho vùng chữ.
3. **Bảng:** nemotron B0/B0e đọc thiếu (`table_03` chỉ mô tả cấu trúc), B1 đọc đủ (33/33); nhưng B0e của qwen và gemini cũng đạt 33/33 không cần hai bước. Với chỉ 2 bảng, đây là **một quan sát**, chưa phải xu hướng.
4. **B1 không tốt hơn B0e với model nhỏ, có thể kém hơn:** bước trích xuất của 4B bỏ sót dữ kiện (`line_01` chỉ 1/6 điểm) và bước diễn giải **không nhìn lại ảnh** nên không bù được (lan truyền lỗi). Một phần cải thiện của B1 với nemotron là do prompt (B0e: 98 → 106; B1 vượt B0e: 106 → 115), chưa tách hết vì B1 có hai prompt riêng.
5. **Bịa thành phần ở sơ đồ vòng:** `cycle_03` thêm giai đoạn "Hạt mọc" không có trong ảnh và bỏ "Hạt mới"; B1 vẫn mắc và lỗi nằm ngay trong `facts` (một bước xác minh B2 đối chiếu `facts` với ảnh có thể bắt được).
6. **Bản đồ ≈ 2/12 ở mọi điều kiện:** mệnh đề ground truth viết theo hướng tương đối so với Trường học còn model nêu vị trí tuyệt đối; chỉ số **đánh giá thấp**. Không sửa ground truth sau khi xem kết quả (cân nhắc v0.3).
7. **Ảnh không đọc được:** B0/B0e (mọi model) **nói** trong văn bản là ảnh mờ nhưng vẫn trả `status="ok"`; chỉ B1 trả `status="unreadable"` có cấu trúc (2/2). Lợi ích về **hợp đồng**, chưa phải độ chính xác; model vẫn có thể bịa chi tiết ("năm ô" khi thực tế 4).
8. **Lỗi định dạng của model nhỏ:** nháy kép không escape trong JSON (2/22), lẫn nhãn kỹ thuật vào diễn giải, nhầm `image_type`; đã thêm bộ khôi phục JSON và đánh dấu trong `uncertainties`.
9. **Giới hạn gói miễn phí:** Google `gemini-3.8-flash` (5 RPM, 250K TPM, 20 RPD) không đủ cho 22 ảnh/ngày; `gemini-3.1-flash-lite` chạy liền; OpenRouter Gemma bị 429.

## 4. Chạy lặp 3 lần: `qwen3-vl-4b` B0e cục bộ (22 ảnh × 3)

Công cụ: `run_b1_dev.py --reps 3` và `repeat_stats.py`; bản ghi ở `evaluation/records_b0e__lmstudio__qwen-qwen3-vl-4b__reps/`.

| Chỉ số | Kết quả |
|---|---|
| Tổng mệnh đề critical phủ được theo từng lần | 123, 123, 123 / 141 (87,2%) |
| Độ lệch chuẩn giữa các lần | **0,0** |
| Ảnh ổn định hoàn toàn theo chỉ số | 20/20 |
| Lần chạy đơn trước đó | 123/141 (trùng) |
| Câu trả lời giống hệt từng ký tự giữa 3 lần | **0/22** (độ trễ trung vị 6,6 / 5,4 / 6,4 s) |

Model **diễn đạt khác nhau** mỗi lần nhưng luôn nêu cùng tập dữ kiện mà chỉ số kiểm tra. Độ lệch chuẩn 0 là **hiệu ứng trần** của chỉ số (không bắt bịa thêm, thứ tự, chất lượng diễn đạt), không phải model hoàn hảo; việc hai model cùng đạt 123 nhiều khả năng cũng do đó. 18 mệnh đề thiếu là thiếu có hệ thống (bản đồ, sơ đồ vòng, hình học), không phải nhiễu.

## 5. Giới hạn

- Một lần chạy mỗi ảnh (trừ mục 4), ảnh tổng hợp sạch, chỉ số từ khóa phạt cả cách diễn đạt khác và không bắt bịa thêm; chưa chấm rubric_v1 bằng người; ground truth do mã sinh, chưa có người thứ hai rà soát.
- B0 chạy sớm hơn B0e/B1 vài giờ; các model chạy ở thời điểm và nhà cung cấp khác nhau (gói miễn phí có thể thay đổi).
- Hệ quả: cần chỉ số nhạy hơn (rubric bằng người, đếm mệnh đề thừa/bịa, đúng chiều quan hệ) trước khi so sánh có ý nghĩa.

## 6. Việc tiếp theo

1. Chấm tay rubric_v1 các mẫu lỗi (`cycle_03`, `pie_03`, `table_03`, `map_01`) cho cả ba điều kiện.
2. Thử bước xác minh B2 (đối chiếu `facts` với ảnh) nhắm vào lỗi bịa/chép sai.
3. Chạy `gemini-3.8-flash` theo đợt nhỏ (≤ 15 ảnh/ngày) nếu muốn đưa vào so sánh.
4. Chỉ chạy tập test (23 mẫu) sau khi đóng băng prompt, model và rubric.

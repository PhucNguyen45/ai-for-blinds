# Khảo sát Qwen3-VL Q4 (4B và 8B) trên LM Studio, RTX 2070 Max-Q 8 GB

> **Trạng thái:** thăm dò. **Ngày:** 2026-11-17 · **Cập nhật:** 2026-11-18 · **Mảng:** A
> **Kết luận ngắn:** 4B Q4 chạy tốt cục bộ (7–9 s mỗi mô tả, phủ 83% → 86% → 87% khi phóng ảnh x0,5 → x1 → x1,5, chênh x1/x1,5 nằm trong dao động); 8B Q4 **không nạp đủ lên GPU 8 GB** nên chậm (20–230 s) và chưa thấy hơn 4B. Bản đồ sơ đồ chỉ 17% ở mọi mức.
> Phần A: **4B** (đầy đủ, 132 request). Phần B: **8B** (dở dang, 63/132 request, một lần lặp), có so sánh cùng ảnh.

## A. `qwen/qwen3-vl-4b` — đợt `baseline_q4_ctx16k_p1`

- Phương pháp: B0e (b0e_v1); benchmark v0.2.0 (tập dev); mã git `47aaa02`
- Bắt đầu 2026-11-17T14:39:07.059176+00:00; scales [0.5, 1.0, 1.5]; số lần lặp 2
- Model: 4B Q4_K_M, 3.33 GB, context tối đa 262144
- Cấu hình đang nạp (API LM Studio): context_length=16384, parallel=1, flash_attention=True, eval_batch_size=2048, physical_batch_size=512, offload_kv_cache_to_gpu=True
- VRAM trước khi chạy: 7250/8192 MiB
- Ghi chú: Q4_K_M, ctx 16384, parallel 1, FA bat; GPU offload/anh toi da: theo giao dien (khong doc duoc qua API)


### Nhận xét (đọc cùng các bảng bên dưới)

**Điều quan sát được**
1. **Phóng ảnh có xu hướng tăng phủ**: 83,3% (x0,5) → 86,2% (x1) → 87,2% (x1,5). Chênh x1 so với x1,5 (+1,5 điểm) **nằm trong dao động giữa hai lần lặp** của chính x1 (120 đến 123 trên 141), nên chưa đủ kết luận. Chênh x0,5 so với x1 rõ hơn nhưng vẫn chỉ 2 lần lặp.
2. **Khác biệt dồn vào vài ảnh**: `cycle_03`, `cycle_01` (sơ đồ vòng) và `bar_03` kém hẳn ở x0,5; `pie_03` dao động theo cả hai chiều. Biểu đồ cột, bảng và sơ đồ khối gần như đã chạm trần ở mọi scale.
3. **Bản đồ sơ đồ (`schematic_map`) chỉ phủ 16,7% ở cả ba scale**: phóng ảnh không cứu được. Đây là giới hạn **nhận thức/hiểu bố cục**, không phải do thiếu chi tiết ảnh. Cần xem tay `map_01`, `map_03` và là ứng viên cho fine-tune.
4. **Ảnh không đọc được: model KHÔNG báo "unreadable" ở lần nào (0/4 ở mỗi scale)**. Lưu ý: prompt `b0e_v1` **không** hướng dẫn model từ chối khi ảnh quá mờ, nên đây là đặc điểm của cặp (prompt, model), không kết luận được model "không biết" nói không đọc được. Mô tả sinh ra ở hai mẫu này chỉ nêu loại hình, không bịa số, nhưng vẫn mang `status=ok`.
5. **Hai lần bị cắt (`finish_reason=length`, 600 token) đều ở x0,5** (`line_01`, `map_03`); ở x1 và x1,5 không có. Số token ra TB giảm khi ảnh lớn hơn (413 → 395 → 379).
6. **VRAM đỉnh 7452 MiB / 8192 MiB (khoảng 7,3 / 8,0 GiB) ở cả ba scale**: scale không làm tăng đỉnh VRAM (bộ nhớ KV đã cấp trước ở ctx 16384). Còn dư khoảng 740 MiB, **sát giới hạn**.
7. **Tốc độ**: 7,2 s (x0,5) → 7,6 s (x1) → 9,1 s (x1,5) mỗi mô tả; sinh chữ khoảng 52 token/giây, xử lý prompt khoảng 630 đến 760 token/giây (log LM Studio).

**Không kết luận được**
- Chưa biết phóng ảnh có giúp trên **ảnh thật** hay không: phóng bằng nội suy không thêm chi tiết, chỉ tăng token thị giác.
- Chỉ số từ khóa không đo bịa; chạm trần ở nhiều loại hình.
- Chưa so sánh với Q8, 8B, hay các cấu hình lấy mẫu.

**Việc nên làm tiếp (đề xuất)**
- Xem tay các mẫu thấp: `cycle_03`, `cycle_01`, `map_01`, `map_03`, `pie_03`.
- Thêm hướng dẫn "ảnh mờ/thiếu thì nói rõ và đề nghị chụp lại" vào prompt, đo lại tỉ lệ báo unreadable (đúng với yêu cầu của đề tài).
- Nâng `max_tokens` lên 800 và lặp ≥3 lần để thu hẹp khoảng dao động.
- Thử x1,5 so với x2 trên ảnh render gốc ở độ phân giải cao, thay vì phóng nội suy.

### A1. Mức phủ mệnh đề critical theo độ phóng ảnh

| Scale | Cỡ ảnh | Phủ trung bình | Từng lần lặp | Token vào (TB) | Token ra (TB) | Thời gian TB / p95 (s) | Lỗi |
|---|---|---|---|---|---|---|---|
| x0.5 | 550×360 | 117.5/141 (83.3%) | r01=119, r02=116 | 444 | 413 | 7.2 / 10.0 | 0 |
| x1 | 1100×720 | 121.5/141 (86.2%) | r01=123, r02=120 | 1005 | 395 | 7.6 / 10.3 | 0 |
| x1.5 | 1650×1080 | 123.0/141 (87.2%) | r01=123, r02=123 | 2025 | 379 | 9.1 / 11.7 | 0 |

Chỉ số từ khóa thô, chạm trần và không đo độ bịa; chênh lệch nhỏ giữa các hàng không có ý nghĩa nếu nằm trong độ lệch giữa các lần lặp của cùng một hàng.

### A2. Theo loại hình (phủ trung bình, cộng dồn các lần lặp)

| Loại hình | x0.5 | x1 | x1.5 |
|---|---|---|---|
| bar_chart | 50/54 (92.6%) | 54/54 (100.0%) | 54/54 (100.0%) |
| cycle_diagram | 12/26 (46.2%) | 18/26 (69.2%) | 18/26 (69.2%) |
| flow_diagram | 26/26 (100.0%) | 26/26 (100.0%) | 26/26 (100.0%) |
| geometry | 20/24 (83.3%) | 20/24 (83.3%) | 20/24 (83.3%) |
| line_chart | 34/38 (89.5%) | 34/38 (89.5%) | 34/38 (89.5%) |
| pie_chart | 23/24 (95.8%) | 21/24 (87.5%) | 24/24 (100.0%) |
| schematic_map | 4/24 (16.7%) | 4/24 (16.7%) | 4/24 (16.7%) |
| table | 66/66 (100.0%) | 66/66 (100.0%) | 66/66 (100.0%) |

### A3. Ổn định, kết thúc, VRAM, ảnh không đọc được

| Scale | finish_reason | Lỗi theo mã | Ảnh không đọc được (báo / bỏ sót) | VRAM tối đa (MiB) |
|---|---|---|---|---|
| x0.5 | {'stop': 42, 'length': 2} | - | 0 / 4 | 7452 |
| x1 | {'stop': 44} | - | 0 / 4 | 7447 |
| x1.5 | {'stop': 44} | - | 0 / 4 | 7454 |

### A4. Ảnh dao động hoặc khác nhau nhiều giữa các scale

- `cycle_03` (cycle_diagram, 7 mệnh đề): x0.5=3.0, x1=5.0, x1.5=5.0
- `bar_03` (bar_chart, 7 mệnh đề): x0.5=5.0, x1=7.0, x1.5=7.0
- `pie_03` (pie_chart, 6 mệnh đề): x0.5=5.5, x1=4.5, x1.5=6.0
- `cycle_01` (cycle_diagram, 6 mệnh đề): x0.5=3.0, x1=4.0, x1.5=4.0

### A5. Giới hạn

- Phóng to bằng nội suy (LANCZOS) không thêm chi tiết thật; nó chỉ tăng số token thị giác. Ảnh chụp thật ở độ phân giải cao có thể cho kết quả khác. Muốn tách hai yếu tố cần render lại benchmark ở độ phân giải cao.
- Số lần lặp nhỏ, một model, tập dev tổng hợp: kết quả thăm dò, không khái quát.
- Temperature 0 không cho kết quả giống hệt giữa hai lần (đã quan sát), nên mọi so sánh cần khoảng dao động.

---

## B. `qwen/qwen3-vl-8b` — đợt `baseline_8b_q4_ctx16k_p1`

- Phương pháp: B0e (b0e_v1); benchmark v0.2.0 (tập dev); mã git `47aaa02`
- Bắt đầu 2026-11-17T15:12:22.095020+00:00; scales [0.5, 1.0, 1.5]; số lần lặp 2
- Model: 8B Q4_K_M, 6.19 GB, context tối đa 262144
- Cấu hình đang nạp (API LM Studio): context_length=16384, parallel=1, flash_attention=True, eval_batch_size=2048, physical_batch_size=512, offload_kv_cache_to_gpu=True
- VRAM trước khi chạy: 7839/8192 MiB
- Ghi chú: 8B Q4_K_M, ctx 16384, parallel 1, FA bat; VRAM nhan thay 7840/8192 MiB luc nhan roi (chi con ~350 MiB)


### Nhận xét về 8B (dở dang)

**Dữ liệu:** 63 trong 132 request đã chạy, gần hết lần lặp 1 (thiếu 3 ảnh cuối ở x1,5, chưa có lần lặp 2). Phúc dừng vì quá chậm. Hai request ở x0,5 (`table_01`, `table_03`) **hết thời gian chờ 300 giây** và không được tính vào độ phủ.

**Tốc độ và bộ nhớ (kết quả chính, không còn nghi vấn):**
- Một mô tả mất trung bình **61 s (x0,5), 97 s (x1), 118 s (x1,5)**, p95 tới 160 s; bản 4B chỉ 7 đến 9 s. Tốc độ sinh chữ khoảng 14 token/giây ở request đầu, rồi 3 đến 10 token/giây (4B: khoảng 52).
- **Chậm ngay từ đầu, không chỉ từ request thứ 60** như quan sát ban đầu; sau đó còn giảm thêm.
- **VRAM đã 7839 / 8192 MiB (khoảng 7,7 / 8,0 GiB) ngay khi nạp xong, đỉnh 7963 MiB**: gần như không còn chỗ cho bộ đệm tính toán của ảnh. Nguyên nhân chậm được làm rõ ở mục "Chẩn đoán" ngay bên dưới.
- Kết luận thực tế: **8B Q4 ở cấu hình này không dùng được** cho đề tài trên máy này (ứng dụng đọc ra giọng nói không thể chờ hàng chục giây đến vài phút, và có timeout).

**Chất lượng (chỉ số từ khóa thô, một lần lặp, cùng ảnh với 4B):** 8B hơn nhẹ ở x0,5 (91 so với 86 trên 108) và x1 (125 so với 123 trên 141), bằng nhau ở x1,5 (120 so với 120). Khác biệt dồn vào vài ảnh (`bar_03`, `cycle_03`, `geo_06`, `map_03`), và chênh lệch nằm trong dao động giữa các lần lặp đã thấy ở 4B (khoảng 3 điểm). **Không kết luận được 8B tốt hơn.** Bản đồ sơ đồ vẫn thấp (16,7% đến 33,3%), nên kích thước model không giải quyết được giới hạn này.

**Ảnh không đọc được:** 8B cũng không báo "unreadable" lần nào (0/2 ở x0,5 và x1; prompt `b0e_v1` không hướng dẫn việc này).

**Hệ quả cho đề tài:** giữ **4B** làm baseline và đối tượng fine-tune. Nếu muốn giữ 8B làm ứng viên thì cần chạy lại đủ 22 ảnh × nhiều lần lặp ở cấu hình đã chẩn đoán (ctx 8192), vì dữ liệu hiện có chỉ là một lần lặp ở cấu hình chậm hơn.


### Chẩn đoán nguyên nhân chậm (2026-11-18, sau khi nạp lại 8B với context 8192)

**Phát hiện từ log LM Studio:** model **không được nạp đủ lên GPU**. Log ghi `n_gpu_layers already set by user to <N>`: lần chạy 132 request dùng **32 lớp** trên GPU (và 30 lớp ở lần nạp thử trước đó), trong khi model có **36 lớp**. Các lớp còn lại chạy trên **CPU với 4 luồng** (`n_threads = 4`), nên mỗi token phải chờ phần CPU. Lần nạp lại (context 8192) dùng **34 lớp**. LM Studio có giới hạn VRAM nghiêm ngặt nên tự giảm số lớp cho vừa 8 GB.

**Đo lại (ctx 8192, parallel 1, 34 lớp trên GPU, 3 ảnh dev ở x1, tổng thời gian request):**

| Ảnh | Thời gian | Token ra | Tốc độ tổng (gồm xử lý ảnh) |
|---|---|---|---|
| `bar_01` | 26,3 s | 542 | 20,6 token/s |
| `table_03` | 31,3 s | 481 | 15,4 token/s |
| `cycle_03` | 21,1 s | 399 | 18,9 token/s |

- So với lần chạy ctx 16384 (97 s trung bình ở x1), nhanh hơn khoảng **3 đến 4 lần**, nhưng vẫn **chậm hơn 4B khoảng 3 lần** (4B: 7 đến 9 s mỗi mô tả).
- **Không phải throttling nhiệt:** nhiệt độ GPU 52 đến 58 °C, xung nhịp 1470 đến 1815 MHz (tối đa 2100). Lý do giới hạn là `0x4` (SW power cap, giới hạn công suất của dòng Max-Q), không phải nhiệt. GPU chỉ dùng khoảng 45 đến 86%, phù hợp với việc đang chờ phần CPU.
- **Hạn chế của chẩn đoán:** đổi hai thứ cùng lúc (context 16384 → 8192 và 32 → 34 lớp trên GPU) nên chưa tách được đóng góp riêng của từng thứ; chỉ 3 request, một lần lặp; chưa chạy lại 22 ảnh.
- **Kết luận:** nguyên nhân chính khả dĩ nhất là **offload GPU từng phần** (một số lớp chạy trên CPU) do 8B Q4 cộng phần thị giác không vừa 8 GB. 8B vẫn không phù hợp làm model chạy hằng ngày trên máy này.

### Các bảng chi tiết (8B)

### B1. Mức phủ mệnh đề critical theo độ phóng ảnh

| Scale | Cỡ ảnh | Phủ trung bình | Từng lần lặp | Token vào (TB) | Token ra (TB) | Thời gian TB / p95 (s) | Lỗi |
|---|---|---|---|---|---|---|---|
| x0.5 | 550×360 | 91.0/108 (84.3%) | r01=91/108 | 444 | 418 | 60.9 / 121.3 | 2 |
| x1 | 1100×720 | 125.0/141 (88.7%) | r01=125/141 | 1005 | 444 | 96.6 / 161.5 | 0 |
| x1.5 | 1650×1080 | 120.0/138 (87.0%) | r01=120/138 | 2025 | 435 | 117.8 / 148.5 | 0 |

Chỉ số từ khóa thô, chạm trần và không đo độ bịa; chênh lệch nhỏ giữa các hàng không có ý nghĩa nếu nằm trong độ lệch giữa các lần lặp của cùng một hàng.

### B2. Theo loại hình (phủ trung bình, cộng dồn các lần lặp)

| Loại hình | x0.5 | x1 | x1.5 |
|---|---|---|---|
| bar_chart | 27/27 (100.0%) | 27/27 (100.0%) | 27/27 (100.0%) |
| cycle_diagram | 9/13 (69.2%) | 9/13 (69.2%) | 9/13 (69.2%) |
| flow_diagram | 13/13 (100.0%) | 13/13 (100.0%) | 13/13 (100.0%) |
| geometry | 11/12 (91.7%) | 10/12 (83.3%) | 7/9 (77.8%) |
| line_chart | 17/19 (89.5%) | 17/19 (89.5%) | 17/19 (89.5%) |
| pie_chart | 12/12 (100.0%) | 12/12 (100.0%) | 12/12 (100.0%) |
| schematic_map | 2/12 (16.7%) | 4/12 (33.3%) | 2/12 (16.7%) |
| table | - | 33/33 (100.0%) | 33/33 (100.0%) |

### B3. Ổn định, kết thúc, VRAM, ảnh không đọc được

| Scale | finish_reason | Lỗi theo mã | Ảnh không đọc được (báo / bỏ sót) | VRAM tối đa (MiB) |
|---|---|---|---|---|
| x0.5 | {'stop': 20, '-': 2} | {'timeout': 2} | 0 / 2 | 7963 |
| x1 | {'stop': 20, 'length': 2} | - | 0 / 2 | 7945 |
| x1.5 | {'stop': 19} | - | 0 / 0 | 7875 |

### B4. Ảnh dao động hoặc khác nhau nhiều giữa các scale

- `map_03` (schematic_map, 6 mệnh đề): x0.5=1.0, x1=3.0, x1.5=1.0
- `geo_06` (geometry, 3 mệnh đề): x0.5=3.0, x1=2.0, x1.5=2.0

### So khớp cùng ảnh: `baseline_8b_q4_ctx16k_p1` (qwen/qwen3-vl-8b) và `baseline_q4_ctx16k_p1` (qwen/qwen3-vl-4b), chỉ lần lặp 1

Chỉ tính ảnh có kết quả hợp lệ ở cả hai đợt (loại bản ghi lỗi). Một lần lặp: không thấy được dao động.

| Scale | Số ảnh | Mệnh đề | qwen/qwen3-vl-8b | qwen/qwen3-vl-4b | Ảnh khác nhau (đợt này vs đợt so sánh) |
|---|---|---|---|---|---|
| x0.5 | 18 | 108 | 91 | 86 | `bar_03` 7 vs 5, `cycle_03` 5 vs 3, `geo_06` 3 vs 2 |
| x1 | 20 | 141 | 125 | 123 | `map_03` 3 vs 1 |
| x1.5 | 19 | 138 | 120 | 120 | - |

### B5. Giới hạn

- Phóng to bằng nội suy (LANCZOS) không thêm chi tiết thật; nó chỉ tăng số token thị giác. Ảnh chụp thật ở độ phân giải cao có thể cho kết quả khác. Muốn tách hai yếu tố cần render lại benchmark ở độ phân giải cao.
- Số lần lặp nhỏ, một model, tập dev tổng hợp: kết quả thăm dò, không khái quát.
- Temperature 0 không cho kết quả giống hệt giữa hai lần (đã quan sát), nên mọi so sánh cần khoảng dao động.


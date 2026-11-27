# Benchmark v0.2.0 — diễn giải học liệu trực quan cho học sinh khiếm thị

> **Dữ liệu KHÔNG nằm trong repo.** Toàn bộ ảnh, ground truth, `manifest.json`, ảnh ứng viên và ảnh SGK chỉ giữ ở máy tác giả
> (`.gitignore`) để dùng fine-tune và giữ tập test riêng tư; thứ đưa ra demo là **model đã fine-tune**, không phải dữ liệu.
> Chỉ file mô tả này được theo dõi. Phần **tổng hợp** tái tạo được **giống hệt từng byte** từ mã:
> `cd ai && uv run python evaluation/generators/generate_benchmark_v02.py` (hai mẫu legacy `chart_01`, `chart_02_no_labels`
> do bộ sinh v0.1 tạo và cần được giữ từ bản sao cũ). Ảnh ứng viên tải lại bằng `fetch_commons_candidates.py`; ảnh SGK không tái tạo được.

> **Trạng thái:** bản thí điểm gồm **mẫu tổng hợp** để kiểm tra pipeline và so sánh sơ bộ.
> Chưa phải benchmark đại diện cho học liệu thực tế. Đã có kết quả **thăm dò trên tập dev**
> (xem `ai/evaluation/reports/`); tập test chưa chạy.

> **27/11/2026:** câu hỏi loại `computation` và mệnh đề `inference` (tổng, chênh lệch, cạnh huyền, diện tích) cần đối chiếu với [Quy cách đầu ra](../../ai/README.md#quy-cách-đầu-ra-chốt-ngày-27112026): chênh lệch hai cột được phép khi không trùng bài tập trên trang (quy tắc 12), các phép tính khác tạm thời không được. Khi báo điểm, tách riêng hai nhóm này. Ground truth không bị sửa. Bộ này chưa đo việc tuân thủ "không giải bài tập".

## Thành phần

| Nhóm | Số mẫu | Loại |
|---|---:|---|
| chart | 20 | bar_chart (9), line_chart (7), pie_chart (4) |
| table | 6 | table |
| figure | 17 | flow_diagram (6), cycle_diagram (4), geometry (7) |
| map | 4 | schematic_map (sơ đồ khu phố, hướng Bắc ở trên) |
| text | 0 | **chưa có** — cần trang văn bản/học liệu thật |

Trong 47 mẫu: 2 mẫu legacy v0.1 (`chart_01`, `chart_02_no_labels`), 38 mẫu gốc, 4 biến thể
`*_hard` (xoay, giảm sáng, mờ, nhiễu; vẫn đọc được) và 3 biến thể `*_unreadable`
(độ phân giải cực thấp; kỳ vọng hệ thống **từ chối hợp lý**, không bịa).

## Cấu trúc

- `manifest.json` — danh sách mẫu, sha256 ảnh và ground truth, `split`, `difficulty`,
  `expected_status`, `license`, `generator`, `derived_from`.
- `synthetic/<id>.png` và `synthetic/<id>_truth.json`.
- Ground truth `truth_v0.2`: `propositions` (kind = `value | relation | comparison |
  structure | inference`; `critical` đánh dấu dữ kiện bắt buộc phải có),
  `questions` (lookup / comparison / computation / relation / refusal), `data` (dữ liệu gốc
  dùng để vẽ ảnh), `expected_status` (`ok` hoặc `unreadable`).
- Mệnh đề `inference` (ví dụ tổng, chênh lệch, cạnh huyền, diện tích) là kết quả suy ra,
  **không** hiển thị trong ảnh: nên chấm riêng với dữ kiện đọc trực tiếp.

## Quy ước sử dụng

1. **dev** (24 mẫu): dùng để thiết kế/chỉnh prompt và rubric. **test** (23 mẫu): không dùng
   để chỉnh prompt hay rubric; chỉ chạy khi đã đóng băng cấu hình.
2. Hai mẫu legacy đã được dùng trong thăm dò và chấm thử → xếp vào **dev**.
3. Biến thể `_hard` / `_unreadable` kế thừa split của ảnh gốc để tránh rò rỉ.
4. Không sửa ground truth sau khi đã xem đầu ra mô hình; nếu phải sửa, tăng phiên bản
   benchmark và ghi lý do.
5. Ảnh tổng hợp do mã sinh (seed cố định), giấy phép CC0, không dùng tư liệu bên ngoài.

## Tái tạo và kiểm tra (chạy trong `ai/`)

```bash
uv run python evaluation/generators/generate_benchmark_v02.py   # sinh lại, giữ mục legacy
uv run python evaluation/generators/validate_benchmark.py       # kiểm hash, schema, split
```

## Giới hạn đã biết

- Ảnh sạch, font cố định, bố cục đơn giản → dễ hơn học liệu thật. Kết quả tốt trên bộ này
  **không** suy ra được chất lượng trên SGK/ảnh chụp.
- Ngôn ngữ và chủ đề do người viết mã chọn; chưa có thẩm định của giáo viên.
- Chưa có người thứ hai rà soát ground truth (dù được sinh từ dữ liệu vẽ nên ít sai).
- Chưa có nhóm `text`, ảnh chụp thực tế (nghiêng phối cảnh, bóng), bản đồ thật, hình minh
  họa khoa học thật, và học liệu tiếng Việt thật.
- `line_03_unreadable` vẫn lộ hình dáng đường mờ; chỉ nhãn và số liệu là không đọc được.
- Chưa có hạng mục STT/TTS.

## Việc tiếp theo

Xem mục "Việc tiếp theo" của `README.md` gốc (một danh sách duy nhất); riêng benchmark: người thứ hai rà soát ground truth của ≥ 20% mẫu.

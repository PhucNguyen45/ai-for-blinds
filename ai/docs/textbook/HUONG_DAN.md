# Hướng dẫn thu thập, nạp và gán nhãn ảnh SGK

Dành cho người thu thập dữ liệu (Phúc và người rà soát). Công cụ: `ai/evaluation/generators/ingest_textbook.py`.

## 0. Quy tắc quan trọng nhất: repo này CÔNG KHAI và dữ liệu CHỈ Ở MÁY

SGK có bản quyền nhà xuất bản. Thầy cho phép **dùng** cho nghiên cứu, nhưng điều đó không có nghĩa được **đăng công khai**.
Vì vậy `.gitignore` đã chặn những thứ sau, và bạn **không được ép thêm vào git** (`git add -f`):

| Thứ | Vì sao không đưa lên |
|---|---|
| Ảnh SGK (`raw/`, `images/`) | Bản quyền |
| Ground truth của ảnh SGK (`truth/`) | Là mô tả/chép lại nội dung hình (số liệu, nhãn, chữ) |
| `intake.csv`, `registry.json` | Danh mục sách/trang đã thu thập |
| Đầu ra mô hình trên ảnh SGK (`records*/_restricted/`) | Là bản diễn giải lại nội dung SGK |

Được phép công khai: mã công cụ, tài liệu này, mẫu phiếu `intake_template.csv`, và **số liệu tổng hợp** (điểm, tỷ lệ) trong báo cáo.
Toàn bộ `data/benchmark/` (kể cả `manifest.json`) chỉ ở máy tác giả. Khi trích ví dụ vào báo cáo, chỉ trích ngắn và ghi nguồn
(tên sách, NXB, trang). **Trước mỗi lần commit, chạy `git status` và tự hỏi: "có file nào chứa nội dung SGK không?"**

Bản quyền ảnh Wikimedia/CC trong `candidates/` là chuyện khác (đã có giấy phép tự do và bảng nguồn).

## 1. Thu thập cái gì (mục tiêu ~40–60 hình)

| Loại (`category`) | Môn gợi ý | Số mẫu gợi ý |
|---|---|---:|
| `bar_chart`, `line_chart`, `pie_chart` | Địa lí, Toán, KHTN | 10–12 |
| `table` | Địa lí, Toán, KHTN | 6–8 |
| `map` | Địa lí, Lịch sử và Địa lí | 8–10 |
| `geometry` | Toán | 8–10 |
| `science_figure`, `flow_diagram`, `cycle_diagram` | Sinh học, Vật lí, Hóa học, KHTN, Tin học | 10–12 |
| `text` (trang chữ, công thức) | Ngữ văn, Lịch sử, Toán | 5–8 |

Chọn **nhiều sách và nhiều bài khác nhau** (dev/test được chia **theo sách**, nên ít nhất 4–6 sách để cả hai tập đều có mẫu).
Ưu tiên hình mà thông tin nằm trong **quan hệ, số liệu, thứ tự**, không chỉ là tranh minh họa trang trí.

## 2. Lấy ảnh bằng cách nào

- **SGK điện tử:** NXB Giáo dục Việt Nam cung cấp SGK điện tử miễn phí qua `taphuan.nxbgd.vn` (theo báo chí; trang Hành trang số cũ đã ngừng).
  *Chưa được xác minh trực tiếp.* Bạn mở bằng trình duyệt, **đọc điều khoản sử dụng**, rồi chụp màn hình vùng cần lấy. Không viết
  chương trình tải hàng loạt khi chưa đọc điều khoản.
- **Sách giấy:** chụp bằng điện thoại. Đủ sáng, giữ điện thoại song song với trang, lấy trọn hình và chú thích, không để lọt mặt người.
- Nên có **hai kiểu**: khoảng 2/3 ảnh "sạch" (chụp màn hình/scan) để đo khả năng đọc, và khoảng 1/3 ảnh **chụp thực tế bằng điện thoại**
  (hơi nghiêng, bóng, thiếu sáng nhẹ) để gần với lúc học sinh dùng ứng dụng. Cùng một hình có thể có cả hai bản (hai dòng trong phiếu,
  cùng `book`, `page`, `figure_label`, ghi chú `chụp thực tế`).
- Mỗi ảnh tối thiểu **300 px** cạnh ngắn (khuyến nghị ≥1000 px). Định dạng: png, jpg, jpeg, webp. Mỗi ảnh chứa **một hình** (cắt gọn cả chú thích).

Đặt file vào `data/benchmark/textbook/raw/` (thư mục này không có sẵn: hãy tạo; nằm ngoài git). Quy ước tên gợi ý: `dia8_p023_hinh2.jpg`, `toan9_p101_hinh45_thuc-te.jpg`.

## 3. Điền phiếu nạp `intake.csv`

Sao chép `ai/docs/textbook/intake_template.csv` thành `data/benchmark/textbook/intake.csv` rồi thêm mỗi hình một dòng:

| Cột | Bắt buộc | Ý nghĩa |
|---|:--:|---|
| `file` | ✔ | Tên file trong `raw/` |
| `book` | ✔ | Tên sách, **viết nhất quán** (vd `Địa lí 8`). Dùng để chia dev/test theo sách |
| `publisher` | ✔ | vd `NXB Giáo dục Việt Nam` |
| `series` |  | Bộ sách (Kết nối tri thức, Chân trời sáng tạo, Cánh diều…) |
| `grade` | ✔ | Số 1–12 |
| `subject` | ✔ | vd `Địa lí` |
| `page` |  | Số trang |
| `figure_label` |  | vd `Hình 2.3` |
| `category` | ✔ | `bar_chart`, `line_chart`, `pie_chart`, `table`, `flow_diagram`, `cycle_diagram`, `geometry`, `map`, `science_figure`, `text`, `other` |
| `difficulty` |  | `easy` (ít thành phần, rõ), `medium`, `hard` (dày, nhiều lớp, chữ nhỏ). Để trống = medium |
| `notes` |  | Ghi chú tự do |

Ví dụ:
```
file,book,publisher,series,grade,subject,page,figure_label,category,difficulty,notes
dia8_p023_hinh2.jpg,Địa lí 8,NXB Giáo dục Việt Nam,Kết nối tri thức,8,Địa lí,23,Hình 2,map,medium,
toan9_p101_hinh45.jpg,Toán 9,NXB Giáo dục Việt Nam,Kết nối tri thức,9,Toán,101,Hình 45,geometry,easy,chụp thực tế
```
Lưu file dạng UTF-8 (Excel: "CSV UTF-8").

## 4. Chạy công cụ nạp

Trong thư mục `ai/`:
```bash
uv run python evaluation/generators/ingest_textbook.py
```
- Công cụ kiểm tra từng dòng, in `LỖI dòng N (...)` nếu có (thiếu cột, file không thấy, grade ngoài 1–12, ảnh <300 px…).
  Sửa phiếu rồi chạy lại. Chạy lại nhiều lần an toàn: ảnh đã đăng ký (theo hash) sẽ không bị nạp trùng, id (`tb_001`, `tb_002`…) giữ nguyên.
- Kết quả: ảnh được sao chép vào `images/`, và mỗi ảnh có file ground truth **rỗng** `truth/tb_XXX_truth.json`.

## 5. Gán nhãn ground truth (việc quan trọng nhất, do NGƯỜI làm)

Mở `truth/tb_XXX_truth.json` và điền hai mảng `propositions` và `questions` **chỉ từ những gì nhìn thấy trong ảnh gốc**.
**Không** sao chép đầu ra của VLM (kể cả "để đỡ gõ"): đó làm hỏng phép đo, vì mô hình sẽ được chấm bằng chính câu trả lời của nó.

**Mệnh đề** (`propositions`): mỗi mệnh đề là một dữ kiện kiểm tra được.

| `kind` | Dùng khi | Ví dụ |
|---|---|---|
| `value` | Nhãn, số liệu đọc trực tiếp | `Cột Hà Nội | có giá trị | 8,5 triệu người` |
| `relation` | Quan hệ, mũi tên, thứ tự, vị trí | `Sông A | chảy vào | Hồ B` |
| `comparison` | Lớn nhất, nhỏ nhất, hơn kém | `Giá trị lớn nhất | thuộc về | Tháng 7` |
| `structure` | Loại hình, tiêu đề, chú giải, hướng, cách bố cục | `Chú giải | gồm | ba màu: …` |
| `inference` | Điều **suy ra** (tổng, hiệu, diện tích) không hiện trong ảnh | `Tổng hai cột | bằng | 15` |

- `critical: true` cho dữ kiện **bắt buộc** phải nêu để hiểu hình; `false` cho chi tiết phụ và mọi mệnh đề `inference`.
- Giữ nguyên nhãn **đúng chính tả và dấu tiếng Việt** như trong ảnh.
- Giá trị phải **ước lượng** từ đồ thị (không có nhãn số): ghi rõ trong `object` (vd `khoảng 30, sai số ±2`) và đừng để `critical`.
- Ghi cả điều **không có**: vd `Biểu đồ | không hiển thị | số liệu phần trăm`.
- Với bản đồ nên ghi vị trí **tuyệt đối** (hàng/cột, góc, giáp biển…) lẫn quan hệ tương đối quan trọng.
- Ảnh quá mờ/che khuất không đọc được: đặt `"expected_status": "unreadable"` và ghi mệnh đề `structure` giải thích lý do.

**Câu hỏi** (`questions`, ≥2 mỗi ảnh): `type` ∈ `lookup | comparison | computation | relation | refusal`. Mỗi câu có `answer` ngắn, kiểm chứng được từ ảnh.

Ví dụ hoàn chỉnh (nội dung minh họa tự nghĩ ra, **không phải SGK**):
```json
{
  "schema": "truth_v0.2", "id": "tb_001", "category": "bar_chart", "synthetic": false, "language": "vi",
  "title": "Địa lí 8 — trang 23 Hình 2",
  "expected_status": "ok",
  "ground_truth_status": "verified", "verified_by": "Nguyễn Hoàng Phúc",
  "source": {"book": "Địa lí 8", "publisher": "NXB Giáo dục Việt Nam", "grade": "8", "subject": "Địa lí", "page": "23", "figure_label": "Hình 2"},
  "data": {},
  "propositions": [
    {"id": "P1", "kind": "structure",  "subject": "Tiêu đề", "predicate": "là", "object": "Lượng mưa các tháng", "critical": true},
    {"id": "P2", "kind": "value",      "subject": "Tháng 7", "predicate": "có lượng mưa", "object": "320 mm", "critical": true},
    {"id": "P3", "kind": "comparison", "subject": "Tháng có lượng mưa lớn nhất", "predicate": "là", "object": "Tháng 7", "critical": true},
    {"id": "P4", "kind": "inference",  "subject": "Chênh lệch tháng cao nhất và thấp nhất", "predicate": "bằng", "object": "300 mm", "critical": false}
  ],
  "questions": [
    {"id": "Q1", "type": "comparison", "question": "Tháng nào mưa nhiều nhất?", "answer": "Tháng 7"},
    {"id": "Q2", "type": "lookup", "question": "Lượng mưa tháng 7 là bao nhiêu?", "answer": "320 mm"}
  ]
}
```
Các trường `annotation_guide`, `data` trong file mẫu có thể giữ nguyên. **Thời gian**: khoảng 10–20 phút mỗi hình, ~10–15 giờ cho 50 hình.

## 6. Duyệt và rà soát bởi người thứ hai

1. Người gán nhãn tự đối chiếu từng mệnh đề với ảnh, rồi đặt `ground_truth_status` = `"verified"` và `verified_by` = tên.
2. **Người thứ hai** (không cần giỏi môn học; chỉ cần có ảnh trước mặt) kiểm tra **20–30%** số mẫu, chọn ngẫu nhiên: mỗi mệnh đề có
   đúng, đủ các mệnh đề `critical` chưa, có mệnh đề nào mơ hồ không. Ghi lại tỷ lệ mệnh đề hai người thống nhất; nếu dưới ~90% thì
   rà lại cả loạt (quy ước viết chưa rõ). Phần nội dung chuyên môn của môn học nên hỏi thầy cô khi không chắc.
3. Chưa duyệt thì **để nguyên `template_unfilled`**: công cụ sẽ không đưa vào benchmark.

## 7. Đưa vào benchmark

```bash
uv run python evaluation/generators/ingest_textbook.py --promote
uv run python evaluation/generators/validate_benchmark.py
```
`--promote` chỉ nhận mẫu có `verified` + `verified_by`, ít nhất một mệnh đề `critical` và một câu hỏi; mẫu khác sẽ được liệt kê kèm lý do bị bỏ qua.
Lần đầu có ảnh thật, phiên bản benchmark tự đổi thành `0.3.0` (thành phần bộ dữ liệu thay đổi: các kết quả cũ không còn so sánh trực tiếp).
Mẫu được đánh dấu `restricted: true`, `source: textbook`, và split theo sách.

## 8. Chạy mô hình trên ảnh SGK

```bash
uv run python evaluation/runner/run_b1_dev.py --method b0e --provider lmstudio --execute        # chỉ tập dev
```
- Bản ghi của mẫu SGK nằm ở `records_.../_restricted/` (đã bị ignore). `archive_runs.py` sẽ **từ chối** lưu mẫu SGK vào `records/` công khai.
- Chỉ chạy tập **test** khi đã đóng băng prompt, model và rubric.
- Dùng API đám mây (Google, OpenRouter) nghĩa là **gửi ảnh SGK ra ngoài**; gói miễn phí của Google có thể dùng nội dung để cải thiện sản phẩm
  và có người đọc. Với ảnh SGK nên ưu tiên **LM Studio cục bộ**, hoặc xin ý kiến thầy trước khi dùng dịch vụ đám mây.

## 9. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `thiếu 'book'` | Điền đủ các cột bắt buộc |
| `không thấy file trong raw/` | Tên file trong phiếu phải trùng tên thật (phân biệt hoa/thường) |
| `ảnh quá nhỏ` | Chụp/cắt lại, cạnh ngắn ≥300 px |
| `category phải thuộc ...` | Dùng đúng một giá trị trong danh sách |
| `--promote` bỏ qua mẫu | Đọc lý do in ra: chưa verified, thiếu critical, thiếu câu hỏi |
| Dev/test lệch (một tập rỗng) | Thêm sách khác; cùng sách luôn cùng tập |
| Sửa ground truth sau khi đã chạy mô hình | Không nên (làm lệch phép đo). Nếu bắt buộc, ghi lý do và tăng phiên bản benchmark |

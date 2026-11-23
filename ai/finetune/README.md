# Tập huấn luyện tổng hợp cho fine-tune VLM

> **Trạng thái:** bộ sinh dữ liệu đã có và được kiểm thử; **chưa huấn luyện** model nào. Dữ liệu sinh ra **chỉ ở máy**
> (`data/train/`, bị `.gitignore`); thứ đưa ra demo là model đã fine-tune, không phải dữ liệu.

## Có gì

| Thành phần | Mô tả |
|---|---|
| `train_gen.py` | Sinh mẫu: ảnh JPEG + ground truth theo mệnh đề (`truth_v0.2`) + **lời diễn giải mục tiêu bằng văn nói** + cặp hỏi đáp có trả lời nói + nhãn lỗi chụp. Lệnh con `generate`, `check`, `stats` |
| `themes.py` | Kho chủ đề riêng cho huấn luyện (tách khỏi benchmark) và bộ sinh nội dung theo thủ tục |
| (dùng `speech/vn_numbers.py`) | Đọc số/đơn vị bằng chữ tiếng Việt ("hai mươi chín độ C") |
| `export_sft.py` | Xuất JSONL hội thoại (ảnh → mô tả; tùy chọn thêm hỏi đáp) cho fine-tune |

8 loại hình: biểu đồ cột, đường, tròn, bảng, lưu đồ (5 bố cục), sơ đồ vòng, hình học (5 dạng), sơ đồ bản đồ.
Mỗi mẫu được vẽ với tham số ngẫu nhiên; lời diễn giải sinh **từ chính dữ liệu vẽ ảnh** nên đúng tuyệt đối (không bịa).

## Dùng

Chạy trong `ai/`:
```bash
uv run python finetune/train_gen.py generate --n 1200 --seed 1 --out ../data/train/v1   # ~1 phút, ~110 MB
uv run python finetune/train_gen.py check --train ../data/train/v1                        # không trùng benchmark
uv run python finetune/train_gen.py stats --train ../data/train/v1
uv run python finetune/export_sft.py --data ../data/train/v1 --out ../data/train/v1/sft_api_v1.jsonl \
    --split train --include-ask --describe-system-file <prompt hệ thống của backend> --ask-system-file <prompt hỏi đáp>
```
Cùng `--seed` cho kết quả **giống hệt từng byte**. `--issue-rate` (mặc định 0,12) là tỉ lệ ảnh lỗi chụp.

## Chống rò rỉ với benchmark (quan trọng)

- Tập huấn luyện dùng **chủ đề, tiêu đề và nhãn riêng**, không dùng lại chủ đề của dev/test (nước, bướm, cây đậu, v.v.).
- `generate` và `check` đối chiếu với benchmark cục bộ (nếu có) theo **tiêu đề, chữ ký dữ liệu và hash ảnh**; có trùng thì dừng.
- Tách `train`/`val` (5%) ngay trong tập huấn luyện; `val` **không** phải benchmark test.
- Đừng bao giờ đưa dev/test hay ảnh SGK vào huấn luyện nếu vẫn muốn dùng chúng để đánh giá.

## Định dạng mục tiêu

- Mặc định `--format api_v1`: trợ lý trả đúng một JSON `{"page_type","unreadable","description"}` như backend API v1 hiện tại mong đợi.
  **Hợp đồng đang được nhóm thống nhất lại**; đổi định dạng ở đây khi hợp đồng đổi (`--format plain` trả thẳng văn nói).
- `description`: văn nói thuần, ý chính trước, đọc số bằng chữ, 30–150 từ, kết thúc bằng câu gợi ý.
- Prompt hệ thống khi huấn luyện **phải giống** prompt khi chạy thật: nạp bằng `--describe-system-file/--ask-system-file`.
  Bản rút gọn mặc định chỉ để thử.

## Lỗi chụp và hướng dẫn chụp lại (phạm vi chưa xác nhận)

~12% mẫu là ảnh **mờ, tối, chói hoặc bị cắt mất một phần**, với `unreadable=true` và lời hướng dẫn chụp lại cụ thể.
Các nhãn này mã hóa một **chính sách sản phẩm**: khung hình thiếu/hỏng thì yêu cầu chụp lại thay vì đoán. Ý tưởng "hướng dẫn canh camera"
chưa được thầy/nhóm xác nhận; đặt `--issue-rate 0` nếu muốn bỏ. Với các mẫu này, `page_type` luôn là `mixed` (không đoán loại trang từ ảnh hỏng).

## Hạn chế đã biết

- **Chỉ ảnh tổng hợp sạch**: mô hình dễ học "kiểu vẽ" của bộ sinh. Bắt buộc đánh giá trên ảnh thật (benchmark dev/test, ảnh SGK) và cân nhắc trộn ảnh thật đã duyệt khi có.
- **Nội dung theo thủ tục không nhất quán về nghĩa** (vd chu trình "Về nhà → Sửa lỗi → Đóng gói"): hữu ích để học đọc nhãn và quan hệ, không để học kiến thức.
- **Câu văn sinh từ mẫu** (vài biến thể mỗi loại): mô hình có thể học thuộc khuôn câu; cần kiểm tra mức đa dạng đầu ra.
- **Chưa có** trang chữ (nhóm `text`), chữ viết tay, bảng đen, ảnh chụp thật, bản đồ thật, hình khoa học thật.
- Lời diễn giải ngắn nên bỏ bớt chi tiết với bảng lớn: chi tiết nằm ở cặp hỏi đáp.
- Chưa kiểm chứng QLoRA trên RTX 2070 8 GB (có thể sát giới hạn VRAM) cho model nền; model nền đang chuyển từ Qwen3-VL-4B sang Gemma 4 E4B (7,5B, nặng hơn), chưa chọn cách huấn luyện.
- Nếu sau này đưa SGK vào huấn luyện: kiểm tra mức **ghi nhớ/nhả lại nội dung có bản quyền** trước khi phát hành model.

## Việc tiếp theo

Xem mục "Việc tiếp theo" của `README.md` gốc (một danh sách duy nhất).

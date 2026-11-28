# Tập huấn luyện tổng hợp cho fine-tune VLM

> **Trạng thái:** bộ sinh dữ liệu đã có và được kiểm thử; **chưa huấn luyện** model nào. Dữ liệu sinh ra **chỉ ở máy**
> (`data/train/`, bị `.gitignore`); thứ đưa ra demo là model đã fine-tune, không phải dữ liệu.

> **Cảnh báo (27/11/2026): bộ sinh chưa khớp [Quy cách đầu ra](../README.md#quy-cách-đầu-ra-chốt-ngày-27112026). Chưa dùng đầu ra hiện tại để huấn luyện.**
> - Sinh cặp hỏi đáp loại `computation` kèm đáp án tính sẵn. Chênh lệch hai cột được phép (quy tắc 6); tổng, cạnh huyền, diện tích, chu vi tạm thời **không được** (mặc định). Câu hỏi chênh lệch trùng bài tập trên trang cũng không được tính (quy tắc 12).
> - Lời mô tả mục tiêu dài, mô tả cả hình; khi không có câu hỏi chỉ được nói ngắn phần nổi bật nhất hoặc đề mục lớn (quy tắc 7).
> - Lời mô tả mục tiêu nêu cả giá trị suy ra (ví dụ cạnh huyền không ghi trên hình) và kết thúc bằng câu gợi ý, trái quy tắc "chỉ trả lời điều được hỏi".
> - Chưa có mẫu ảnh bài tập (đọc đề, không đưa đáp án), bài giải mẫu in sẵn, hội thoại nhiều lượt.
>
> Hướng của đề tài: model riêng thuộc **họ Gemma**, **ưu tiên distill** (fine-tune vẫn được phép). Đầu ra của teacher cũng phải theo quy cách và được người kiểm một phần; xem điều khoản của model teacher. Không dùng đáp án VMMU hay bộ đề thi để dạy hành vi. Qwen3-VL 4B chỉ dùng để thử quy trình hoặc đối chứng.

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
- Chưa huấn luyện. Tài liệu Unsloth nêu Gemma 4 E4B cần 10 GB VRAM để huấn luyện, hơn mức 8 GB của RTX 2070; Phúc nghiêng về huấn luyện trên Kaggle hoặc Colab (chưa thử). Claude đọc file trên Hugging Face ngày 27/11: bản `unsloth/gemma-4-E4B-it-unsloth-bnb-4bit` có trọng số khoảng 10,2 GiB (các bảng embedding, phần thị giác, âm thanh và một số lớp không nén), trong khi VRAM trống của RTX 2070 khoảng 7,7 GiB; bản 4-bit của Qwen3-VL 4B là 4,30 GB. Unsloth Studio không huấn luyện từ file GGUF. Chưa chạy thử huấn luyện.
- Nếu sau này đưa SGK vào huấn luyện: kiểm tra mức **ghi nhớ/nhả lại nội dung có bản quyền** trước khi phát hành model.

## Việc tiếp theo

Xem mục "Việc tiếp theo" của `README.md` gốc (một danh sách duy nhất).

## Lịch sử cập nhật

Ai sửa file này, theo lịch sử git. "(AI hỗ trợ)" là commit có ghi trợ lý AI trong lời nhắn; commit cũ không ghi thì không suy ra là không dùng.

| Ngày | Người | Việc | Commit |
|---|---|---|---|
| 28/11/2026 | Phúc yêu cầu, Claude ghi | ghi số đo dung lượng bản 4-bit của Gemma và Qwen | `8897986` |
| 27/11/2026 | Phúc (AI hỗ trợ) | docs: gộp 6 báo cáo đánh giá model thành 1, dọn nội dung cũ và link hỏng, ghi luồng sử dụng | `442be9d` |
| 27/11/2026 | Phúc (AI hỗ trợ) | docs: định hướng mới, 12 quy tắc đầu ra của VLM, nhật ký 27/11 (chưa sửa prompt, calc, bộ sinh dữ liệu) | `a0cdcd9` |
| 23/11/2026 | Phúc (AI hỗ trợ) | feat(vlm): optional LMSTUDIO_REASONING_EFFORT for Gemma 4; docs: base model moving to Gemma 4 E4B | `28fae5e` |
| 19/11/2026 | Phúc (AI hỗ trợ) | docs: consolidate markdown (26 -> 13) and refresh README | `1a934b3` |
| 18/11/2026 | Phúc (AI hỗ trợ) | feat(ai): capture quality gate, unreadable prompt, QA with code-computed arithmetic, TTS text prep; split vlm modules | `a878419` |
| 17/11/2026 | Phúc | feat(ai): synthetic training-set generator for VLM fine-tuning; update README | `9c38b09` |

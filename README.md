# AI for Blinds

Nghiên cứu, phát triển hệ thống nhận dạng, diễn giải hình ảnh ứng dụng mô hình ngôn ngữ thị giác (VLM), hỗ trợ học sinh khiếm thị học tập kiến thức trực quan.

> **Nhánh `phuc` (phần AI, Mảng A) — cập nhật 2026-11-19.** `backend/` (Nam) và `frontend/` (Toàn) ở nhánh này chưa có mã (xem [Nhánh](#nhánh)). Mọi kết quả là **thăm dò** trên ảnh tổng hợp, chưa phải kết luận khoa học; tập test chưa chạy.

## Thành phần

- `ai/`: VLM, prompt, cổng chất lượng ảnh, hỏi đáp, hợp đồng đầu ra, đánh giá, chuẩn bị TTS: xem [`ai/README.md`](ai/README.md). Lịch sử theo ngày: [`ai/NHAT_KY_PHAT_TRIEN.md`](ai/NHAT_KY_PHAT_TRIEN.md).
- `data/`: **chỉ ở máy tác giả, không có trong repo** (xem [Dữ liệu](#dữ-liệu)).
- `docs/bao_cao/`: tài liệu nộp của Mảng A. `backend/`, `frontend/`: Nam, Toàn (nhánh này rỗng).

## Điều cần biết ngay

- **Cổng "ảnh không đọc được" chưa dùng được trên ảnh thật:** `b0g_v1` đúng trên ảnh tổng hợp (4/4 ảnh mờ, 0/40 báo nhầm) nhưng **báo nhầm 5/32 trang SGK thật sạch** → [báo cáo mô-đun](ai/evaluation/reports/system_modules_4b_20261118.md), mục 6.
- **Model nền: đang chuyển từ Qwen3-VL-4B sang Gemma 4 E4B** (Q4, chạy cục bộ qua LM Studio, miễn phí; cần gửi `reasoning_effort=none`, xem `LMSTUDIO_REASONING_EFFORT` ở `ai/README.md`). Trên dev, Gemma phủ ngang Qwen (~85%) nhưng chậm hơn (11–14 s so với 7–9 s mỗi mô tả); chưa đo `b0g_v1` và hỏi đáp cho Gemma. Các số đo đến nay là của Qwen 4B; bản 8B không nạp đủ lên GPU 8 GB nên bị loại → [khảo sát Qwen](ai/evaluation/reports/survey_qwen3vl_q4_20261117.md).
- **Chưa fine-tune** (hướng huấn luyện cho Gemma chưa chọn). Chưa có chấm bằng người, chưa có người khiếm thị đánh giá, chưa có SGK lớp 4–5 hay biểu đồ/bản đồ SGK thật.

## Trạng thái phần AI

| Hạng mục | Trạng thái | Chi tiết |
|---|---|---|
| Hợp đồng đầu ra | Nháp v0.1, chưa đối chiếu với API v1 của Nam | [`ai/contract/`](ai/contract/README.md) |
| Module AI (`describe_page`, `ask_page`) | Chạy được, có kiểm thử, không ném ngoại lệ | [`ai/README.md`](ai/README.md) |
| Nhà cung cấp VLM | OpenRouter, Google AI Studio, LM Studio (cục bộ) | [`ai/README.md`](ai/README.md) |
| Cổng chất lượng ảnh | Bắt tối/mờ trên ảnh tổng hợp; chưa hiệu chỉnh trên ảnh thật | [mô-đun](ai/evaluation/reports/system_modules_4b_20261118.md) |
| Hỏi đáp theo hình | Tính toán bằng mã; 68% → 90% trên dev (từ khóa thô, có thể lạc quan) | [mô-đun](ai/evaluation/reports/system_modules_4b_20261118.md) |
| So sánh phương pháp / model (dev) | 4B cục bộ ngang gemini-3.1-flash-lite, hơn nemotron; B1 không giúp 4B | [so sánh](ai/evaluation/reports/so_sanh_phuong_phap_va_model_dev_20261117.md) |
| Benchmark | 47 ảnh tổng hợp (dev 24 / test 23); 74 ảnh Wikimedia ứng viên chưa có ground truth | [`data/benchmark/`](data/benchmark/README.md) |
| Dữ liệu ngoài (Hugging Face) | 7 bộ đã tải (~47 GB), phân 3 mục, có lớp phủ train/val/test chống rò rỉ | [dữ liệu ngoài](ai/evaluation/reports/du_lieu_ngoai_20261118.md) |
| Tập huấn luyện tổng hợp / fine-tune | Bộ sinh đã có; **chưa huấn luyện** | [`ai/finetune/`](ai/finetune/README.md) |
| Chuẩn hóa văn bản TTS | Có; **chưa có engine STT/TTS** (để phần mềm quyết định) | [`ai/README.md`](ai/README.md) |
| Đánh giá bằng người (rubric), người khiếm thị | Chưa có | [`rubric_v1.md`](ai/evaluation/rubrics/rubric_v1.md) |

## Chạy nhanh

```bash
cd ai
cp .env.example .env              # điền khóa; KHÔNG commit .env
uv run pytest -q                  # kiểm thử, không gọi mô hình thật
uv run python vlm/list_models.py --provider lmstudio
uv run python evaluation/runner/survey_lmstudio.py --tag demo --scales 1.0 --reps 2   # dry run; thêm --execute để gọi model đang nạp
```

Chỉ thêm `--execute` khi muốn gọi mô hình thật. Mặc định chỉ chạy tập **dev**; tập test chỉ chạy khi đã đóng băng cấu hình.

## Dữ liệu

Chỉ nằm ở máy tác giả (`.gitignore`): để **fine-tune**, để giữ **tập test riêng tư** và vì SGK có bản quyền. Khi ship demo, thứ đưa ra là **model đã fine-tune** (trọng số phát hành riêng, không commit).

| Thư mục | Nội dung |
|---|---|
| `data/benchmark/` | bộ **đánh giá** của nhóm (ảnh tổng hợp; tái tạo được từ mã), ảnh ứng viên Wikimedia |
| `data/train/v1/` | bộ **huấn luyện** tổng hợp, chủ đề tách khỏi benchmark |
| `data/external/` | dữ liệu ngoài: `1_hoc_tap/` (SGK), `2_cuoc_song/`, `3_hon_hop/` (infographic), kèm `_index/`, `_reports/`, `_sft/` |

SGK và học liệu có bản quyền **không** đưa lên repo công khai; không commit khóa API, `.env` hay trọng số model. Lịch sử git cũ vẫn chứa bản sao dữ liệu tổng hợp và ảnh ứng viên (tái tạo được hoặc đã công khai).

## Nhánh

| Nhánh | Nội dung |
|---|---|
| `main` | Bản cũ (2026-05, SgBe Vision); nhánh mặc định, chưa cập nhật |
| `dev`, `nam` | Backend FastAPI `/v1/*`, `docs/API_v1.md` (Nam): hợp đồng API v1 hiện hành |
| `toan/app-mvp` | App Flutter MVP theo API v1 (Toàn) |
| `fix/e2e-vlm-stt-rag` | Bản chạy thông cũ (2026-08), có thể lỗi thời |

Nhánh `phuc` được **xây lại từ đầu** (2026-10-23) nên khác gốc với các nhánh trên; việc hợp nhất chưa thực hiện. Mọi thay đổi hợp đồng cần cả nhóm duyệt.

## Việc tiếp theo

1. Hiệu chỉnh cổng "không đọc được" trên trang SGK thật rồi đo lại.
2. Thu thập và gán nhãn SGK lớp 4–5, biểu đồ/bản đồ thật (cần người gán nhãn, người rà soát thứ hai, văn bản cho phép của thầy).
3. Chấm tay (rubric, hai người) và thiết kế chỉ số nhạy hơn; chạy tập test khi đóng băng cấu hình.
4. Quyết định hướng fine-tune (QLoRA trên 8 GB VRAM chưa kiểm chứng).
5. Đối chiếu hợp đồng AI v0.1 với API v1 (Phúc, Nam, Toàn) và hợp nhất các nhánh.

---
*Cập nhật README: (1) chỉ sửa dòng trạng thái đã đổi; (2) đổi ngày ở đầu; (3) thêm mục vào `ai/NHAT_KY_PHAT_TRIEN.md`.*

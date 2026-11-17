# AI for Blinds

Nghiên cứu, phát triển hệ thống nhận dạng, diễn giải hình ảnh
ứng dụng mô hình ngôn ngữ thị giác, hỗ trợ học sinh khiếm thị
học tập kiến thức trực quan.

> **Nhánh `phuc` — cập nhật 17/11/2026.** Nhánh này chứa phần **AI (Mảng A)**: module diễn giải ảnh bằng VLM,
> bộ dữ liệu đánh giá và các thực nghiệm thăm dò. `backend/` (Nam) và `frontend/` (Toàn) ở nhánh này **chưa có mã**;
> mã của hai phần đó nằm ở các nhánh khác (xem [Các nhánh khác](#các-nhánh-khác)). Mọi kết quả dưới đây là **thăm dò**,
> chưa phải kết luận khoa học.

## Các thành phần

- `ai/`: VLM, prompting, hợp đồng đầu ra, đánh giá mô hình, STT/TTS — Phúc.
- `backend/`: API, dữ liệu và triển khai — Nam. *(nhánh này: rỗng)*
- `frontend/`: Ứng dụng Flutter và trợ năng — Toàn. *(nhánh này: rỗng)*
- `data/benchmark/`: bộ dữ liệu đánh giá — **chỉ ở máy tác giả, không có trong repo** (xem [Dữ liệu và fine-tune](#dữ-liệu-và-fine-tune)).
- `docs/`: tài liệu nghiên cứu và thiết kế. *(nhánh này: rỗng; tài liệu nội bộ không đưa lên repo công khai)*

## Trạng thái phần AI (nhánh `phuc`)

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Hợp đồng đầu ra AI (`ai/contract/`) | **Bản nháp v0.1** | Mô hình Pydantic, JSON Schema, ví dụ. Chưa đối chiếu với `docs/API_v1.md` của Nam; chưa được nhóm duyệt |
| Module `describe_image` (`ai/vlm/`) | Chạy được, có kiểm thử | Phương pháp B0/B0e (1 bước) và B1 (trích xuất rồi diễn giải); lỗi vận hành trả `status="error"`, không ném ngoại lệ |
| Nhà cung cấp VLM | OpenRouter, Google AI Studio, LM Studio (cục bộ) | Chọn bằng `VLM_PROVIDER` hoặc tham số; LM Studio tự dò địa chỉ từ WSL2 |
| Benchmark v0.2.0 (chỉ ở máy) | **47 mẫu tổng hợp** | 8 loại hình; dev 24 / test 23; ground truth theo mệnh đề (`truth_v0.2`); tái tạo được từ mã `ai/evaluation/generators/` |
| Ảnh thật (ở máy) | 37 ứng viên Wikimedia Commons | Chỉ giấy phép tự do; **chưa** nằm trong benchmark; 4 bản nháp ground truth **chưa kiểm chứng** |
| Ảnh SGK (ở máy) | **Chưa có** | Có công cụ nạp + hướng dẫn (`ai/docs/textbook/HUONG_DAN.md`); nội dung SGK **không** được đưa lên repo |
| Tập huấn luyện (`ai/finetune/`) | Bộ sinh **đã có**, 96 kiểm thử | Sinh ảnh + lời diễn giải văn nói + hỏi đáp + nhãn lỗi chụp; tách chủ đề khỏi dev/test; dữ liệu chỉ ở máy |
| Fine-tune VLM | **Chưa huấn luyện** | Xem `ai/finetune/README.md` và [Dữ liệu và fine-tune](#dữ-liệu-và-fine-tune) |
| Thực nghiệm | Chỉ tập **dev**, 1 lần chạy/ảnh | Xem `ai/evaluation/reports/`; tập test **chưa chạy** |
| Hỏi đáp theo hình, STT/TTS (`ai/speech/`) | **Chưa có** | |
| Phương pháp xác minh (B2) | **Chưa có** | |
| Đánh giá bằng người (rubric), người dùng khiếm thị | **Chưa có** | Chỉ số hiện dùng là từ khóa thô, thiếu độ nhạy |

### Kết quả thăm dò chính (dev, ảnh tổng hợp — không khái quát được)

- Qwen3-VL-4B chạy cục bộ qua LM Studio (miễn phí) đạt mức phủ mệnh đề ngang `gemini-3.1-flash-lite` và hơn nemotron trong cùng điều kiện;
  là ứng viên baseline, **chưa** kết luận hơn kém vì chỉ số chạm trần.
- B1 (hai bước) giúp bảng số liệu với một model lớn nhưng **không** giúp với model 4B (lan truyền lỗi giữa hai bước).
- Lỗi thường gặp: sai dấu tiếng Việt khi chép nhãn (tùy model), bịa thành phần ở sơ đồ vòng, bỏ sót số liệu bảng.

Chi tiết và giới hạn: `ai/evaluation/reports/dev_b0_nemotron_20261117.md`, `dev_b0_b0e_b1_20261117.md`, `dev_model_comparison_20261117.md`.

## Các nhánh khác

| Nhánh | Nội dung | Ghi chú |
|---|---|---|
| `main` | Bản cũ (05/2026, SgBe Vision) | Nhánh mặc định; chưa cập nhật |
| `dev`, `nam` | Backend FastAPI `/v1/*`, `prompts/v1`, `docs/API_v1.md` (Nam, 10/2026) | Hợp đồng API v1 hiện hành của nhóm |
| `toan/app-mvp` | App Flutter MVP theo hợp đồng API v1 (Toàn, 10/2026) | |
| `fix/e2e-vlm-stt-rag` | Bản chạy thông cũ (08/2026) | Ngăn xếp cũ, có thể đã lỗi thời |

Nhánh `phuc` đã **xây lại từ đầu** (23/10/2026) nên **khác gốc** với `dev`/`nam`/`toan/app-mvp`; việc hợp nhất chưa thực hiện.
Hợp đồng API v1 và hợp đồng AI v0.1 chưa được đối chiếu; mọi thay đổi hợp đồng cần cả nhóm duyệt.

## Chạy nhanh (phần AI)

```bash
cd ai
cp .env.example .env            # điền khóa của bạn; KHÔNG commit .env
uv run pytest -q                # 96 kiểm thử, không gọi API thật
uv run python evaluation/generators/generate_benchmark_v02.py  # (tùy chọn) tái tạo benchmark tổng hợp ở máy; dữ liệu không có sẵn trong repo
uv run python evaluation/generators/validate_benchmark.py     # kiểm tra benchmark cục bộ (hash, schema, split)
uv run python vlm/list_models.py --provider lmstudio          # model khả dụng của nhà cung cấp
uv run python evaluation/runner/run_b1_dev.py --method b0e --provider lmstudio   # dry run trên tập dev
```
Chỉ thêm `--execute` khi muốn gọi mô hình thật. Mặc định chỉ chạy tập **dev**; tập test chỉ chạy khi đã đóng băng cấu hình.

## Dữ liệu và fine-tune

**Dữ liệu chỉ nằm ở máy tác giả**, không có trong repo: benchmark tổng hợp, ảnh ứng viên, ảnh SGK, ground truth và bản ghi đầu ra
từng mẫu (`.gitignore`). Mục đích: (1) dùng để **fine-tune** VLM; (2) giữ **tập test riêng tư** để phép đo không bị "rò rỉ" vào
dữ liệu huấn luyện của bên khác; (3) tránh đăng nội dung có bản quyền. Khi ship demo, thứ được đưa ra là **model đã fine-tune**
(trọng số phát hành riêng, không commit vào git).

- Mẫu tổng hợp tái tạo từ mã (giống hệt từng byte); giấy phép CC0.
- Ảnh Wikimedia Commons tải lại bằng `fetch_commons_candidates.py`; giữ giấy phép gốc và ghi nguồn khi dùng.
- **SGK và học liệu có bản quyền: không đưa lên repo công khai** (ảnh, ground truth, đầu ra mô hình). Xem `ai/docs/textbook/HUONG_DAN.md`.
- Lịch sử git cũ (các commit đã push trước 17/11/2026) vẫn chứa bản sao dữ liệu tổng hợp và ảnh ứng viên; chúng đều tái tạo được hoặc đã công khai.
- **Khi fine-tune:** dùng tập huấn luyện **riêng** (`ai/finetune/`: `uv run python finetune/train_gen.py generate ...`), không lấy từ dev/test; kiểm tra trùng benchmark bằng `train_gen.py check`; đánh giá rò rỉ/ghi nhớ nội dung SGK trước khi phát hành model.
- Không commit khóa API, file `.env` hay trọng số model.

## Việc tiếp theo

1. Đối chiếu hợp đồng AI v0.1 với `docs/API_v1.md`; thống nhất cách hợp nhất các nhánh.
2. Thu thập và gán nhãn ảnh SGK (cần người gán nhãn và người rà soát thứ hai); thiết kế chỉ số nhạy hơn (rubric, mệnh đề bịa).
3. Fine-tune thử trên tập huấn luyện đã có (QLoRA trên 8 GB VRAM **chưa kiểm chứng**) rồi đo trên dev; hỏi đáp theo hình và STT/TTS; thử xác minh dữ kiện (B2); chạy tập test khi đóng băng cấu hình.

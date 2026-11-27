# AI for Blinds

Nghiên cứu, phát triển hệ thống nhận dạng, diễn giải hình ảnh ứng dụng mô hình ngôn ngữ thị giác (VLM), hỗ trợ học sinh khiếm thị học tập kiến thức trực quan.

> **Nhánh `phuc`, cập nhật 2026-11-27.** Gồm cả hệ thống: module AI (Phúc), backend API v1 (Nam), app Flutter (Toàn); cách ghép và cách chạy ở [`docs/TICH_HOP.md`](docs/TICH_HOP.md). Mọi kết quả đo là **thăm dò**, chưa phải kết luận khoa học. Tập test của benchmark tổng hợp chưa chạy (VMMU test chạy một lần ngày 27/11).

## Định hướng (cập nhật 2026-11-27)

- **Người dùng:** học sinh khiếm thị lớp 1–12 và sinh viên khiếm thị. Hệ thống hỗ trợ học, **không giải bài tập, không đưa đáp án**, không thay giáo viên; VLM chỉ trả lời điều được hỏi. Chi tiết: [Quy cách đầu ra](ai/README.md#quy-cách-đầu-ra-chốt-ngày-27112026).
- **Sản phẩm:** app di động, bài báo nghiên cứu, một VLM riêng của đề tài (định hướng họ Gemma).
- **Kiến trúc:** hybrid client-server. Online dùng model teacher trên server hoặc cloud; mất mạng dùng model student. Server trả văn bản, app lo TTS.
- **Phương pháp:** fine-tune hoặc distill, **ưu tiên distill** (yêu cầu của giảng viên); tách nghiên cứu model-level và system-level.

## Thành phần

- `ai/`: VLM, prompt, cổng chất lượng ảnh, hỏi đáp, hợp đồng đầu ra, đánh giá, chuẩn bị TTS: xem [`ai/README.md`](ai/README.md). Lịch sử theo ngày: [`ai/NHAT_KY_PHAT_TRIEN.md`](ai/NHAT_KY_PHAT_TRIEN.md).
- `data/`: phần lớn **chỉ ở máy tác giả** (xem [Dữ liệu](#dữ-liệu)); repo chỉ theo dõi `data/library/` và README của `data/benchmark/`.
- `backend/`: FastAPI, hợp đồng [`docs/API_v1.md`](docs/API_v1.md) (Nam). Chế độ `mock` / `openai` / `ai`.
- `frontend/`: app Flutter cho học sinh khiếm thị (Toàn): xem [`frontend/README.md`](frontend/README.md). Ngày 27/11 thêm hướng dẫn chụp trên máy (nhắc khi đang ngắm, kiểm ảnh vừa chụp); test tự động đạt, **chưa chạy trên điện thoại**.
- `data/library/`: kho sách đã số hóa phục vụ `/v1/library` (có trong repo). `prompts/`, `scripts/`: của backend.
- `docs/bao_cao/`: tài liệu nộp của Mảng A. `docs/TICH_HOP.md`: tài liệu ghép hệ thống.

## Điều cần biết ngay

- **Mã chưa khớp [Quy cách đầu ra](ai/README.md#quy-cách-đầu-ra-chốt-ngày-27112026):** prompt hiện tại chưa cấm giải bài tập, hỏi đáp còn tính hộ, ảnh không kèm câu hỏi vẫn được mô tả cả trang.
- **Báo "không đọc được" trên trang SGK thật còn sai:** `b0g_v1` báo nhầm 5/32 trang sạch (đo với Qwen3-VL 4B, chưa đo lại với Gemma) → [đánh giá model](ai/evaluation/reports/danh_gia_model.md), mục 3.4.
- **Cổng chất lượng của máy chủ còn chặn nhầm hình nền đen rõ nét** (xem [`ai/README.md`](ai/README.md)).
- **Model:** hướng của đề tài là họ Gemma. Trên benchmark dev tổng hợp, phần **mô tả** của Gemma 4 E4B và Qwen3-VL 4B ngang nhau trong dao động; phần **hỏi đáp có tính hộ** Gemma 42/59, Qwen 51–53/59 (đính chính 27/11: kết luận "ngang nhau" trước đây so lệch điều kiện) → [đánh giá model](ai/evaluation/reports/danh_gia_model.md), mục 4 và 5.
- **Chưa fine-tune hay distill.** Chưa có chấm bằng người, chưa có người khiếm thị đánh giá; chưa có bộ đánh giá đã gán nhãn trên SGK thật.

## Trạng thái phần AI

| Hạng mục | Trạng thái | Chi tiết |
|---|---|---|
| Hợp đồng đầu ra | Nháp v0.1; đã đối chiếu với API v1 trong `backend/app/ai_bridge.py` (Toàn ghép), **chờ cả nhóm duyệt** | [`ai/contract/`](ai/contract/README.md) |
| Module AI (`describe_page`, `ask_page`) | Chạy được, có kiểm thử, không ném ngoại lệ | [`ai/README.md`](ai/README.md) |
| Nhà cung cấp VLM | OpenRouter, Google AI Studio, LM Studio (cục bộ) | [`ai/README.md`](ai/README.md) |
| Cổng chất lượng ảnh | Đã hiệu chỉnh trên ảnh thật 27/11 (chặn nhầm ảnh tốt VizWiz 15,1% → 1,3%, đổi lại bắt ít ảnh xấu hơn) | [báo cáo cổng](ai/evaluation/reports/capture_gate_anh_that_20261127.md) |
| Hỏi đáp theo hình | Tính toán bằng mã; 68% → 90% trên dev (từ khóa thô, có thể lạc quan). **Chưa khớp quy cách không giải bài tập** | [đánh giá model, mục 3](ai/evaluation/reports/danh_gia_model.md) |
| So sánh phương pháp / model (dev) | 4B cục bộ ngang gemini-3.1-flash-lite, hơn nemotron; B1 không giúp 4B | [đánh giá model, mục 1](ai/evaluation/reports/danh_gia_model.md) |
| Benchmark | 47 ảnh tổng hợp (dev 24 / test 23); 74 ảnh Wikimedia ứng viên chưa có ground truth | [`data/benchmark/`](data/benchmark/README.md) |
| Dữ liệu ngoài (Hugging Face) | 8 bộ trong lớp phủ (~55 GB) và VizWiz chưa vào bảng kiểm kê; phân 3 mục, có lớp phủ train/val/test chống rò rỉ; cần xác minh giấy phép trước khi huấn luyện | [dữ liệu ngoài](ai/evaluation/reports/du_lieu_ngoai_20261118.md) |
| Tập huấn luyện tổng hợp / fine-tune | Bộ sinh đã có; **chưa huấn luyện** | [`ai/finetune/`](ai/finetune/README.md) |
| Chuẩn hóa văn bản TTS | Có; **chưa có engine STT/TTS** (để phần mềm quyết định) | [`ai/README.md`](ai/README.md) |
| Đánh giá bằng người (rubric), người khiếm thị | Chưa có người chấm. Ngày 26/11, AI chấm sơ bộ 4 ca lỗi × 2 điều kiện (không thay người chấm) | [`rubric_v1.md`](ai/evaluation/rubrics/rubric_v1.md); [mẫu, mục 6](ai/evaluation/reports/danh_gia_model.md) |

## Chạy cả hệ thống

```powershell
py -3.12 -m venv .venv
.venv\Scripts\pip install -r backend\requirements-dev.txt -r backend\requirements-ai.txt
$env:VLM_MODE="mock"     # hoặc "ai" (điền ai\.env trước)
.venv\Scripts\python -X utf8 -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
cd frontend; flutter run  # emulator tự trỏ http://10.0.2.2:8000
```

Hoặc `docker compose up --build`. Chi tiết: [`docs/TICH_HOP.md`](docs/TICH_HOP.md).

## Chạy riêng phần AI

```bash
cd ai
cp .env.example .env              # điền khóa; KHÔNG commit .env
uv run pytest -q                  # kiểm thử, không gọi mô hình thật
uv run python vlm/list_models.py --provider lmstudio
uv run python evaluation/runner/survey_lmstudio.py --tag demo --scales 1.0 --reps 2   # dry run; thêm --execute để gọi model đang nạp
```

Chỉ thêm `--execute` khi muốn gọi mô hình thật. Mặc định chỉ chạy tập **dev**; tập test chỉ chạy khi đã đóng băng cấu hình.

## Dữ liệu

Chỉ nằm ở máy tác giả (`.gitignore`): để **fine-tune**, để giữ **tập test riêng tư** và vì SGK có bản quyền. Khi ship demo, thứ đưa ra là **model của đề tài** (trọng số phát hành riêng, không commit).

| Thư mục | Nội dung | Tài liệu mô tả |
|---|---|---|
| `data/benchmark/` | bộ **đánh giá** của nhóm (ảnh tổng hợp; tái tạo được từ mã), ảnh ứng viên Wikimedia | [README](data/benchmark/README.md) |
| `data/train/v1/` | bộ **huấn luyện** tổng hợp, chủ đề tách khỏi benchmark | [README fine-tune](ai/finetune/README.md) |
| `data/external/` | dữ liệu ngoài: `1_hoc_tap/`, `2_cuoc_song/`, `3_hon_hop/` (infographic), kèm `_index/`, `_reports/`, `_sft/`; mỗi bộ có README riêng ở máy | [báo cáo kiểm kê](ai/evaluation/reports/du_lieu_ngoai_20261118.md) |
| `data/library/` | kho sách đã số hóa cho `/v1/library` (có trong repo) | [TICH_HOP, mục Thư viện](docs/TICH_HOP.md#thư-viện) |

SGK và học liệu có bản quyền **không** đưa lên repo công khai; không commit khóa API, `.env` hay trọng số model. Lịch sử git cũ vẫn chứa bản sao dữ liệu tổng hợp và ảnh ứng viên (tái tạo được hoặc đã công khai).

## Tài liệu theo thư mục

Bản đồ tài liệu: mỗi thư mục gốc, nơi có md mô tả và các báo cáo chính.

| Thư mục | Tài liệu |
|---|---|
| `ai/` | [README](ai/README.md) (bảng các thư mục con), [nhật ký phát triển](ai/NHAT_KY_PHAT_TRIEN.md) |
| `ai/contract/` | [README hợp đồng v0.1](ai/contract/README.md) |
| `ai/finetune/` | [README](ai/finetune/README.md) |
| `ai/docs/textbook/` | [hướng dẫn nạp ảnh SGK](ai/docs/textbook/HUONG_DAN.md) |
| `ai/evaluation/rubrics/` | [rubric v1](ai/evaluation/rubrics/rubric_v1.md) |
| `ai/evaluation/reports/` | [đánh giá model và mô-đun](ai/evaluation/reports/danh_gia_model.md); [cổng ảnh trên ảnh thật](ai/evaluation/reports/capture_gate_anh_that_20261127.md); [dữ liệu ngoài](ai/evaluation/reports/du_lieu_ngoai_20261118.md) |
| `backend/` | [API v1](docs/API_v1.md) (hợp đồng); chưa có README riêng cho mã backend |
| `data/` | xem mục [Dữ liệu](#dữ-liệu) |
| `docs/` | [TICH_HOP](docs/TICH_HOP.md) (ghép hệ thống); [API v1](docs/API_v1.md); [bản nháp hồ sơ nghiên cứu A01](docs/bao_cao/A01_ho_so_nghien_cuu_DRAFT.md) |
| `frontend/` | [README](frontend/README.md); [checklist trợ năng](frontend/docs/CHECKLIST_TRO_NANG.md); [kịch bản tương tác](frontend/docs/KICH_BAN_TUONG_TAC.md); [yêu cầu giao diện](frontend/docs/YEU_CAU_GIAO_DIEN.md) |
| `prompts/v1/` | các prompt backend đọc (`backend/app/prompts.py`); chưa có README |
| `scripts/`, `.github/` | chưa có md; `scripts/digitize_book.py` có mô tả trong docstring, `.github/workflows/ci.yml` có comment đầu file |

## Nhánh

| Nhánh | Nội dung |
|---|---|
| `main` | Bản cũ (2026-05, SgBe Vision); nhánh mặc định, chưa cập nhật |
| `phuc` | Module AI (Phúc) **+ bản ghép backend/app**; chứa toàn bộ `toan/tich-hop` tính đến 2026-11-27 |
| `dev`, `nam` | Backend FastAPI `/v1/*`, `docs/API_v1.md` (Nam): hợp đồng API v1 hiện hành |
| `toan/tich-hop` | **Nhánh duy nhất của Toàn**: bản ghép `phuc` + `dev` + app Flutter `frontend/` + các sửa của Toàn (cổng chất lượng 27/11) |
| `fix/e2e-vlm-stt-rag` | Bản chạy thông cũ (2026-08), có thể lỗi thời |

Nhánh `phuc` được **xây lại từ đầu** (2026-10-23) nên khác gốc với các nhánh cũ; bản ghép dùng `--allow-unrelated-histories` (2026-11-25), chờ cả nhóm duyệt. Ngày 2026-11-27 Toàn gộp mọi nhánh `toan/*` về `toan/tich-hop`. `dev`, `nam` đã nằm trọn trong `phuc`; chủ nhánh quyết định có xóa `dev`, `nam`, `fix/e2e-vlm-stt-rag` không. Mọi thay đổi hợp đồng cần cả nhóm duyệt.

## Việc tiếp theo

1. Theo [Quy cách đầu ra](ai/README.md#quy-cách-đầu-ra-chốt-ngày-27112026): làm bộ kiểm tra tuân thủ, rồi sửa prompt, cách dùng `calc`, mô tả ngắn khi không có câu hỏi.
2. Hướng dẫn chụp: build và thử trên điện thoại thật, hiệu chỉnh ngưỡng, đo tỉ lệ ảnh hỏng khi tắt và bật ([`frontend/README.md`](frontend/README.md)).
3. Sửa cổng máy chủ chặn nhầm hình nền đen; đo lại báo "không đọc được" trên trang SGK thật.
4. Thu thập và gán nhãn SGK thật, gồm bảng đen và màn hình (cần người gán nhãn, người rà soát thứ hai, văn bản cho phép của thầy); chấm tay hai người.
5. Sau đó chọn teacher và cách distill (model student họ Gemma); huấn luyện trên Kaggle, Colab hoặc máy chủ học viện.

---
*Cập nhật README: (1) chỉ sửa dòng trạng thái đã đổi; (2) đổi ngày ở đầu; (3) thêm mục vào `ai/NHAT_KY_PHAT_TRIEN.md`.*

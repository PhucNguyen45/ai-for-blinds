# Tích hợp hệ thống SgBe (nhánh `toan/tich-hop`)

Người ghép: Toàn, 25/11/2026. Ghép ba nhánh thành một hệ chạy thông:

| Phần | Người | Thư mục | Nguồn |
|---|---|---|---|
| Module AI (VLM, prompt, cổng chất lượng ảnh, hỏi đáp) | Phúc | `ai/` | nhánh `phuc` (0296f26) |
| Backend FastAPI, API v1, kho thư viện | Nam | `backend/`, `data/library/`, `prompts/`, `scripts/`, `docs/API_v1.md` | nhánh `dev` (giữ nguyên lịch sử) |
| App Flutter | Toàn | `frontend/` | nhánh `toan/frontend` |

Nhánh `phuc` được dựng lại từ đầu nên khác gốc với `dev`; lần ghép dùng `--allow-unrelated-histories`.
Xung đột chỉ có `.gitignore` (gộp hai bên) và `README.md` (giữ bản của Phúc, thêm mục chạy cả hệ thống).

## Luồng chạy

```
App (Flutter)  ──HTTP API v1──>  Backend (FastAPI)  ──VLM_MODE──┬─ mock   : dữ liệu thử, không cần mạng
  chụp, nghe, hỏi bằng giọng      /v1/describe                    ├─ openai : backend tự gọi mô hình (VLM_*)
  STT có sẵn của Android          /v1/ask                         └─ ai     : ai/pipeline.py của Phúc
                                  /v1/library                                 cổng chất lượng ảnh → prompt → VLM
                                  /health                                     (OpenRouter / Google / LM Studio)
```

Chế độ mới **`VLM_MODE=ai`** (`backend/app/ai_bridge.py`): backend lưu ảnh, gọi `describe_page` / `ask_page`
của Phúc trong threadpool, đổi kết quả hợp đồng v0.1 sang API v1. Cấu hình mô hình đọc từ `ai/.env`
(`VLM_PROVIDER`, `<PROVIDER>_MODEL`, khóa), không dùng các dòng `VLM_*` của backend.

## Đối chiếu hợp đồng AI v0.1 ↔ API v1

Backend trả **cả hai bộ trường**: trường API v1 (app cũ, công cụ của Nam đọc) và trường v0.1 (app mới đọc thêm).

| API v1 (`/v1/describe`) | Lấy từ v0.1 (`DescriptionResult`) |
|---|---|
| `description` | `interpretation_vi`; rỗng thì `summary_vi` (ảnh bị chặn chỉ có `summary_vi`) |
| `unreadable` | `status ∈ {unreadable, unsupported}` |
| `page_type` | `image_type`: bar/line/pie_chart→`chart`, table→`table`, flow/cycle_diagram, geometry→`figure`, map→`map`, text→`text`; còn lại (`unknown` của B0) → `mixed` khi gửi `auto` |
| `model`, `prompt_version` | `meta.model`, `meta.prompt_id`; ảnh bị cổng chặn (không có `meta`) → tên model cấu hình, `capture_gate` |
| *(thêm)* `status`, `summary_vi`, `interpretation_vi`, `image_type`, `uncertainties`, `question_answering_ready` | giữ nguyên |

| `error.code` của module AI | HTTP | `code` API v1 |
|---|---|---|
| `timeout` | 504 | `VLM_TIMEOUT` |
| `invalid_image` | 400 | `INVALID_IMAGE` |
| `invalid_input` | 422 | `INVALID_REQUEST` |
| `config_error` | 503 | `AI_NOT_CONFIGURED` *(mã mới)* |
| `http_error`, `empty_response`, `invalid_output`, `unknown` | 502 | `VLM_ERROR` |

Câu báo lỗi cho người dùng là câu tiếng Việt cố định của backend; chi tiết nội bộ (`error.message` của module AI)
chỉ ghi log, không đọc cho người dùng.

`/v1/ask`: `history` của API v1 (`[{question, answer}]`) đổi thành `[(q, a)]` cho `ask_page`; `answer_vi` → `answer`.

### Ba điểm nghĩa đã thống nhất trong lần ghép

1. **`partial` = lời diễn giải bị CẮT NGẮN do giới hạn độ dài**, không phải ảnh hỏng (`vlm/describer.py`:
   `finish_reason == "length"`). Backend để `unreadable=false`; app đọc phần có được rồi nói
   "Phần mô tả bị ngắt giữa chừng. Bạn có thể bấm Hỏi để hỏi thêm về phần còn lại."
2. **Ảnh bị cổng chất lượng chặn**: `summary_vi` đã là lời hướng dẫn chụp lại ("… rồi chụp lại nhé").
   App không nói thêm câu hướng dẫn của mình (tránh nói hai lần). Kết quả này **không lưu cache**
   (chụp lại cùng ảnh vẫn được kiểm lại).
3. **`question_answering_ready` không dùng để chặn nút Hỏi.** Hợp đồng dành cờ này cho B1 (facts có cấu trúc);
   B0 hiện tại luôn để `false` (`ai/contract/README.md`, "Hạn chế hiện tại"). `/v1/ask` gửi lại chính ảnh cho
   mô hình nên hỏi được với mọi ảnh `ok`/`partial`. App chỉ chặn hỏi khi ảnh hỏng hoặc lỗi.
   *Nếu không sửa điểm này, app sẽ chặn Hỏi sau MỌI lần mô tả thật.*

### Chặn lặp trước khi đọc to (thêm 25/11/2026)

Mô hình nhỏ giải mã tham lam đôi khi lặp một câu tới hết giới hạn token (thẻ mô hình Peppercorn-0.3b đo
2,8% trang). `backend/app/repetition.py` cắt phần lặp ở cả ba chế độ, cho cả mô tả lẫn câu trả lời:
khối 1–4 câu giống nhau liền nhau từ 3 lần (hoặc từ 2 lần mà kéo tới hết văn bản), hay một đoạn ký tự lặp
từ 4 lần ở đuôi. Giữ một bản, giữ phần sau nếu mô hình đã thoát vòng lặp. Khi có cắt: `status` `ok` →
`partial`, thêm `"loop_cut"` vào `uncertainties`, không lưu đệm (chụp lại sẽ gọi mô hình lần nữa).
Mã viết riêng, không chép mã Peppercorn (giấy phép của họ chỉ cho nghiên cứu, đánh giá).
Kiểm: `tests/test_repetition.py` (ca lặp mô phỏng, ca không được cắt, mọi lời mô tả mẫu trong repo);
ngoài repo: 0 cắt nhầm trên 6 đầu ra thật của Qwen3-VL 8B/30B.

## Thư viện

`data/library/` có ba cuốn: `demo` (Nam), `tnxh3-mau`, `lsdl4-mau` (chuyển từ sách mẫu đóng gói của app sang định
dạng manifest của Nam, `model="viet-tay"`, `reviewed=false`). `PageRecord` có thêm `title` (không bắt buộc).

App tải theo ba tầng: máy chủ → bản đã lưu lần trước (nghe được khi mất mạng, yêu cầu UI-44) → sách mẫu trong app.
Màn hình ghi rõ nguồn ("Máy chủ" / "Đã lưu" / "Bản mẫu") và nói nguồn trong câu giới thiệu.

## Chạy cả hệ thống trên máy

```powershell
# 1. Môi trường Python (một lần)
py -3.12 -m venv .venv
.venv\Scripts\pip install -r backend\requirements-dev.txt -r backend\requirements-ai.txt

# 2a. Backend dữ liệu thử
$env:VLM_MODE="mock"; .venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000

# 2b. Hoặc backend gọi module AI (điền ai\.env trước: copy ai\.env.example)
$env:VLM_MODE="ai"; .venv\Scripts\python -X utf8 -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000

# 3. App: emulator dùng sẵn http://10.0.2.2:8000; điện thoại thật đổi địa chỉ trong Cài đặt (người hỗ trợ)
cd frontend; flutter run
```

Docker: `docker compose up --build` (image gồm `ai/` rút gọn; khóa lấy từ `ai/.env` lúc chạy, không nằm trong image).

## Kiểm thử

| Phần | Lệnh | Kết quả 26/11/2026 |
|---|---|---|
| Backend (gồm 26 test cầu nối AI, 12 test chặn lặp) | `cd backend; ..\.venv\Scripts\python -X utf8 -m pytest -q` | 52 passed |
| Module AI | `cd ai; ..\.venv\Scripts\python -X utf8 -m pytest -q --ignore=tests/test_finetune.py` | 157 passed |
| App | `cd frontend; flutter analyze; flutter test` | No issues; 84 passed, 3 skipped (cần backend thật) |

Chạy thử đầu-cuối trên emulator với backend mock: thư viện tải từ máy chủ (3 cuốn, nhãn "Máy chủ"), chụp → mô tả
→ đọc từng câu tô vàng. Chế độ `ai` với pipeline thật: `/health` báo đúng model, ảnh tối bị cổng chặn đúng câu
hướng dẫn; lỗi mô hình (khóa hết hạn, HTTP 401) ra 502 `VLM_ERROR` câu tiếng Việt.

### Chạy với mô hình thật (26/11/2026)

Gemma 4 E4B (`lmstudio-community/gemma-4-E4B-it-GGUF`, Q4_K_M 5,34 GB + mmproj 0,99 GB) chạy bằng LM Studio 0.4.29
trên laptop RTX 5060 8 GB: nạp 9,9 giây, dùng 5,9/8,1 GB bộ nhớ GPU. `ai/.env` (không có khóa, không lên git):

```
VLM_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_MODEL=google/gemma-4-e4b   # đặt rõ: bỏ trống thì module AI lấy mô hình đầu tiên, có thể là mô hình embedding
LMSTUDIO_REASONING_EFFORT=none
```

Nạp: `lms load gemma-4-e4b-it --identifier google/gemma-4-e4b --gpu max --context-length 8192` (cùng tên mô hình với lệnh benchmark của Phúc), rồi `lms server start`.

| Ảnh (Wikimedia Commons) | Thời gian phía máy chủ | Nhận xét |
|---|---|---|
| Biểu đồ dân số Việt Nam 1950–2017 | 22,5 s lần đầu (mô hình vừa nạp), 9,6 s qua app | Đúng loại, trục, khoảng năm, xu hướng |
| Sơ đồ vòng đời phần mềm | 6,8–7,0 s | Đúng 6 khối và tỉ lệ; gọi nhầm là "biểu đồ"; **bỏ sót hai mũi tên quay vòng** |
| Bản đồ hành chính Việt Nam | 7,4 s | Đọc đúng chú giải 1–10 |
| Hỏi "Năm nào dân số cao nhất…" | 3,5 s | Đúng năm, số "khoảng chín mươi triệu" hơi thấp (ảnh ~95 triệu) |

Trên app (máy ảo, "Đọc ảnh có sẵn"): ảnh → máy chủ → lời mô tả đọc từng câu, nhãn loại trang đúng ("Biểu đồ").

Lỗi bỏ sót mũi tên trùng với phát hiện của Phúc cùng ngày: lỗi lớn nhất của Gemma là quan hệ, chiều mũi tên, và
chỉ số từ khóa không bắt được ([chấm rubric mẫu, mục 6](../ai/evaluation/reports/danh_gia_model.md), ca
`cycle_03`). Reasoning để tắt theo [đánh giá model, mục 4](../ai/evaluation/reports/danh_gia_model.md).

Hai lỗi tìm ra khi chạy thật:

1. Loại trang luôn là `mixed` vì B0 trả `image_type="unknown"`. Đã sửa ở cầu nối: `guess_page_type()` lấy loại từ câu
   đầu lời mô tả ("Chủ đề: Đây là một biểu đồ…"), sau đó mới tới phần tóm tắt.
2. Prompt `ask_calc_v1` (dòng 11) bảo mô hình **tự viết số bằng chữ**; cùng một câu hỏi, lần thì "hai nghìn mười bảy",
   lần thì "hai không hai mốt bảy" (sai). Hàm `speech.vn_numbers.words(2017)` của module AI đọc đúng "hai nghìn không
   trăm mười bảy". Đề xuất cho Phúc: prompt để mô hình giữ chữ số, mã đổi sang chữ bằng `prepare_for_speech()`.

## Việc còn lại

- Đo thời gian trên điện thoại thật.
- Phúc: sửa prompt `ask_calc_v1` theo lỗi 2 ở trên.
- Phúc: cổng chất lượng chặn nhầm hình nền đen. "Vòng đời Mặt Trời" (Commons, rõ nét) bị báo "Ảnh quá tối": độ sáng
  trung bình 24,9 < `dark_mean` 60, nhưng std 61,2 và độ nét Laplacian 1.467,8 rất cao; sơ đồ vòng đời phần mềm suýt bị
  chặn (độ sáng 64,3). Hình vũ trụ, ban đêm trong SGK hay có nền đen. Đề xuất: quy tắc "tối" xét cả độ tương phản như quy
  tắc "cháy sáng" (ví dụ tối khi độ sáng thấp VÀ std thấp).
  (Cập nhật 27/11, Phúc: chạy lại trên ảnh đang có, cổng máy chủ **vẫn chặn** hình này vì trung bình 24,9 < ngưỡng chặn mới
  `dark_mean` 30. App đã có hai lớp kiểm trên máy xét thêm tương phản nên cho qua, nhưng máy chủ vẫn chặn; chưa sửa máy chủ.)
- Hỏi bằng giọng nói: chỉ kiểm được trên điện thoại thật (STT của emulator không có micro/mạng).
- Phúc: hai test của `ai/` hỏng trên Windows do môi trường (thiếu font DejaVu; đọc file không chỉ định
  `encoding="utf-8"`), chạy được với `-X utf8`; trên CI (Ubuntu) cài `fonts-dejavu-core`.
- Nam: duyệt mã lỗi mới `AI_NOT_CONFIGURED` và trường `title` của trang thư viện.

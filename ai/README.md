# Module AI (`ai/`)

Phần AI của hệ thống: ảnh trang sách đã chụp → kiểm tra chất lượng ảnh → mô tả bằng VLM → hỏi đáp → chuẩn bị đọc ra giọng nói.
Backend (Nam) chỉ cần gọi `pipeline.py`. Hợp đồng đầu ra: `contract/` (bản nháp v0.1; backend đã ánh xạ sang API v1, xem `docs/TICH_HOP.md`, chờ cả nhóm duyệt).

```
pipeline.py            describe_page(), ask_page()  <- điểm vào cho backend
capture/quality.py     cổng chất lượng ảnh (chặn ảnh tối/mờ nặng; cảnh báo ảnh hơi tối/mờ) + câu hướng dẫn chụp lại
vlm/                   gọi VLM: providers (OpenRouter/Google/LM Studio), client (HTTP), describer (mô tả, nhận
                       prompt_id b0/b0e/b0g), b1 (hai bước), ask (hỏi đáp), calc (tính biểu thức do model viết),
                       common (phần dùng chung), list_models (liệt kê model của nhà cung cấp)
speech/                chuẩn hóa văn bản cho TTS (số, đơn vị ra chữ); chưa có engine STT/TTS
contract/              mô hình Pydantic, JSON Schema, ví dụ của DescriptionResult và AnswerResult
prompts/               prompt có phiên bản (b0_v1, b0e_v1, b0g_v1, b1_*, ask_v1, ask_calc_v1)
evaluation/            benchmark, chạy thực nghiệm, báo cáo (xem mục Đánh giá bên dưới)
finetune/              bộ sinh tập huấn luyện tổng hợp (dữ liệu chỉ ở máy tác giả)
external_data/         khảo sát, tải, kiểm tra trùng, phân mục và phân vai train/val/test các bộ dữ liệu Hugging Face (dữ liệu ở data/external/, không có trong repo)
docs/textbook/         hướng dẫn nạp ảnh SGK
tests/                 kiểm thử, không gọi mạng
```

## Quy cách đầu ra (chốt ngày 27/11/2026)

Nguồn duy nhất về hành vi của VLM; tài liệu khác dẫn tới mục này. Theo định hướng Phúc và Toàn trao đổi lại với giảng viên hướng dẫn (Phúc thuật lại).

**Người dùng:** học sinh khiếm thị lớp 1–12 và sinh viên khiếm thị đại học, cao đẳng. Hệ thống **hỗ trợ học, không làm bài hộ**, không thay giáo viên.

**Ảnh đầu vào:** trang sách, vở, bài giảng trên bảng đen hoặc tivi; công thức, sơ đồ, biểu đồ, bảng; vật thể, không gian. Kèm câu hỏi của người dùng, thành chuỗi nhiều lượt.

| # | Quy tắc đã chốt |
|---|---|
| 1 | **Không giải bài tập, không đưa đáp án.** Ảnh trang sách: chỉ diễn giải. |
| 2 | Người dùng không nhìn thấy nên **phải đọc cho họ nội dung trong ảnh**. Biểu đồ không đủ dữ liệu để đọc chính xác thì được nói ở **mức tương đối** (và nói rõ là tương đối). |
| 3 | Ảnh bài tập: **đọc đề trước**. Nếu người dùng hỏi tiếp thì xử lý **tùy câu hỏi**, vẫn theo quy tắc 1. |
| 4 | **Bài giải mẫu in sẵn** trong ảnh: được đọc thoải mái. |
| 5 | VLM **chỉ trả lời điều được hỏi**; không được yêu cầu thì không nói thêm (không tự thêm nội dung, gợi ý hay suy diễn). |
| 6 | Hỏi **chênh lệch giữa hai cột** của biểu đồ: được nói thẳng kết quả. |
| 7 | Ảnh gửi **không kèm câu hỏi**: chỉ nói ngắn gọn **phần nổi bật nhất** trong ảnh, hoặc đọc **các đề mục lớn**. |
| 8 | Ảnh **không đọc được**: tự báo là không đọc được và hướng dẫn chụp lại. |
| 9 | Sau khi đọc đề: được đọc lại đề, dữ kiện trên trang và **giải nghĩa từ ngữ, khái niệm trong đề**; **không** chỉ cách làm, không gợi ý hướng giải, không đưa kết quả. |
| 10 | Trang có **đánh dấu là bài kiểm tra hoặc bài thi**: chỉ **mô tả theo hình ảnh có sẵn trong trang**, không nói gì khác. Quy tắc này thắng mọi quy tắc cho phép ở trên (giải nghĩa từ, chênh lệch hai cột). |
| 11 | Câu hỏi cần **kiến thức không có trong ảnh**: nói là trang không ghi, rồi **dừng**. Ngoại lệ duy nhất: giải nghĩa từ ngữ, khái niệm trong đề (quy tắc 9). |
| 12 | App xét **cả phần chữ lẫn phần hình** trên trang. Điều được hỏi **trùng yêu cầu của bài tập** trên trang: **chỉ đọc dữ kiện**, không tính, không so sánh hộ (thắng quy tắc 6). **Không trùng**, hoặc trang **không có bài tập**: được trả lời để hiểu hình, kể cả nói chênh lệch hai cột. |

**Luồng sử dụng (Phúc chốt 27/11):** chụp ảnh → không đọc được thì báo và hướng dẫn chụp lại → VLM **mô tả ngắn** → app hỏi một câu cố định ("Bạn muốn hỏi gì về ảnh này?", VLM không tự đặt câu hỏi) → người dùng hỏi → VLM trả lời → hỏi tiếp trên cùng ảnh hoặc chụp ảnh mới. App chưa theo phần mô tả ngắn và câu mời.

**Format trả lời (phương án A):** chỉ trả lời đúng câu được hỏi, **câu đầu tiên là câu trả lời**, văn nói, không ký hiệu định dạng. Chỉ thêm lời khi cần cho đúng hoặc để người dùng biết giới hạn (ước lượng tương đối, trang không ghi, chỗ không đọc rõ, câu trùng bài tập). Câu mẫu cho các tình huống này là đề xuất, chưa chốt câu chữ. Người dùng yêu cầu đọc nguyên văn hoặc cả trang thì được trả lời dài.

**Mặc định tạm thời** (đề xuất của trợ lý, Phúc có thể nới sau): phép tính khác ngoài chênh lệch hai cột (tổng, trung bình, diện tích, chu vi, cạnh huyền) **không làm**. Quy tắc mới do Phúc bổ sung dần.

**Giới hạn đã biết của quy tắc 12:** nếu ảnh không chứa phần đề, app không biết đó là bài tập; câu hỏi diễn đạt khác đề có thể không được nhận ra là trùng. Cần đo riêng.

**Ngoài phạm vi hiện tại:** chấm bài làm viết tay của chính người dùng. Theo Phúc, người khiếm thị không viết chữ như người sáng mắt, và sách dành riêng cho người khiếm thị rất ít.

**Mã hiện tại chưa khớp** (chưa sửa):

| Chỗ | Lệch |
|---|---|
| `prompts/ask_v1.txt`, `ask_calc_v1.txt` | Không có quy tắc cấm giải bài. Cả hai cho tính **mọi** câu cần tính, kể cả khi là bài tập; mã tính qua `vlm/calc.py` (mặc định `calc=True`). Chênh lệch hai cột thì được phép (quy tắc 6) |
| `pipeline.describe_page` | Ảnh không kèm câu hỏi hiện được mô tả đầy đủ cả trang, trái quy tắc 7 |
| `prompts/b0g_v1.txt` | Mô tả bốn mục gồm cả "ý nghĩa" dù không được hỏi; không có quy tắc cho ảnh bài tập |
| `finetune/` | Sinh câu hỏi tính toán kèm đáp án và câu gợi ý cuối lời mô tả (xem README của thư mục) |

**Kiến trúc và hướng model:** hybrid client-server. Online: model teacher trên server tự host (dự kiến A100) hoặc nhà cung cấp cloud. Mất mạng hoặc mạng chập chờn: model student của đề tài. Server trả văn bản, client lo TTS. Model riêng của đề tài định hướng **họ Gemma**; thầy cho phép fine-tune hoặc distill, **ưu tiên distill**. Laptop dùng cho nghiên cứu, benchmark. Nghiên cứu tách hai cấp: **model-level** (prompt, fine-tune, PEFT, distill, quantization) và **system-level** (OCR, RAG, tiền xử lý, phát hiện đối tượng, định tuyến, kiểm tra); đo được riêng đóng góp từng phần.

**Hệ quả cho đánh giá:** điểm đáp án VMMU đo khả năng giải đề, **không phải** chất lượng sản phẩm. Cần thêm phép đo **tuân thủ** (gặp ảnh bài tập: đọc đề đúng và không lộ đáp án), đo bịa, đọc đúng số, tên riêng, dấu.

## Chạy

```bash
cp .env.example .env              # điền khóa; KHÔNG commit .env
uv run pytest -q                  # kiểm thử, không gọi mô hình thật
uv run python vlm/list_models.py --provider lmstudio
```

```python
from pipeline import describe_page, ask_page

result = describe_page("trang.jpg", provider="lmstudio")      # DescriptionResult
if result.status == "unreadable":
    ...                                                       # result.summary_vi là lời hướng dẫn chụp lại
answer = ask_page("trang.jpg", "Cột nào cao nhất?")            # AnswerResult; câu tính toán hiện do mã tính (chưa khớp quy cách, xem trên)
# Câu hỏi về vị trí/hướng: nên chỉ truyền ảnh; truyền description=... làm kết quả tệ hơn (đo trên dev)
```

Lỗi vận hành (mạng, HTTP, cấu hình, ảnh hỏng) trả `status="error"` kèm `error`, không ném ngoại lệ.

Model có chế độ suy nghĩ (Gemma 4): đặt biến môi trường `LMSTUDIO_REASONING_EFFORT=none` để tắt, nếu không model dùng hết `max_tokens` để nghĩ và trả `empty_response`. Không đặt thì payload không đổi (Qwen). Đo ngày 2026-11-26: ở `max_tokens` 2000, bật và tắt reasoning ngang nhau trên dev; ở 600 thì bật không dùng được (xem [đánh giá model](evaluation/reports/danh_gia_model.md), mục 4).

## Cổng chất lượng ảnh (`capture/quality.py`)

Điện thoại có thêm hai lớp kiểm trước cổng này (đang ngắm và vừa chụp), xem [`frontend/README.md`](../frontend/README.md#hướng-dẫn-chụp-thêm-27112026). Cổng ở đây vẫn là lớp kiểm cuối.

Hiệu chỉnh ngày 27/11/2026 trên ảnh thật ([báo cáo](evaluation/reports/capture_gate_anh_that_20261127.md)):

- **Chặn** (trả `status="unreadable"` ngay, không gọi VLM): ảnh gần như đen (`dark`), mờ nặng (`blur`), hoặc cháy sáng toàn ảnh (`glare`: sáng trung bình > 235 và gần như không có tương phản; chủ ý, có test `test_pipeline.py`). Lý do nằm trong `uncertainties` dạng `capture_gate:<lý do>`.
- **Cảnh báo** (`warnings`, vẫn gọi VLM): ảnh hơi tối hoặc hơi mờ.
- Lỗi phụ thuộc nội dung (chói che một phần, hình bị cắt mất mép) không đo được bằng thống kê ảnh; prompt `b0g_v1` xử lý.

> Lưu ý: docstring của `capture/quality.py` và báo cáo 27/11 chỉ nêu tối và mờ nặng là mức chặn, nhưng code vẫn chặn `glare`. Trên SGK, glare chặn 12 trang gần như trắng (trang lót sau bìa), không ảnh hưởng trang nội dung. Cần sửa docstring và báo cáo cho khớp với code.

## Điểm yếu đã biết (kiểm tra ngày 27/11/2026)

| Điểm yếu | Trạng thái | Bằng chứng |
|---|---|---|
| Cổng chặn nhầm ảnh tốt | Đã cải thiện: 15,1% → 1,3% trên VizWiz tốt | `evaluation/reports/capture_gate_anh_that_20261127.md` |
| Cổng chặn nhầm hình nền đen rõ nét | **Còn.** Chạy lại 27/11: hình "Vòng đời Mặt Trời" (trung bình 24,9, độ lệch chuẩn 61,2, Laplace 1467,8) và một ảnh tương tự vẫn bị chặn là `dark`. Bộ kiểm trên điện thoại xét thêm tương phản nên cho qua; cổng máy chủ chưa sửa | `docs/TICH_HOP.md`, `frontend/README.md` |
| Báo nhầm "không đọc được" trên trang SGK (5/32, b0g_v1) | Chưa cải thiện. Nguyên nhân là VLM, không phải cổng; số đo gốc là Qwen 4B, chưa đo lại với Gemma | `danh_gia_model.md`, mục 3 |
| Ảnh bảng đen và màn hình điện thoại | Chưa có ảnh kiểm tra (cần khoảng 20 ảnh) | báo cáo cổng 27/11, mục 4 |
| Hỏi đáp có mô tả làm câu về vị trí tệ đi | Chưa cải thiện; README vẫn khuyên chỉ truyền ảnh | `danh_gia_model.md`, mục 3 |
| Bộ lọc `chat_vi` chưa đo thật | Đã nối vào đường gọi của describer, ask và b1, có test; chưa đo hiệu quả trên đầu ra thật | `vlm/common.py`, `tests/test_contract_and_describer.py` |
| Lặp câu trong đầu ra mô hình nhỏ | Đã xử lý ở backend (`repetition.py`), không nằm trong `ai/` | `docs/TICH_HOP.md` |
| Gemma bật suy nghĩ làm `empty_response` | Đã xử lý: `LMSTUDIO_REASONING_EFFORT=none` | `evaluation/reports/danh_gia_model.md`, mục 4 |
| Tập test chưa chạy | Benchmark tổng hợp: chưa chạy. VMMU test: đã chạy một lần ngày 27/11 (21/138, `calc=True`) | `NHAT_KY_PHAT_TRIEN.md` |
| Chấm tay bằng hai người | Chưa cải thiện; hiện chỉ có chấm 4 ca bởi trợ lý | `danh_gia_model.md`, mục 6 |
| Hợp đồng đầu ra còn nháp v0.1 | Chưa cải thiện; ánh xạ API v1 đã ghi trong `docs/TICH_HOP.md` | `contract/README.md` |
| Giấy phép GPL/NC khi huấn luyện | Chưa cải thiện; cần hỏi thầy | nhật ký 23/11 |

## Các trạng thái cần hệ thống xử lý

| `status` | Nghĩa | Việc của app |
|---|---|---|
| `ok`, `partial` | Có lời diễn giải (`partial`: bị cắt do giới hạn độ dài) | Đọc `interpretation_vi` |
| `unreadable` | Ảnh không đọc được; `summary_vi` là hướng dẫn chụp lại | Đọc `summary_vi`, mở camera lại |
| `error` | Lỗi vận hành, `error.retryable` cho biết có nên thử lại | Báo lỗi hoặc thử lại |

## Đánh giá (`evaluation/`)

Mọi lệnh chạy từ thư mục `ai/` (`uv run python ...`). Dữ liệu benchmark ở `data/benchmark/` **chỉ có ở máy tác giả**. Báo cáo kết quả ở `evaluation/reports/` (liên kết từ `README.md` gốc).

| Thư mục | Vai trò |
|---|---|
| `generators/` | sinh và kiểm tra benchmark tổng hợp (`generate_benchmark_v02.py`, `validate_benchmark.py`, `generate_chart*.py`), nạp ảnh SGK (`ingest_textbook.py`), tải ảnh Wikimedia (`fetch_commons_candidates.py`) |
| `runner/` | `run_b1_dev.py` (`--method b0e|b0g|b1` trên tập dev; `--reps`, `--max-tokens` mặc định 600), `survey_lmstudio.py` (khảo sát model LM Studio theo độ phóng ảnh/prompt), `run_qa_dev.py` (hỏi đáp trên câu hỏi dev; mặc định model Qwen, truyền `--model` để chạy model khác), `run_vmmu_val.py` (trắc nghiệm VMMU, `--split val|test`, cần `uv run --with pyarrow`), `run_openvivqa_dev.py` (hỏi đáp mở, mẫu dev), `run_vmmu_raw.py` (VMMU gọi thẳng model). Các runner VMMU đo khả năng chọn đáp án đề thi, không phải chất lượng sản phẩm |
| `reporting/` | `proposition_check.py` (chuẩn hóa dấu "8 phẩy 5" và nhãn "Thứ Hai" ↔ "Thứ 2" từ 26/11; vẫn chỉ đếm số và tên, không chấm quan hệ), `repeat_stats.py`, `survey_report.py`, `qa_score.py`, `capture_gate_eval.py`, `archive_runs.py`, `visgkcap_stats.py` (thống kê ViSGKCap, cần `pyarrow`), `watch_progress.py` (xem tiến độ benchmark đang chạy), bộ chấm rubric (`create_scorecards`, `validate_score`, `finalize_score`, `summarize_scores`) |
| `reports/` | báo cáo Markdown |
| `rubrics/` | `rubric_v1.md` (C1–C6, chấm tay) |
| `legacy_b0/` | quy trình B0 theo phiên (2026-10) và script thử OpenRouter gốc; chỉ để tái hiện số liệu cũ |
| `records_*/`, `runs/`, `sessions/`, `scores/` | bản ghi đầu ra từng lần chạy, **không** có trong git |

Quy ước: chỉ số phủ mệnh đề là từ khóa thô, chạm trần và không đo độ bịa; không dùng làm điểm rubric. Tập test của benchmark tổng hợp chưa chạy (giữ đóng băng); không sửa ground truth sau khi xem đầu ra model.

## Lịch sử cập nhật

Ai sửa file này, theo lịch sử git. "(AI hỗ trợ)" là commit có ghi trợ lý AI trong lời nhắn; commit cũ không ghi thì không suy ra là không dùng.

| Ngày | Người | Việc | Commit |
|---|---|---|---|
| 27/11/2026 | Phúc (AI hỗ trợ) | docs: gộp 6 báo cáo đánh giá model thành 1, dọn nội dung cũ và link hỏng, ghi luồng sử dụng | `442be9d` |
| 27/11/2026 | Phúc (AI hỗ trợ) | docs: định hướng mới, 12 quy tắc đầu ra của VLM, nhật ký 27/11 (chưa sửa prompt, calc, bộ sinh dữ liệu) | `a0cdcd9` |
| 26/11/2026 | Phúc (AI hỗ trợ) | fix(ai): sửa bộ chấm và kết quả Gemma trên dev; thêm b0g và báo cáo | `8ad80a9` |
| 23/11/2026 | Phúc (AI hỗ trợ) | feat(vlm): optional LMSTUDIO_REASONING_EFFORT for Gemma 4; docs: base model moving to Gemma 4 E4B | `28fae5e` |
| 19/11/2026 | Phúc (AI hỗ trợ) | revert: drop fine-tune prep (ft_describe_v1 prompt, spoken export format) | `92b30d1` |
| 19/11/2026 | Phúc (AI hỗ trợ) | docs: consolidate markdown (26 -> 13) and refresh README | `1a934b3` |
| 18/11/2026 | Phúc (AI hỗ trợ) | feat(ai): capture quality gate, unreadable prompt, QA with code-computed arithmetic, TTS text prep; split vlm modules | `a878419` |

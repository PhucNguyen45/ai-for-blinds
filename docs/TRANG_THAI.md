# Trạng thái hệ thống — 21/08/2026

Ghi lại cho cả nhóm. Nhánh này đưa repo từ chỗ **không khởi động được** lên
chỗ **chạy đầu cuối**: app Android chụp ảnh, backend gọi mô hình, kết quả được
đọc to bằng tiếng Việt và lưu lại để ôn tập.

## Sáu endpoint đều trả 200

| Endpoint | Trạng thái | Ghi chú |
|---|---|---|
| `GET /` | 200 | Báo luôn model đang phục vụ |
| `POST /describe` | 200 | Qwen3-VL 8B qua OpenRouter |
| `POST /ocr` | 200 | Không cần PaddleOCR, xem mục dưới |
| `POST /tts` | 200 | Edge TTS, giọng `vi-VN-HoaiMyNeural` |
| `POST /stt` | 200 | PhoWhisper tiny bản CTranslate2 |
| `POST /rag/query` | 200 | ChromaDB + embedding tiếng Việt |

## Ba quyết định kỹ thuật cần cả nhóm biết

### 1. Tầng VLM không còn khoá cứng vào Gemini

`backend/services/vlm_service.py` nói chuyện với **bất kỳ endpoint tương thích
OpenAI**. Đổi mô hình chỉ bằng biến `VLM_MODEL` trong `.env`, không sửa code.
Dev đi qua OpenRouter; khi triển khai on-premise thì trỏ `OPENROUTER_BASE_URL`
vào vLLM chạy nội bộ — vẫn giao thức đó, không phải viết lại.

Đo thực tế trên một trang SGK có biểu đồ (`scripts/eval_vlm.py`):

| Model | Thời gian | Số liệu | Kết luận |
|---|---|---|---|
| `qwen3-vl-8b-instruct` | 2,9s | đúng hết | **đang dùng** |
| `qwen3-vl-30b-a3b-instruct` | 9,3s | đúng hết | chậm hơn, không lợi hơn |
| `nemotron-nano-12b-vl:free` | 14,2s | đúng hết | đọc sai chữ tiếng Việt |
| `gemma-4-*:free` | — | — | 429, hạn mức dùng chung đã cạn |

Bản 8B chạy được trên GPU 16GB, dễ xin hơn 24GB cho bản 30B.

### 2. `/ocr` đi qua VLM, không dùng PaddleOCR

Ràng buộc đề tài: một mô hình gánh cả OCR lẫn mô tả. `ocr_service` tự chuyển
sang `vlm_service.transcribe()` khi không có PaddleOCR. Đọc trang SGK chính xác
từng chữ, kể cả dấu. Đổi lại, repo bớt được `paddleocr` và `paddlepaddle` —
khoảng vài GB phụ thuộc và một điểm hỏng.

### 3. PhoWhisper thay Whisper gốc

Đo bằng `scripts/bench_stt.py`, năm câu hỏi kiểu học sinh:

| Model | WER | Thời gian |
|---|---|---|
| `diepho/PhoWhisper-tiny-ct2` | **2,0%** | 1,8s |
| `diepho/PhoWhisper-small-ct2` | 8,5% | 12,7s |
| `whisper small` | 13,7% | 6,7s |
| `whisper base` | 28,9% | 2,5s |

Whisper base nghe "vì sao" thành "vì sau"; PhoWhisper tiny nghe đúng. Bản tiny
chỉ khoảng 75MB, nhanh nhất, lại chính xác nhất — không cần bản lớn hơn.

Lưu ý: năm câu này do Edge TTS đọc, giọng sạch, không có tạp âm. Trước khi
chốt cho báo cáo, cần đo lại bằng giọng người thật trong phòng học.

## Chạy thế nào

```
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements-dev.txt
copy .env.example .env        # rồi điền OPENROUTER_API_KEY
uvicorn backend.main:app --reload --port 8000
```

```
cd frontend
flutter pub get
flutter run --dart-define=BACKEND_URL=http://10.0.2.2:8000
```

Máy thật thì thay `10.0.2.2` bằng IP LAN của máy chạy backend, hoặc nhập thẳng
trong màn hình Cài đặt của app.

## Script mới

| Script | Việc |
|---|---|
| `scripts/eval_vlm.py` | Chấm điểm nhiều VLM trên cùng bộ ảnh, tự kiểm quy tắc văn nói |
| `scripts/bench_stt.py` | Đo WER và tốc độ các model nhận dạng giọng nói |
| `scripts/ingest_sgk.py` | Nạp SGK vào ChromaDB, cắt theo tiêu đề bài |
| `scripts/eval_vqa.py` | Chấm model trên ViInfographicVQA — ảnh có sẵn đáp án |
| `scripts/download_datasets.py` | Tải các bộ dữ liệu ảnh tiếng Việt |

## Nâng cấp đợt hai

**Hỏi thẳng về ảnh vừa chụp.** Nghe mô tả xong, nhấn "Hỏi về ảnh", nói câu hỏi,
nhấn lần nữa để gửi. Ảnh được giữ lại nên không phải chụp lại. Đường đi:
ghi âm → `/stt` → `/describe` kèm trường `question` → đọc đáp án.

**Nhớ kết quả cũ.** Chụp lại đúng trang đã chụp thì trả lời ngay, không gọi lại
mô hình: **4,66 giây xuống 0,0015 giây**, và không tốn thêm tiền. Nhớ 64 ảnh
gần nhất, khoá theo mã băm của ảnh cộng với tên model.

**Tự thử lại khi nhà cung cấp chặn.** Gặp 429 hoặc 5xx thì chờ 1, 2, 4 giây rồi
thử lại, tối đa ba lần. Trước đây một lần chặn là học sinh nghe im lặng.

**Nhiệt độ 0 cho việc tra cứu.** Đọc chữ và trả lời câu hỏi về ảnh là tra cứu,
không phải sáng tác. Ở nhiệt độ 0,3 cùng một câu hỏi lúc trả lời đúng lúc bảo
"không thấy thông tin trong ảnh". Hạ về 0 thì năm lần chạy cho cùng một kết quả.
Phần mô tả tự do vẫn giữ 0,3.

**Sửa quy tắc đọc số.** Quy tắc cũ bắt viết số thành chữ, model làm nửa vời và
sinh ra câu "tám mươi lăm **point** tám". Nay giữ nguyên chữ số vì máy đọc phát
âm đúng, chỉ bắt viết chữ cho ký hiệu: phần trăm, độ C, mét vuông. Cấm hẳn từ
tiếng Anh.

### Hai lỗi chỉ lộ ra khi chạy app thật

Cả hai đều không thấy khi thử bằng `curl`.

| Lỗi | Hậu quả | Sửa |
|---|---|---|
| File ghi âm gửi lên không kèm loại MIME | `/stt` trả 400 mọi lần — nút Hỏi đáp chưa từng chạy được từ app | Suy MIME từ đuôi file, giống phần ảnh |
| Một lần TTS quá hạn là tắt hẳn giọng server cả phiên | Nghe giọng máy yếu suốt buổi dù mạng chỉ nghẽn một lúc | Chờ hai lần lỗi liên tiếp mới tắt, một phút sau tự thử lại. Thời gian chờ tính theo độ dài văn bản |

## Còn phải làm

- **Kho SGK mới có dữ liệu mẫu** — bốn mục Địa lý 10 do tự viết, chỉ để kiểm
  thử. Cần nội dung thật.
- **PostgreSQL chưa được route nào dùng.** Model và migration có sẵn, chưa nối.
- **Chưa có test backend, CI rỗng.** Nhánh `phuc` đã có sẵn cả hai.
- **Ba nhánh đang phân kỳ** — `main`, `nam`, `phuc` và nhánh này. Nên gộp sớm.
- **Đo lại STT bằng giọng thật** trước khi đưa số vào báo cáo.

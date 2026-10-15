# SgBe — Trợ lý AI đọc học liệu cho học sinh khiếm thị

Đề tài NCKH 2026–2027, Học viện Kỹ thuật Quân sự. Nhóm: Toàn (AI & giọng nói), Nam (backend), Phúc (app Flutter).

```
backend/          FastAPI: API v1, lớp mô hình, lưu trữ   (Nam)
prompts/v1/       prompt theo loại trang                  (Toàn)
data/library/     kho mô tả SGK, mỗi sách một manifest    (Nam)
scripts/          số hóa sách
docs/API_v1.md    hợp đồng API — đọc file này trước khi làm app
app/              app Flutter                              (Phúc — chép repo cũ vào đây)
eval/             script và bộ dữ liệu đánh giá            (Toàn)
```

## Chạy máy chủ (Windows, lần đầu)

Chạy **từng lệnh một**, chờ lệnh trước xong mới gõ lệnh sau.

Git Bash / MSYS2 (UCRT64):

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Mở `http://localhost:8000/docs` để thử từng endpoint ngay trên trình duyệt.

Mặc định `VLM_MODE=mock`: trả dữ liệu giả, không cần mạng, không tốn credit — đủ để Phúc làm app.

## Chuyển sang mô hình thật

Sửa `backend/.env`:

```
VLM_MODE=openai
VLM_BASE_URL=https://openrouter.ai/api/v1     # OpenRouter
VLM_API_KEY=sk-or-...                          # khóa riêng, không đưa lên git
VLM_MODEL=qwen/qwen3-vl-30b-a3b-instruct
```

Sang máy chủ on-premise chạy vLLM: chỉ đổi ba dòng trên, ví dụ `VLM_BASE_URL=http://<ip>:8001/v1`, `VLM_MODEL=Qwen/Qwen3-VL-8B-Instruct`. Không sửa code.

## Chạy bằng Docker

```
docker compose up --build
```

## Kiểm thử

```
cd backend
pytest -q
```

## Số hóa một cuốn sách

Chụp từng trang, đặt tên có số trang (`trang_012.jpg`), rồi:

```
python scripts/digitize_book.py --book lsdl4-ktt --title "Lịch sử và Địa lí 4" --images anh/lsdl4
```

Kết quả ở `data/library/lsdl4-ktt/manifest.json`, mỗi trang `reviewed: false`. Người duyệt sửa `description` rồi đặt `reviewed: true`; chạy lại script sẽ không ghi đè trang đã duyệt.

## Đổi prompt

Tạo thư mục `prompts/v2/` (chép từ v1 rồi sửa), đặt `PROMPT_VERSION=v2` trong `.env`. Mỗi kết quả đều ghi `prompt_version`, bộ nhớ đệm tách theo phiên bản nên không lẫn kết quả cũ.

## Nhật ký

Mỗi yêu cầu ghi một dòng vào `data/logs/requests.jsonl` (loại trang, mô hình, phiên bản prompt, độ trễ, lỗi). Đây là đầu vào cho bảng đánh giá và số đo p50/p95.

## Việc tiếp theo (chưa làm)

- PostgreSQL (lộ trình gói 1.3): hiện lưu bằng file, đủ cho MVP; thêm khi kho sách lớn.
- `/v1/describe` trả dạng stream để TTS đọc câu đầu sớm.
- STT PhoWhisper trong `backend/app/stt.py` (Toàn).

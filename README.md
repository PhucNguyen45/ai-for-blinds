# VLM Server

Server FastAPI tích hợp Gemini Vision để app mobile gửi **ảnh + câu hỏi** → server trả về câu trả lời do VLM phân tích ảnh.

## Cấu trúc

```
.
├── app/
│   ├── main.py        # FastAPI app, endpoint /api/ask
│   ├── vlm.py         # Tích hợp Gemini
│   └── config.py      # Cấu hình từ .env
├── static/
│   └── index.html     # Trang demo (có camera capture)
├── requirements.txt
├── .env.example
└── README.md
```

## Cài đặt

1. **Lấy API key Gemini** tại https://aistudio.google.com/apikey

2. **Cài dependencies**:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Tạo `.env`** từ template:
   ```bash
   cp .env.example .env
   ```
   Sửa `GEMINI_API_KEY=...` bằng key thật.

   > **Lưu ý về `GEMINI_MODEL`**: mặc định là `gemini-3.0-pro`. Nếu API trả lỗi "model not found", thử đổi sang `gemini-2.5-pro`, `gemini-2.5-flash`, hoặc `gemini-2.0-flash`.

## Chạy server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Trang demo: http://localhost:8000/
- API docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/health

## API

### `POST /api/ask`

**Request** (`multipart/form-data`):
- `image` (file, required): Ảnh JPEG/PNG/WEBP/HEIC, ≤ 10MB
- `question` (string, required): Câu hỏi về ảnh

**Response 200**:
```json
{
  "answer": "Trong ảnh có một con mèo đang ngồi trên ghế sofa...",
  "model": "gemini-3.0-pro",
  "elapsed_ms": 1432
}
```

**Lỗi**:
- `400` ảnh rỗng / câu hỏi rỗng
- `413` ảnh quá lớn
- `422` ảnh không hợp lệ / VLM từ chối trả lời
- `500` lỗi server

### Test bằng curl

```bash
curl -X POST http://localhost:8000/api/ask \
  -F "image=@cat.jpg" \
  -F "question=Trong ảnh có gì?"
```

## Test từ điện thoại

1. Đảm bảo điện thoại và máy chạy server cùng mạng Wi-Fi.
2. Tìm IP máy server: `ipconfig` (Windows) / `ifconfig` (Mac/Linux).
3. Truy cập `http://<IP-máy>:8000/` từ trình duyệt mobile.
4. Bấm **"📷 Chụp ảnh"** → camera mở trực tiếp → chụp → gõ câu hỏi → gửi.

## Tích hợp từ app mobile native

### Android (Kotlin + OkHttp)
```kotlin
val client = OkHttpClient()
val body = MultipartBody.Builder()
    .setType(MultipartBody.FORM)
    .addFormDataPart("image", "photo.jpg",
        imageFile.asRequestBody("image/jpeg".toMediaType()))
    .addFormDataPart("question", question)
    .build()
val req = Request.Builder()
    .url("http://<server>:8000/api/ask")
    .post(body).build()
client.newCall(req).execute().use { /* parse JSON */ }
```

### iOS (Swift + URLSession)
Dùng `URLSession.upload(for:from:)` với multipart body — tương tự pattern trên.

## Cấu hình `.env`

| Biến | Mặc định | Mô tả |
|------|----------|------|
| `GEMINI_API_KEY` | (bắt buộc) | API key Google AI Studio |
| `GEMINI_MODEL` | `gemini-3.0-pro` | Tên model Gemini |
| `MAX_IMAGE_MB` | `10` | Giới hạn upload |
| `REQUEST_TIMEOUT_S` | `60` | Timeout gọi Gemini |
| `ALLOWED_ORIGINS` | `*` | CORS origins, ngăn cách bằng dấu phẩy |

## Production note

- Đặt `ALLOWED_ORIGINS` cụ thể (không để `*`).
- Chạy sau reverse proxy (nginx/Caddy) với HTTPS.
- Đặt rate limit (vd. `slowapi`).
- Cân nhắc lưu lịch sử hỏi đáp vào DB nếu cần.

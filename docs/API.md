# API Reference

Tất cả endpoints yêu cầu header: `X-API-Key: sgbe_dev_key_2024`

## VLM Server (port 8000)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/health` | Health check |
| GET | `/api/voices` | Danh sách giọng đọc |
| POST | `/api/ask` | Ảnh + câu hỏi → JSON |
| POST | `/api/ask-voice` | Ảnh + audio → MP3 |
| POST | `/api/tts` | Text → MP3 |

## AI Gateway (port 8001)

### POST /describe
Request: multipart `file` (image)
Response: `{"description": "..."}`

### POST /ocr
Request: multipart `file` (image)
Response: `{"text": "..."}`

### POST /stt
Request: multipart `file` (audio) + `language` (form)
Response: `{"text": "...", "segments": [...], "language": "vi"}`

### POST /tts
Request: `{"text": "...", "voice": "...", "emotion": "neutral"}`
Response: audio/mpeg binary

### POST /rag/query
Request: `{"question": "...", "n_results": 5, "grade": 10, "subject": "Sinh học"}`
Response: `{"answer": "...", "source": {...}, "sources": [...]}`

### POST /detect
Request: multipart `file` (image)
Response: `{"objects": [...], "object_count": N, "scene_description": "..."}`

### POST /sonify
Request: `{"data_points": [{"label": "...", "value": N}], "chart_type": "bar"}`
Response: `{"description": "...", "tones": [...], "summary": "..."}`

### POST /money — Nhận dạng mệnh giá tiền VNĐ
Request: multipart `file` (image)
Response: `{"data": {"denomination": "500000", "formatted": "500.000 đồng", "method": "vlm", "confidence": 0.95}}`

- `method`: `yolo` (nếu cấu hình `VND_YOLO_MODEL_PATH` hợp lệ) hoặc `vlm` (Gemini).
- `denomination` = `null` khi ảnh không phải tờ tiền Việt Nam.
- `503` khi không có phương thức nhận dạng khả dụng.
- Rate limit: 10/phút.

### POST /search — Truy hồi thông tin Internet (web + tin tức)
Request: `{"query": "Thủ đô của Việt Nam là gì?", "n_results": 5}`
Response: `{"data": {"query": "...", "results": [{"title": "...", "snippet": "...", "url": "...", "source": "web|news", "score": 0.98}]}}`

- Nguồn: DuckDuckGo (`web`) + RSS tin tức VnExpress/Dân Trí xếp hạng TF-IDF (`news`).
- Rate limit: 20/phút.

## Bộ nhớ khoảnh khắc học tập (Persistent Visual Memory)

Mỗi endpoint /moments yêu cầu header bổ sung:
- `X-Device-Id: <device_id>` — định danh thiết bị, phạm vi hóa dữ liệu (mỗi thiết bị chỉ xem dữ liệu của mình).
- `503` khi cơ sở dữ liệu không khả dụng.

### POST /moments — Lưu khoảnh khắc
Request: `{"title": "Công thức diện tích", "content": "S = πr²", "content_type": "text|description|ocr|image_description", "grade": 9, "subject": "Toán", "chapter": "...", "page_number": 12}`
Response: `{"success": true, "data": {"id": "...", "title": "...", "content": "...", "content_type": "...", "grade": 9, "subject": "Toán", "created_at": "..."}, "message": "Đã lưu khoảnh khắc học tập."}`

- Backend tự tạo embedding ngữ nghĩa (`all-MiniLM-L6-v2`) từ tiêu đề + nội dung.
- Rate limit: 30/phút.

### GET /moments — Danh sách khoảnh khắc
Response: `{"success": true, "data": [{"id": "...", "title": "...", "content": "...", "content_type": "...", "grade": ..., "subject": "...", "created_at": "..."}], "message": "Có N khoảnh khắc."}`

- Sắp theo thời gian tạo mới nhất trước (tối đa 100).
- Rate limit: 60/phút.

### DELETE /moments/{moment_id} — Xóa khoảnh khắc
Response: `{"success": true, "message": "Đã xóa khoảnh khắc học tập."}`

- `404` khi không thuộc về thiết bị.
- Rate limit: 30/phút.

### POST /moments/search — Tìm kiếm ngữ nghĩa
Request: `{"query": "Định lý Pytago", "n_results": 5}`
Response: `{"success": true, "data": {"query": "...", "results": [{"id": "...", "title": "...", "content": "...", "content_type": "...", "created_at": "...", "distance": 0.1}]}, "message": "Tìm thấy N kết quả."}`

- `distance` = khoảng cách cosine (càng nhỏ càng liên quan); kết quả xếp tăng dần.
- Rate limit: 30/phút.

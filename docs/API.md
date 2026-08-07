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

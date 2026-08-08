# Kiến trúc SgBe Vision

## Tổng quan

```
Mobile App (Flutter)
    │
    ├── http://localhost:8000  ─── VLM Server (app/)
    │       ├── /api/ask         → Gemini Vision + TTS
    │       ├── /api/ask-voice   → Voice Q&A
    │       └── /api/tts         → Text-to-Speech
    │
    └── http://localhost:8001  ─── AI Gateway (backend/)
            ├── /describe   → VLM Service (Gemini)
            ├── /ocr        → OCR Service (PaddleOCR)
            ├── /stt        → STT Service (faster-whisper)
            ├── /tts        → TTS Service (Edge TTS)
            ├── /rag/query  → RAG Service (ChromaDB)
            ├── /detect     → Detection Service (YOLOv8)
            ├── /money      → Money Service (YOLO VND → fallback Gemini VLM)
            ├── /search     → IR Service (DuckDuckGo + RSS tin tức + TF-IDF)
            ├── /sonify     → Sonification Service
            └── /moments    → Moment Service (SentenceTransformer + cosine) — Persistent Visual Memory
```

## Data Flow

### Scan tài liệu
1. User chụp ảnh → Flutter CameraService
2. ScannerScreen gọi API backend tương ứng
3. Backend xử lý (AI) → trả kết quả
4. TTS đọc kết quả cho user

### Hỏi đáp kiến thức (Voice QA)
1. User ghi âm câu hỏi → AudioService
2. Gửi audio → /stt → text
3. Gửi text → /rag/query → câu trả lời
4. TTS đọc câu trả lời + nguồn tham khảo

### Nhận dạng tiền VNĐ (Money)
1. User chụp ảnh tờ tiền → ScannerScreen (ScanMode.money)
2. POST /money (multipart ảnh) → MoneyService
3. Ưu tiên YOLO nếu có `vnd_yolo_model_path`, ngược lại dùng Gemini VLM
4. Trả về mệnh giá + độ tin cậy → TTS đọc "Tờ tiền 500.000 đồng..."

### Tìm kiếm thông tin (Search / IR)
1. User ghi âm từ khóa → AudioService → POST /stt → text
2. POST /search → IR Service: gộp DuckDuckGo + RSS tin tức (xếp hạng TF-IDF)
3. Kết quả (web/news) hiển thị + TTS đọc top 3 kết quả
4. RSS được cache đĩa với TTL `NEWS_REFRESH_HOURS` (mặc định 6 giờ)

### Bộ nhớ khoảnh khắc học tập (Persistent Visual Memory)
1. User quét tài liệu hoặc hỏi đáp → nhấn "Lưu" (ScannerScreen / VoiceQAScreen)
2. POST /moments (X-Device-Id) → MomentService tạo embedding (SentenceTransformer) + lưu LearningMoment
3. ReviewScreen nạp danh sách qua GET /moments (merge với storage local, dedupe theo id)
4. Tìm lại bằng POST /moments/search → cosine distance theo thiết bị
5. Xóa qua DELETE /moments/{id} (cũng xóa local)

## Database Schema (PostgreSQL + pgvector)

- users → device-based auth + TTS preferences
- textbook_contents → SGK chunks + embeddings
- learning_sessions → session tracking
- learning_moments → persistent visual memory (embedding lưu JSON text; grade/subject từ migration 0002)
- voice_notes → recording metadata
- feedbacks → user ratings

## Security

- API Key authentication (X-API-Key header)
- Rate limiting per endpoint (slowapi)
- File validation (MIME type + size)
- Metadata filter sanitization (RAG)

## Accessibility

- Voice-first: mọi tương tác qua touch + audio
- High contrast, large fonts (18-36pt)
- Semantics labels trên mọi widget
- Haptic feedback trên mọi hành động

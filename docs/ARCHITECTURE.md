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
            └── /sonify     → Sonification Service
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

## Database Schema (PostgreSQL + pgvector)

- users → device-based auth + TTS preferences
- textbook_contents → SGK chunks + embeddings
- learning_sessions → session tracking
- learning_moments → persistent visual memory
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

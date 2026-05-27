# SgBe Vision — Trợ lý học tập AI đa phương thức cho học sinh khiếm thị

**SgBe Vision** là ứng dụng di động giúp học sinh khiếm thị Việt Nam học tập độc lập thông qua AI: quét sách, mô tả hình ảnh, đọc văn bản thành giọng nói, nhận dạng giọng nói, và truy hồi kiến thức. Thiết kế **voice-first**, **accessibility-first**, hoạt động được offline.

---

## 📋 Mục lục

- [🎯 Đối tượng & Triết lý](#-đối-tượng--triết-lý-thiết-kế)
- [📁 Cấu trúc dự án](#-cấu-trúc-dự-án)
- [🏗️ Kiến trúc hệ thống](#️-kiến-trúc-hệ-thống)
- [🖥️ Frontend (Flutter)](#️-frontend-flutter)
- [⚙️ Backend (FastAPI)](#️-backend-fastapi)
- [📡 API Reference](#-api-reference)
- [🐳 Docker Setup](#-docker-setup)
- [🚀 Hướng dẫn chạy](#-hướng-dẫn-chạy)
- [🧪 Testing](#-testing)
- [📦 Key Dependencies](#-key-dependencies)
- [🗺️ Lộ trình phát triển](#️-lộ-trình-phát-triển)
- [🧠 Notes for AI Agents](#-notes-for-ai-agents)

---

## 🎯 Đối tượng & Triết lý thiết kế

**Người dùng chính:** Học sinh khiếm thị Việt Nam.

**Nguyên tắc cốt lõi:**

1. **Non-visual interaction** — Mọi tính năng đều dùng được qua touch + audio. Không cần phản hồi thị giác.
2. **Massive touch targets** — Mọi nút ≥80px (120px cho primary actions). Không icon nhỏ.
3. **Semantics everywhere** — Mọi widget có `Semantics` label. TalkBack/VoiceOver mô tả được toàn bộ UI.
4. **Haptic feedback** — Mọi tap đều có `HapticFeedback.mediumImpact()` hoặc `.heavyImpact()`.
5. **High contrast** — Nền đen/trắng, viền đậm. Không gradient, shadow, hay decorative elements.
6. **Large text** — Body text tối thiểu 18pt, button 24pt. Text scaler clamp 1.2×–2.0×.
7. **Graceful degradation** — `Backend AI → Backend OCR → On-device ML Kit`. Hoạt động fully offline.
8. **Vietnamese first** — Toàn bộ UI và AI services đều ưu tiên tiếng Việt.

---

## 📁 Cấu trúc dự án

```
ai-for-blinds/
├── README.md                             # Bạn đang ở đây
├── .gitignore
│
├── backend/                              # FastAPI — AI Gateway & Services
│   ├── main.py                           # Entry point, route registration
│   ├── config.py                         # Environment variables, settings
│   ├── database.py                       # SQLAlchemy engine + session factory
│   ├── requirements.txt                  # Python dependencies
│   ├── alembic.ini                       # Database migration config
│   ├── models/                           # SQLAlchemy database models
│   │   ├── __init__.py                   #   Base declarative class
│   │   ├── user.py                       #   Student profile + preferences
│   │   ├── learning_session.py           #   Study session tracking
│   │   ├── learning_moment.py            #   Persistent Visual Memory
│   │   ├── voice_note.py                 #   Voice recording metadata
│   │   ├── textbook_content.py           #   SGK chunks for RAG
│   │   └── feedback.py                   #   User ratings
│   ├── services/                         # AI service implementations
│   │   ├── __init__.py
│   │   ├── ocr_service.py               #   PaddleOCRv5 (Vietnamese)
│   │   ├── vlm_service.py               #   Gemini 2.5 Flash (image description)
│   │   ├── tts_service.py               #   Edge TTS + SSML emotion
│   │   ├── stt_service.py               #   Whisper / phoWhisper
│   │   ├── rag_service.py               #   ChromaDB + embeddings
│   │   ├── object_detection.py          #   YOLOv8 + Vietnamese labels
│   │   └── sonification.py              #   Tone.js subprocess
│   ├── routes/                           # API route handlers
│   │   ├── __init__.py
│   │   ├── describe.py                  #   POST /describe
│   │   ├── ocr.py                       #   POST /ocr
│   │   ├── tts.py                       #   POST /tts
│   │   ├── stt.py                       #   POST /stt
│   │   ├── rag.py                       #   POST /rag/search, /rag/add, GET /rag/stats
│   │   └── sonify.py                    #   POST /sonify
│   ├── utils/                            # Shared utilities
│   │   ├── __init__.py
│   │   ├── file_handler.py              #   File validation + temp management
│   │   └── response_builder.py          #   Standardized JSON responses
│   └── migrations/                       # Alembic migrations
│       ├── env.py                        #   Migration environment
│       ├── script.py.mako               #   Migration template
│       └── 0001_initial_schema.py       #   Initial schema (6 tables + pgvector)
│
├── frontend/                             # Flutter mobile app
│   ├── pubspec.yaml                      # Flutter dependencies
│   ├── lib/
│   │   ├── main.dart                    # Entry point, portrait lock
│   │   ├── app.dart                     # Root widget (MultiProvider, routes, theme)
│   │   ├── theme/
│   │   │   └── app_theme.dart           # Light & dark high-contrast themes
│   │   ├── models/
│   │   │   ├── voice_note.dart          # VoiceNote data model
│   │   │   └── library_item.dart        # Unified library item model
│   │   ├── services/
│   │   │   ├── tts_service.dart         # Text-to-speech (flutter_tts)
│   │   │   ├── ocr_service.dart         # On-device OCR (Google ML Kit)
│   │   │   ├── api_service.dart         # HTTP client for FastAPI
│   │   │   └── library_service.dart     # Local library persistence
│   │   ├── widgets/
│   │   │   └── big_button.dart          # BigButton, BigCircleButton, BigMediaButton
│   │   └── screens/
│   │       ├── splash_screen.dart       # TTS announcement → auto-navigate
│   │       ├── home_screen.dart         # 5 feature buttons (My Library added)
│   │       ├── book_scanner_screen.dart # Multi-page scan + camera guidance
│   │       ├── library_screen.dart      # Search/filter saved items
│   │       ├── text_reader_screen.dart  # Type/paste → TTS reading
│   │       ├── voice_notes_screen.dart  # Record/play/delete voice memos
│   │       └── settings_screen.dart     # Speed, pitch, volume controls
│   ├── assets/                          # Static assets
│   │   ├── images/
│   │   ├── fonts/
│   │   └── audio/
│   └── test/
│       └── widget_test.dart             # Smoke test
│
├── docker/                               # Docker configurations
│   ├── docker-compose.yml               # PostgreSQL + pgvector + Backend service
│   └── Dockerfile.backend               # Backend container image
│
├── models/                               # Pre-trained model files
│   ├── paddleocr/                        # PaddleOCRv5 models
│   ├── whisper/                          # Whisper models
│   └── yolo/                             # YOLOv8 models
│
├── data/                                 # Data files
│   ├── sgk/                              # Textbook PDFs, images
│   ├── embeddings/                       # Pre-computed vector embeddings
│   └── audio_samples/                    # TTS/STT audio samples
│
├── docs/                                 # Documentation
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   └── CONTRIBUTING.md
│
├── notebooks/                            # Jupyter notebooks
│   ├── data_preprocessing.ipynb
│   ├── model_finetuning.ipynb
│   └── evaluation.ipynb
│
└── .github/                              # GitHub Actions
    └── workflows/
        └── ci.yml
```

---

## 🏗️ Kiến trúc hệ thống

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                    SgBe Vision System                         │
                    └─────────────────────────────────────────────────────────────┘
                                          │
     ┌────────────────────────────────────┼────────────────────────────────────┐
     │                                    │                                    │
     ▼                                    ▼                                    ▼
┌──────────────────┐           ┌──────────────────────┐           ┌──────────────────┐
│   Mobile App     │ ←──HTTP── │   FastAPI Gateway    │ ←─────── │    Database      │
│   (Flutter)      │    :8000  │   (backend/main.py)  │           │    Layer         │
│                  │           │                      │           │                  │
│  Voice-first     │  /describe│  Route → Service     │           │  PostgreSQL 16   │
│  Accessibility   │  /ocr     │  architecture:       │           │  + pgvector      │
│  Offline mode    │  /tts     │                      │           │                  │
│                  │  /stt     │  routes/              │           │  6 tables:       │
│                  │  /rag     │    describe.py        │           │  users           │
│                  │  /sonify  │    ocr.py             │           │  learning_       │
│                  │           │    tts.py             │           │  sessions        │
│                  │           │    stt.py             │           │  learning_       │
│                  │           │    rag.py             │           │  moments         │
│                  │           │    sonify.py          │           │  voice_notes     │
│                  │           │                      │           │  textbook_       │
│                  │           │  services/            │           │  contents        │
│                  │           │    vlm_service.py     │           │  feedbacks       │
│                  │           │    ocr_service.py     │           │                  │
│                  │           │    tts_service.py     │           │  ChromaDB        │
│                  │           │    stt_service.py     │           │  (vector search) │
│                  │           │    rag_service.py     │           │                  │
│                  │           │    object_detection.py│           └──────────────────┘
│                  │           │    sonification.py    │
└──────────────────┘           └──────────────────────┘
         │                              │
         │                              │
    ┌────┴────┐                   ┌─────┴──────┐
    │ On-device│                  │   AI APIs   │
    │  ML Kit  │                  │             │
    │  OCR     │                  │ Gemini 2.5  │
    │          │                  │ Flash       │
    │ Platform │                  │ Edge TTS    │
    │  TTS     │                  │ (Microsoft) │
    └─────────┘                   │ PhoWhisper  │
                                  │ YOLOv8      │
                                  │ Tone.js     │
                                  └─────────────┘
```

### Luồng dữ liệu — Book Scanner (Critical Path)

```
User taps "Scan book page"
  → HapticFeedback.mediumImpact()
  → ImagePicker.pickImage(source: camera)
  → Try 1: POST /describe (Gemini VLM — Vietnamese description, 60s timeout)
      → backend/routes/describe.py
        → backend/services/vlm_service.py
  → Fallback: POST /ocr (PaddleOCR — text extraction, 30s timeout)
      → backend/routes/ocr.py
        → backend/services/ocr_service.py
  → Fallback: On-device Google ML Kit OCR (offline, instant)
  → Auto-speak via TTS
  → Optional: POST /rag/search (ask questions about scanned content)
      → backend/routes/rag.py
        → backend/services/rag_service.py
```

Frontend **hoạt động fully offline** (local ML Kit OCR + platform TTS). Backend cung cấp trải nghiệm giàu hơn (Gemini + PaddleOCR + Edge TTS) nhưng là tùy chọn.

---

## 🖥️ Frontend (Flutter)

### Entry Point

**`frontend/lib/main.dart`** — `WidgetsFlutterBinding.ensureInitialized()`, lock portrait, launch `BlindScholarApp`.

### App Root

**`frontend/lib/app.dart`** — `BlindScholarApp`:
- `MultiProvider` với `TtsService` + `LibraryService`
- `MaterialApp` với high-contrast light/dark themes
- `accessibleNavigation: true`, `boldText: true`, `highContrast: true`
- Text scale clamp 1.2×–2.0×

| Route | Screen | Description |
|-------|--------|-------------|
| `/` | `SplashScreen` | TTS "BlindScholar" → auto-nav to `/home` |
| `/home` | `HomeScreen` | 5 feature buttons (My Library + Book Scanner + Text Reader + Voice Notes + Settings) |
| `/library` | `LibraryScreen` | Search & filter saved scans, voice notes, text entries |
| `/book-scanner` | `BookScannerScreen` | Multi-page scan + camera guidance + save to library |
| `/text-reader` | `TextReaderScreen` | Type/paste text → TTS (accepts route arguments) |
| `/voice-notes` | `VoiceNotesScreen` | Record/play/delete with metadata persistence + library sync |
| `/settings` | `SettingsScreen` | TTS speed, pitch, volume + about |

### Theme

**`frontend/lib/theme/app_theme.dart`** — `AppTheme`:
- `lightHighContrast`: Nền trắng, chữ đen, contrast level tối đa.
- `darkHighContrast`: Nền đen, chữ trắng, contrast level tối đa.
- 72px app bar, 64px+ buttons, 8px slider tracks.

### Services

| Service | File | Chức năng |
|---------|------|-----------|
| `TtsService` | `services/tts_service.dart` | `FlutterTts` wrapper (`ChangeNotifier`). Speed/pitch/volume, `speak()`, `pause()`, `resume()` (native platform resume), `stop()`. |
| `OcrService` | `services/ocr_service.dart` | Google ML Kit `TextRecognizer`. `extractTextFromImage(File)` → offline OCR. |
| `ApiService` | `services/api_service.dart` | HTTP client cho FastAPI: `describeImage()`, `ocrImage()`, `isBackendAvailable()`. |
| `LibraryService` | `services/library_service.dart` | JSON file persistence cho `LibraryItem`. `load()`, `addItem()`, `removeItem()`, `search()`. |

### Widgets

| Widget | Kích thước | Dùng cho |
|--------|-----------|----------|
| `BigButton` | Min 80px, full width | Feature buttons |
| `BigCircleButton` | 120×120px circle | Primary actions (scan, record) |
| `BigMediaButton` | Min 100×72px | Media controls (play, pause, stop) |

Tất cả đều có: `Semantics` label, `HapticFeedback`, solid colors, không animation/gradient/shadow.

### Models

| Model | File | Fields |
|-------|------|--------|
| `VoiceNote` | `models/voice_note.dart` | `id`, `filePath`, `title`, `createdAt`, `duration`. `toJson()/fromJson()`, `formattedDuration()` (MM:SS), `formattedDate()` (relative time). |
| `LibraryItem` | `models/library_item.dart` | `id`, `type` (scan/voice_note/text), `title`, `content`, `filePath`, `createdAt`. `matchesQuery()` for search. |

---

## ⚙️ Backend (FastAPI)

### Kiến trúc Modular

Backend được tổ chức theo mô hình **Route → Service → Model**:

```
main.py (entry point)
  └── include_router(routes/*.py)
        └── gọi services/*.py (singleton, lazy init)
              └── gọi models/*.py (SQLAlchemy ORM)
                    └── database.py (PostgreSQL + pgvector)
```

Mọi service đều dùng **singleton pattern** với lazy initialization — khởi tạo lần đầu khi được gọi, tiết kiệm tài nguyên.

### Services

| Service | File | AI Engine | Chức năng |
|---------|------|-----------|-----------|
| **VLM** | `services/vlm_service.py` | Gemini 2.5 Flash | Mô tả ảnh bằng tiếng Việt. `describe()` + `describe_with_context()`. |
| **OCR** | `services/ocr_service.py` | PaddleOCRv5 | Trích xuất văn bản tiếng Việt từ ảnh. Lazy init singleton. |
| **TTS** | `services/tts_service.py` | Edge TTS (Microsoft) | Tổng hợp giọng nói. Hỗ trợ SSML emotion: `synthesize_with_emotion(text, emotion)`. |
| **STT** | `services/stt_service.py` | Whisper / phoWhisper | Nhận dạng giọng nói tiếng Việt. Ưu tiên phoWhisper, fallback base model. |
| **RAG** | `services/rag_service.py` | ChromaDB + sentence embeddings | Tra cứu SGK. `search()`, `add_textbook_chunk()`, `count_chunks()`. |
| **Object Detection** | `services/object_detection.py` | YOLOv8 | Nhận diện vật thể. Vietnamese labels + `describe_detections()`. |
| **Sonification** | `services/sonification.py` | Tone.js (subprocess) | Chuyển dữ liệu thành âm thanh. `sonify_data()` với 3 modes. |

### Database Models

| Model | Table | Vector Support | Key Fields |
|-------|-------|---------------|------------|
| `User` | `users` | — | `device_id`, `tts_speed`, `tts_pitch`, `tts_volume`, `prefers_dark_mode` |
| `LearningSession` | `learning_sessions` | — | `session_type`, `duration_seconds`, `items_processed`, `summary` |
| `LearningMoment` | `learning_moments` | ✅ pgvector | `content`, `content_type`, `file_path`, `embedding`, `textbook_id`, `page_number` |
| `VoiceNote` | `voice_notes` | — | `title`, `file_path`, `duration_seconds`, `transcription`, `is_transcribed` |
| `TextbookContent` | `textbook_contents` | ✅ pgvector | `grade`, `subject`, `chapter`, `page_number`, `content_hash`, `embedding` |
| `Feedback` | `feedbacks` | — | `rating`, `helpful`, `comment`, `feedback_type` |

### Configuration

Tất cả settings tập trung tại **`backend/config.py`** (dataclass `Settings`):

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | **required** | API key cho Gemini |
| `DATABASE_URL` | `postgresql+psycopg2://...` | PostgreSQL + pgvector |
| `DEBUG` | `false` | Debug mode (reload on change) |
| `HOST` / `PORT` | `0.0.0.0:8000` | Server bind |
| `TTS_VOICE` | `vi-VN-HoaiMyNeural` | Edge TTS voice |
| `WHISPER_MODEL` | `base` | Whisper model size |
| `CHROMA_PERSIST_DIR` | `./data/embeddings` | ChromaDB persistence |
| `YOLO_MODEL_PATH` | `./models/yolo/yolov8n.pt` | YOLO weights |
| `MAX_FILE_SIZE` | `10MB` | Upload limit |

---

## 📡 API Reference

### `GET /` — Health Check

```json
{ "status": "ok", "service": "SgBe Vision API", "version": "1.0.0" }
```

### `POST /describe` — Image Description (VLM)

| Param | Type | Description |
|-------|------|-------------|
| `file` | Multipart | JPEG/PNG/WebP/BMP, max 10MB |

**Response:** `{ "success": true, "data": { "description": "..." } }`

### `POST /ocr` — Optical Character Recognition

| Param | Type | Description |
|-------|------|-------------|
| `file` | Multipart | JPEG/PNG/WebP/BMP, max 10MB |

**Response:** `{ "success": true, "data": { "text": "..." } }`

### `POST /tts` — Text-to-Speech

| Param | Type | Description |
|-------|------|-------------|
| `text` | Query | Văn bản cần đọc |
| `emotion` | Query | `neutral` (default), `happy`, `sad`, `angry`, `excited` |

**Response:** MP3 file download (`audio/mpeg`)

### `POST /stt` — Speech-to-Text

| Param | Type | Description |
|-------|------|-------------|
| `file` | Multipart | Audio file (MP3/WAV/M4A/OGG) |
| `language` | Form | Mặc định `vi` |

**Response:** `{ "success": true, "data": { "text": "...", "segments": [...], "language": "vi" } }`

### `POST /rag/search` — Textbook Q&A

```json
{
  "question": "Nguyên lý hoạt động của máy biến áp?",
  "n_results": 5,
  "grade": 12,
  "subject": "Vật lý"
}
```

**Response:** `{ "success": true, "data": { "results": [...], "total": 5, "collection_size": 150 } }`

### `POST /rag/add` — Index Textbook Content

```json
{
  "chunk_id": "grade10_math_ch3_p42",
  "text": "Nội dung sách giáo khoa...",
  "grade": 10,
  "subject": "Toán",
  "chapter": "Chương 3",
  "page_number": 42
}
```

### `GET /rag/stats` — Collection Stats

**Response:** `{ "success": true, "data": { "collection": "sgbe_textbook", "total_chunks": 150, "available": true } }`

### `POST /sonify` — Data Sonification

```json
{
  "data": [
    { "label": "2024-Q1", "value": 45 },
    { "label": "2024-Q2", "value": 62 }
  ],
  "type": "timeseries",
  "title": "Tăng trưởng GDP"
}
```

| `type` | Mô tả | Phương pháp |
|--------|-------|-------------|
| `timeseries` | Dữ liệu chuỗi thời gian | Frequency mapping (C4–C6) |
| `categories` | Dữ liệu phân loại | Scale ascending |
| `simple` | Dãy số đơn giản | Melody mapping |

---

## 🐳 Docker Setup

**`docker/docker-compose.yml`** gồm 2 services:

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `postgres` | `pgvector/pgvector:pg16` | 5432 | PostgreSQL + vector extension |
| `backend` | Custom build | 8000 | FastAPI backend |

```bash
# Start all services
cd docker
export GOOGLE_API_KEY='your-gemini-api-key'
docker compose up -d

# Verify
docker compose ps
curl http://localhost:8000/
```

---

## 🚀 Hướng dẫn chạy

### Frontend Only (on-device OCR + TTS, không cần backend)

```bash
cd frontend
flutter run
```

### Backend (Development)

```bash
cd backend

# 1. Cài dependencies
pip install -r requirements.txt

# 2. Set API key
export GOOGLE_API_KEY='your-gemini-api-key'

# 3. (Optional) Start PostgreSQL + pgvector
cd ../docker && docker compose up -d postgres && cd ../backend

# 4. Chạy server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Backend (Docker)

```bash
cd docker
export GOOGLE_API_KEY='your-gemini-api-key'
docker compose up -d
```

### Full Stack

```bash
# Terminal 1: Backend
cd backend
export GOOGLE_API_KEY='your-gemini-api-key'
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
flutter run
```

### Database Migrations

```bash
cd backend

# Tạo migration mới
alembic revision --autogenerate -m "description"

# Chạy migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Frontend tests
cd frontend && flutter test

# Backend (syntax check)
cd backend && python -m py_compile main.py
```

---

## 🧪 Testing

**Frontend:** `frontend/test/widget_test.dart` — Smoke test: HomeScreen renders with title + 5 feature buttons.

**Backend:** Mỗi Python file được validate qua `py_compile`. Alembic migrations có thể test với database local.

---

## 📦 Key Dependencies

### Flutter (`frontend/pubspec.yaml`)

| Package | Version | Purpose |
|---------|---------|---------|
| `flutter_tts` | ^4.2.2 | Cross-platform TTS |
| `speech_to_text` | ^7.0.0 | Speech recognition |
| `record` | ^5.2.0 | Audio recording |
| `audioplayers` | ^6.1.0 | Audio playback |
| `provider` | ^6.1.2 | State management |
| `path_provider` | ^2.1.5 | App directory paths |
| `intl` | ^0.20.2 | Date formatting |
| `image_picker` | ^1.1.2 | Camera/gallery access |
| `google_mlkit_text_recognition` | ^0.14.0 | On-device OCR |
| `http` | ^1.2.0 | Backend API communication |

### Python (`backend/requirements.txt`)

| Package | Version | Layer | Purpose |
|---------|---------|-------|---------|
| `fastapi` | 0.136.1 | Gateway | Web framework |
| `uvicorn[standard]` | 0.47.0 | Gateway | ASGI server |
| `sqlalchemy` | 2.0.36 | Database | ORM |
| `psycopg2-binary` | 2.9.10 | Database | PostgreSQL driver |
| `alembic` | 1.14.1 | Database | Migrations |
| `google-generativeai` | 0.8.6 | AI — VLM | Gemini 2.5 Flash |
| `paddleocr` | 2.9.1 | AI — OCR | Vietnamese OCR |
| `edge-tts` | 7.2.8 | AI — TTS | Vietnamese speech |
| `faster-whisper` | 1.2.1 | AI — STT | Speech recognition |
| `chromadb` | 0.5.0 | AI — RAG | Vector database |
| `sentence-transformers` | ≥3.0.0 | AI — RAG | Text embeddings |
| `ultralytics` | 8.3.0 | AI — Detection | YOLOv8 |
| `opencv-python-headless` | 4.13.0 | AI — OCR | Image processing |
| `torch` | 2.5.0 | AI — All | PyTorch backend |

---

## 🗺️ Lộ trình phát triển

### MVP (Giai đoạn 1) ✅ Hoàn thành

| Tính năng | Trạng thái | Backend Service | Frontend |
|-----------|-----------|-----------------|----------|
| Smart OCR | ✅ | `services/ocr_service.py` (PaddleOCR) | `BookScannerScreen` + fallback ML Kit |
| Text-to-Speech | ✅ | `services/tts_service.py` (Edge TTS) | `TtsService` + `TextReaderScreen` |
| Scene Description | ✅ | `services/vlm_service.py` (Gemini) | `BookScannerScreen` (try 1) |
| Voice Recording | ✅ | Database model `VoiceNote` | `VoiceNotesScreen` |
| My Library | ✅ | — (Local JSON storage) | `LibraryScreen` + `LibraryService` |
| Speech-to-Text | 🆕 | `services/stt_service.py` (PhoWhisper) | Cần tích hợp frontend |
| RAG Textbook Q&A | 🆕 | `services/rag_service.py` (ChromaDB) | Cần màn hình Q&A |

### Advanced (Giai đoạn 2) 🆕 Đã có backend, cần frontend

| Tính năng | Backend | Frontend |
|-----------|---------|----------|
| Persistent Visual Memory | `models/learning_moment.py` + pgvector | Cần xây dựng |
| Sonification | `services/sonification.py` (Tone.js) | Cần màn hình nghe dữ liệu |
| Emotion-aware Literature | `services/tts_service.py` (SSML) | Cần UI chọn cảm xúc |
| Object Detection | `services/object_detection.py` (YOLOv8) | Cần màn hình phát hiện vật thể |

### Research (Giai đoạn 3) 🔮 Tương lai

- Offline Multimodal Assistant (chạy AI trên thiết bị)
- Personalized Learning Memory (cá nhân hóa theo lịch sử học tập)
- Adaptive Accessibility Intelligence (tự động điều chỉnh UI)
- STEM Accessibility Mode (hỗ trợ thực hành thí nghiệm, cảnh báo an toàn)

---

## ♿ Accessibility Patterns

| Pattern | Implementation |
|---------|---------------|
| **Semantics labels** | Every interactive widget wrapped in `Semantics(button: true, label: ...)` |
| **Touch target size** | Min 80×infinity px (`BoxConstraints(minHeight: 80)`) |
| **Primary actions** | 120×120px circle buttons (`BigCircleButton`) |
| **Haptic feedback** | `HapticFeedback.mediumImpact()` on navigation, `heavyImpact()` on completion |
| **High contrast** | Pure black/white backgrounds, 2-3px borders, no gradients/shadows |
| **Large text** | 24px button text, 20px body, clamped between 1.2×–2.0× |
| **No decorations** | No animations, no curved corners, no decorative icons |
| **Back navigation** | Always stops TTS before popping |
| **Error feedback** | SnackBars with short, clear messages in Vietnamese |
| **Loading states** | Spinner + "Reading..." text with Semantics label |

---

## 🧠 Notes for AI Agents

1. **All UI code assumes a blind user.** Never add visual-only elements. Never reduce touch target sizes. Always add `Semantics` labels.
2. **The fallback chain matters.** `ApiService` (Gemini) → `ApiService` (PaddleOCR) → `OcrService` (ML Kit) → fail. Don't break this order.
3. **`TtsService` is a singleton via `Provider`.** Access via `context.read<TtsService>()` or `Consumer<TtsService>`.
4. **Dispose native resources.** `OcrService.dispose()`, `AudioRecorder.dispose()`, `AudioPlayer.dispose()` must be called.
5. **Check `mounted`** after every async gap before calling `setState()`.
6. **Routes are in `app.dart`.** Add new screens there with a clear route name.
7. **Use `BigButton`/`BigCircleButton`/`BigMediaButton`.** Don't use Material buttons directly.
8. **Backend services use singleton + lazy init.** Import the singleton instance, not the class.
9. **All backend endpoints return standardized JSON.** `{ "success": bool, "message": string, "data": ... }` via `response_builder.py`.
10. **Vietnamese is the primary language.** All API responses, comments, and prompts are in Vietnamese.

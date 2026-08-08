# SgBe Vision — Trợ lý học tập AI đa phương thức cho học sinh khiếm thị

**SgBe Vision** là ứng dụng di động giúp học sinh khiếm thị Việt Nam học tập độc lập thông qua AI: quét sách, mô tả hình ảnh, đọc văn bản thành giọng nói, nhận dạng giọng nói, và truy hồi kiến thức. Thiết kế **voice-first**, **accessibility-first**, hoạt động được offline.

Dự án bao gồm 2 server backend:
- **`backend/`** — FastAPI AI Gateway với nhiều service (OCR, TTS, STT, VLM, RAG, Object Detection)
- **`app/`** — VLM Server nhẹ, tích hợp Gemini Vision + Edge TTS, phục vụ mobile app (ảnh + giọng nói → câu trả lời)

---

## 📋 Mục lục

- [🎯 Đối tượng & Triết lý](#-đối-tượng--triết-lý-thiết-kế)
- [📁 Cấu trúc dự án](#-cấu-trúc-dự-án)
- [🏗️ Kiến trúc hệ thống](#️-kiến-trúc-hệ-thống)
- [🖥️ Frontend (Flutter)](#️-frontend-flutter)
- [⚙️ Backend (FastAPI - backend/)](#️-backend-fastapi---backend)
- [🖥️ VLM Server (app/)](#️-vlm-server-app)
- [📡 API Reference](#-api-reference)
- [🐳 Docker Setup](#-docker-setup)
- [🚀 Hướng dẫn chạy](#-hướng-dẫn-chạy)
- [🧪 Testing](#-testing)
- [📦 Key Dependencies](#-key-dependencies)
- [🗺️ Lộ trình phát triển](#️-lộ-trình-phát-triển)
- [♿ Accessibility Patterns](#-accessibility-patterns)
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
├── .env.example                          # Mẫu cấu hình môi trường cho VLM Server
├── requirements.txt                      # Python dependencies cho VLM Server
│
├── app/                                  # VLM Server (FastAPI nhẹ)
│   ├── __init__.py
│   ├── main.py                           # FastAPI app: /api/ask, /api/ask-voice, /api/tts
│   ├── config.py                         # Pydantic settings từ .env
│   ├── vlm.py                            # Gemini Vision integration (VLM)
│   └── tts.py                            # Edge TTS (Text-to-Speech)
│
├── static/                               # Static files (web demo)
│   └── index.html                        # Demo camera + voice cho VLM Server
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
│   │   ├── money_service.py             #   VND banknote recognition (YOLO→VLM)
│   │   ├── ir_service.py                #   Internet retrieval (DDG + RSS + TF-IDF)
│   │   ├── moment_service.py            #   Persistent Visual Memory (CRUD + semantic search)
│   │   └── sonification.py              #   Tone.js subprocess
│   ├── routes/                           # API route handlers
│   │   ├── __init__.py
│   │   ├── describe.py                  #   POST /describe
│   │   ├── ocr.py                       #   POST /ocr
│   │   ├── tts.py                       #   POST /tts
│   │   ├── stt.py                       #   POST /stt
│   │   ├── rag.py                       #   POST /rag/search, /rag/add, GET /rag/stats
│   │   ├── detect.py                    #   POST /detect
│   │   ├── money.py                     #   POST /money
│   │   ├── search.py                    #   POST /search
│   │   ├── moments.py                   #   POST/GET/DELETE /moments, POST /moments/search
│   │   └── sonify.py                    #   POST /sonify
│   ├── utils/                            # Shared utilities
│   │   ├── __init__.py
│   │   ├── file_handler.py              #   File validation + temp management
│   │   └── response_builder.py          #   Standardized JSON responses
│   └── migrations/                       # Alembic migrations
│       ├── env.py                        #   Migration environment
│       ├── script.py.mako               #   Migration template
│       ├── 0001_initial_schema.py       #   Initial schema (6 tables + pgvector)
│       └── 0002_add_moment_grade_subject.py  #   grade + subject cho learning_moments
│
├── frontend/                             # Flutter mobile app
│   ├── pubspec.yaml                      # Flutter dependencies
│   ├── lib/
│   │   ├── main.dart                    # Entry point, portrait lock
│   │   ├── app.dart                     # Root widget (MultiProvider, routes, theme)
│   │   ├── theme/
│   │   │   └── app_theme.dart           # Light & dark high-contrast themes
│   │   ├── models/
│   │   │   ├── learning_moment.dart     # LearningMoment model (local + API)
│   │   │   ├── scan_mode.dart           # ScanMode enum (OCR/Describe/Chart/Detect/Money)
│   │   │   ├── voice_note.dart          # VoiceNote data model
│   │   │   └── library_item.dart        # Unified library item model
│   │   ├── services/
│   │   │   ├── tts_service.dart         # Text-to-speech (flutter_tts)
│   │   │   ├── ocr_service.dart         # On-device OCR (Google ML Kit)
│   │   │   ├── api_service.dart         # HTTP client for FastAPI (+ /moments)
│   │   │   ├── settings_service.dart    # Persisted settings + deviceId
│   │   │   └── library_service.dart     # Local library persistence
│   │   ├── widgets/
│   │   │   ├── neon_button.dart         # NeonButton, NeonCircleButton, NeonIconButton
│   │   │   └── ...                      # glow_chip, waveform_bar, glass_bottom_sheet…
│   │   └── screens/
│   │       ├── splash_screen.dart       # TTS announcement → auto-navigate
│   │       ├── home_screen.dart         # 5 feature buttons (My Library added)
│   │       ├── scanner_screen.dart      # Quét tài liệu (5 modes) + lưu khoảnh khắc
│   │       ├── voice_qa_screen.dart     # Hỏi đáp SGK + lưu khoảnh khắc
│   │       ├── review_screen.dart       # Ôn tập (sync backend /moments)
│   │       ├── search_screen.dart       # Tìm kiếm Internet voice-first
│   │       ├── book_scanner_screen.dart # Multi-page scan + camera guidance
│   │       ├── library_screen.dart      # Search/filter saved items
│   │       ├── text_reader_screen.dart  # Type/paste → TTS reading
│   │       ├── voice_notes_screen.dart  # Record/play/delete voice memos
│   │       └── settings_screen.dart     # Speed, pitch, volume, server, deviceId
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
│  Voice-first     │           │  Or: VLM Server      │           │  PostgreSQL 16   │
│  Accessibility   │           │  (app/main.py) :8000 │           │  + pgvector      │
│  Offline mode    │           │                      │           │                  │
│                  │  /api/ask │  routes/              │           │  6 tables:       │
│                  │  /api/tts │    /api/ask           │           │  users           │
│                  │  /api/ask-│    /api/ask-voice     │           │  learning_       │
│                  │  -voice   │    /api/tts           │           │  sessions        │
│                  │           │    /api/voices        │           │  learning_       │
│                  │           │                      │           │  moments         │
│                  │           │  services/            │           │  voice_notes     │
│                  │           │    vlm.py (Gemini)    │           │  textbook_       │
│                  │           │    tts.py (Edge TTS)  │           │  contents        │
│                  │           │                      │           │  feedbacks       │
│                  │  /describe│  backend/services/    │           │                  │
│                  │  /ocr     │    vlm_service.py     │           │  ChromaDB        │
│                  │  /tts     │    ocr_service.py     │           │  (vector search) │
│                  │  /stt     │    tts_service.py     │           └──────────────────┘
│                  │  /rag     │    stt_service.py     │
│                  │  /money   │    rag_service.py     │
│                  │  /search  │    object_detection.py│
│                  │  /sonify  │    money_service.py   │
│                  │           │    ir_service.py      │
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
- `MultiProvider` với `AudioService` + `VoiceCommandService`
- `MaterialApp` với high-contrast light/dark themes + Neon Pulse theme
- `accessibleNavigation: true`, `boldText: true`, `highContrast: true`
- Text scale clamp 1.2×–2.0×, `GestureNavigator` (swipe + shake-to-voice)

| Route | Screen | Description |
|-------|--------|-------------|
| `/` | `HomeScreen` | Dashboard Neon Pulse + quick actions (Quét, Hỏi đáp, Tìm kiếm) |
| `/scanner` | `ScannerScreen` | Quét tài liệu: OCR / Mô tả ảnh / Đọc biểu đồ / Phát hiện vật thể / Nhận dạng tiền |
| `/voice-qa` | `VoiceQAScreen` | Hỏi đáp SGK bằng giọng nói (STT → RAG → TTS) |
| `/review` | `ReviewScreen` | Ôn tập / xem lại kiến thức |
| `/search` | `SearchScreen` | Tìm kiếm thông tin Internet voice-first (STT → `/search` → TTS) |
| `/settings` | `SettingsScreen` | TTS speed, pitch, volume + server config |

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
| `ApiService` | `services/api_service.dart` | HTTP client cho FastAPI: `describeImage()`, `ocrImage()`, `sttAudio()`, `ragQuery()`, `detectImage()`, `recognizeMoney()`, `searchWeb()`, `createMoment()`, `listMoments()`, `deleteMoment()`, `searchMoments()`, `isBackendAvailable()`. |
| `SettingsService` | `services/settings_service.dart` | Lưu/nạp settings (server, API key, autoListen) + sinh `deviceId` cố định cho thiết bị. |
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

## ⚙️ Backend (FastAPI — `backend/`)

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
| **Money** | `services/money_service.py` | YOLO VND → fallback Gemini VLM | Nhận dạng mệnh giá tiền Việt Nam. `recognize()` với 2 tầng yolo/vlm. |
| **IR / Search** | `services/ir_service.py` | DuckDuckGo + RSS tin tức + TF-IDF | Truy hồi thông tin Internet. `search()` gộp web + news, cache RSS. |
| **Moment** | `services/moment_service.py` | SentenceTransformer + cosine | Persistent Visual Memory. `create()`, `list_for_device()`, `delete()`, `search()` — lưu khoảnh khắc học tập và tìm kiếm ngữ nghĩa theo thiết bị. |
| **Sonification** | `services/sonification.py` | Tone.js (subprocess) | Chuyển dữ liệu thành âm thanh. `sonify_data()` với 3 modes. |

### Database Models

| Model | Table | Vector Support | Key Fields |
|-------|-------|---------------|------------|
| `User` | `users` | — | `device_id`, `tts_speed`, `tts_pitch`, `tts_volume`, `prefers_dark_mode` |
| `LearningSession` | `learning_sessions` | — | `session_type`, `duration_seconds`, `items_processed`, `summary` |
| `LearningMoment` | `learning_moments` | ✅ pgvector | `content`, `content_type`, `file_path`, `embedding`, `textbook_id`, `grade`, `subject`, `page_number`, `chapter` |
| `VoiceNote` | `voice_notes` | — | `title`, `file_path`, `duration_seconds`, `transcription`, `is_transcribed` |
| `TextbookContent` | `textbook_contents` | ✅ pgvector | `grade`, `subject`, `chapter`, `page_number`, `content_hash`, `embedding` |
| `Feedback` | `feedbacks` | — | `rating`, `helpful`, `comment`, `feedback_type` |

### Configuration (backend/)

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
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Model embedding cho moment search |
| `YOLO_MODEL_PATH` | `./models/yolo/yolov8n.pt` | YOLO weights |
| `VND_YOLO_MODEL_PATH` | `./models/yolo/vnd_yolov8n.pt` | YOLO nhận dạng tiền (tùy chọn; nếu thiếu dùng Gemini VLM) |
| `MONEY_CONFIDENCE` | `0.5` | Ngưỡng tin cậy nhận dạng tiền |
| `SEARCH_DEFAULT_N` | `5` | Số kết quả mặc định cho `/search` |
| `NEWS_CACHE_DIR` | `./data/news_cache` | Cache RSS tin tức |
| `NEWS_REFRESH_HOURS` | `6` | Chu kỳ làm mới cache tin tức (giờ) |
| `MAX_FILE_SIZE` | `10MB` | Upload limit |

---

## 🖥️ VLM Server (`app/`)

Server FastAPI nhẹ, tích hợp Gemini Vision để app mobile gửi **ảnh + câu hỏi** → server trả về câu trả lời do VLM phân tích ảnh.

### Tính năng

| Tính năng | Endpoint | Input | Output |
|-----------|----------|-------|--------|
| **Hỏi đáp hình ảnh** | `POST /api/ask` | Ảnh + câu hỏi (text) | Câu trả lời (JSON) |
| **Hỏi đáp bằng giọng nói** | `POST /api/ask-voice` | Ảnh + audio câu hỏi | Audio MP3 câu trả lời + headers |
| **Text-to-Speech** | `POST /api/tts` | Văn bản | Stream MP3 audio |
| **Danh sách giọng đọc** | `GET /api/voices` | — | Danh sách giọng tiếng Việt |
| **Health check** | `GET /health` | — | Trạng thái server |

### Cấu trúc

```
app/
├── __init__.py
├── main.py        # FastAPI app, tất cả endpoints
├── vlm.py         # Gemini VLM integration (ask_vlm, ask_vlm_voice)
├── tts.py         # Edge TTS (stream_tts, list_voices)
└── config.py      # Pydantic settings từ .env
```

### Configuration (app/)

Cấu hình qua file **`.env`** ở thư mục gốc:

```env
# Lấy API key tại https://aistudio.google.com/apikey
GEMINI_API_KEY=your_api_key_here

# Tên model. Nếu "gemini-3.0-pro" chưa available với key của bạn,
# thử: gemini-2.5-pro, gemini-2.5-flash, gemini-2.0-flash
GEMINI_MODEL=gemini-3.0-pro

# Giới hạn upload (MB)
MAX_IMAGE_MB=10
MAX_AUDIO_MB=10

# Timeout gọi Gemini (giây)
REQUEST_TIMEOUT_S=60

# CORS - đặt domain app mobile nếu cần, mặc định "*" cho dev
ALLOWED_ORIGINS=*

# Giọng đọc edge-tts (tiếng Việt)
TTS_VOICE=vi-VN-HoaiMyNeural
TTS_RATE=+0%
TTS_PITCH=+0Hz
```

### Web Demo

Server phục vụ file `static/index.html` tại `http://localhost:8000/` — trang demo có camera + ghi âm giọng nói, hỗ trợ người khiếm thị (voice-first, haptic feedback, beep cues, shake-to-reset).

### Mobile Integration Examples

**Android (Kotlin + OkHttp)**:
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

**iOS (Swift + URLSession)**:
Dùng `URLSession.upload(for:from:)` với multipart body — tương tự pattern trên.

### Production Notes (VLM Server)

- Đặt `ALLOWED_ORIGINS` cụ thể (không để `*`).
- Chạy sau reverse proxy (nginx/Caddy) với HTTPS.
- Đặt rate limit (vd. `slowapi`).
- Cân nhắc lưu lịch sử hỏi đáp vào DB nếu cần.

---

## 📡 API Reference

### `backend/` API

#### `GET /` — Health Check

```json
{ "status": "ok", "service": "SgBe Vision API", "version": "1.0.0" }
```

#### `POST /describe` — Image Description (VLM)

| Param | Type | Description |
|-------|------|-------------|
| `file` | Multipart | JPEG/PNG/WebP/BMP, max 10MB |

**Response:** `{ "success": true, "data": { "description": "..." } }`

#### `POST /ocr` — Optical Character Recognition

| Param | Type | Description |
|-------|------|-------------|
| `file` | Multipart | JPEG/PNG/WebP/BMP, max 10MB |

**Response:** `{ "success": true, "data": { "text": "..." } }`

#### `POST /tts` — Text-to-Speech

| Param | Type | Description |
|-------|------|-------------|
| `text` | Query | Văn bản cần đọc |
| `emotion` | Query | `neutral` (default), `happy`, `sad`, `angry`, `excited` |

**Response:** MP3 file download (`audio/mpeg`)

#### `POST /stt` — Speech-to-Text

| Param | Type | Description |
|-------|------|-------------|
| `file` | Multipart | Audio file (MP3/WAV/M4A/OGG) |
| `language` | Form | Mặc định `vi` |

**Response:** `{ "success": true, "data": { "text": "...", "segments": [...], "language": "vi" } }`

#### `POST /rag/search` — Textbook Q&A

```json
{
  "question": "Nguyên lý hoạt động của máy biến áp?",
  "n_results": 5,
  "grade": 12,
  "subject": "Vật lý"
}
```

**Response:** `{ "success": true, "data": { "results": [...], "total": 5, "collection_size": 150 } }`

#### `POST /rag/add` — Index Textbook Content

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

#### `GET /rag/stats` — Collection Stats

**Response:** `{ "success": true, "data": { "collection": "sgbe_textbook", "total_chunks": 150, "available": true } }`

#### `POST /sonify` — Data Sonification

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

#### `POST /money` — Nhận dạng mệnh giá tiền VNĐ

| Param | Type | Description |
|-------|------|-------------|
| `file` | Multipart | Ảnh tờ tiền Việt Nam, max 10MB |

**Response:** `{ "success": true, "data": { "denomination": "500000", "formatted": "500.000 đồng", "method": "vlm", "confidence": 0.95 } }`

- `method`: `yolo` (nếu `VND_YOLO_MODEL_PATH` hợp lệ) hoặc `vlm` (Gemini). `denomination = null` khi không phải tờ tiền VN. `503` khi không có phương thức khả dụng. Rate limit: 10/phút.

#### `POST /search` — Truy hồi thông tin Internet

```json
{
  "query": "Thủ đô của Việt Nam là gì?",
  "n_results": 5
}
```

**Response:** `{ "success": true, "data": { "query": "...", "results": [{ "title": "...", "snippet": "...", "url": "...", "source": "web|news", "score": 0.98 }] } }`

- `source`: `web` (DuckDuckGo) hoặc `news` (RSS VnExpress/Dân Trí xếp hạng TF-IDF). Rate limit: 20/phút.

#### `/moments` — Persistent Visual Memory

Tất cả endpoints yêu cầu thêm header `X-Device-Id: <device_id>` để phạm vi hóa dữ liệu theo thiết bị. Trả `503` khi database không khả dụng.

| Method | Endpoint | Mô tả | Rate limit |
|--------|----------|-------|------------|
| POST | `/moments` | Lưu khoảnh khắc: `{title, content, content_type, grade, subject, chapter, page_number}` | 30/phút |
| GET | `/moments` | Danh sách khoảnh khắc của thiết bị (mới nhất trước, tối đa 100) | 60/phút |
| DELETE | `/moments/{id}` | Xóa khoảnh khắc (404 nếu không thuộc thiết bị) | 30/phút |
| POST | `/moments/search` | Tìm kiếm ngữ nghĩa: `{query, n_results}` → `{results: [{id, title, content, distance}]}` | 30/phút |

- Backend tự tạo embedding ngữ nghĩa (`all-MiniLM-L6-v2`) khi lưu; `distance` = khoảng cách cosine (càng nhỏ càng liên quan).
- Chi tiết response xem `docs/API.md`.

---

### `app/` VLM Server API

#### `GET /health` — Health Check

```json
{ "status": "ok", "model": "gemini-3.0-pro", "voice": "vi-VN-HoaiMyNeural" }
```

#### `GET /api/voices` — Danh sách giọng đọc tiếng Việt

```json
{
  "voices": [
    { "name": "vi-VN-HoaiMyNeural", "gender": "Female", "locale": "vi-VN" },
    { "name": "vi-VN-NamMinhNeural", "gender": "Male", "locale": "vi-VN" }
  ]
}
```

#### `POST /api/ask` — Hỏi đáp về ảnh (text)

| Param | Type | Description |
|-------|------|-------------|
| `image` | File (Multipart) | JPEG/PNG/WebP/HEIC, max 10MB |
| `question` | Form (string) | Câu hỏi về ảnh |

**Response 200:**
```json
{
  "answer": "Trong ảnh có một con mèo đang ngồi trên ghế sofa...",
  "model": "gemini-3.0-pro",
  "elapsed_ms": 1432
}
```

**Lỗi:**
- `400` ảnh rỗng / câu hỏi rỗng
- `413` ảnh quá lớn
- `429` rate limit (Retry-After header)
- `422` ảnh không hợp lệ / VLM từ chối trả lời

**Test bằng cURL:**
```bash
curl -X POST http://localhost:8000/api/ask \
  -F "image=@cat.jpg" \
  -F "question=Trong ảnh có gì?"
```

#### `POST /api/ask-voice` — Hỏi đáp về ảnh (giọng nói)

| Param | Type | Description |
|-------|------|-------------|
| `image` | File (Multipart) | JPEG/PNG/WebP/HEIC, max 10MB |
| `audio` | File (Multipart) | WebM/OGG/MP3/WAV, max 10MB |

**Response:** Audio MP3 stream với headers `X-Question`, `X-Answer`, `X-Elapsed-Ms`.

Luồng xử lý: Gemini nghe audio (STT) + nhìn ảnh (VLM) → trả lời → Edge TTS → stream MP3 về client.

#### `POST /api/tts` — Text-to-Speech (standalone)

| Param | Type | Description |
|-------|------|-------------|
| `text` | Form (string) | Văn bản cần đọc |
| `voice` | Form (string, optional) | Giọng đọc, mặc định `vi-VN-HoaiMyNeural` |

**Response:** Stream MP3 audio (`audio/mpeg`).

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

### VLM Server (app/) — Development

```bash
# 1. Tạo .env từ template
cp .env.example .env
# Sửa GEMINI_API_KEY trong .env

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Chạy server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Web demo: http://localhost:8000/
- API docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Backend (backend/) — Development

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
# Terminal 1: VLM Server
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Backend AI Gateway
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001

# Terminal 3: Frontend
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

---

## 🧪 Testing

```bash
# Frontend tests
cd frontend && flutter test

# Backend (syntax check)
cd backend && python -m py_compile main.py

# VLM Server (syntax check)
python -m py_compile app/main.py app/vlm.py app/tts.py app/config.py
```

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

### Python — VLM Server (`requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥0.115 | Web framework |
| `uvicorn[standard]` | ≥0.32 | ASGI server |
| `google-generativeai` | ≥0.8.3 | Gemini AI |
| `python-multipart` | ≥0.0.12 | File upload parsing |
| `python-dotenv` | ≥1.0.1 | .env loading |
| `pydantic-settings` | ≥2.6 | Settings management |
| `Pillow` | ≥11.0 | Image validation |
| `edge-tts` | ≥7.0 | Vietnamese TTS |

### Python — Backend AI Gateway (`backend/requirements.txt`)

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
| `ddgs` | ≥8.1 | AI — IR | DuckDuckGo search |
| `feedparser` | ≥6.0 | AI — IR | RSS tin tức |

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
| VLM Server | 🆕 | `app/main.py` (Gemini + Edge TTS) | Web demo + mobile API |
| Speech-to-Text | 🆕 | `services/stt_service.py` (PhoWhisper) | ✅ Voice Q&A + Search |
| RAG Textbook Q&A | 🆕 | `services/rag_service.py` (ChromaDB) | ✅ `VoiceQAScreen` |
| Money Recognition (tiền VNĐ) | ✅ | `services/money_service.py` (YOLO→Gemini VLM) | ✅ `ScanMode.money` trong `ScannerScreen` |
| Internet Retrieval | ✅ | `services/ir_service.py` (DuckDuckGo + RSS + TF-IDF) | ✅ `SearchScreen` voice-first |

### Advanced (Giai đoạn 2) 🆕 Đã có backend, cần frontend

| Tính năng | Backend | Frontend |
|-----------|---------|----------|
| Persistent Visual Memory | ✅ `services/moment_service.py` + `/moments` API + migration 0002 | ✅ Lưu từ Scanner/Q&A + `ReviewScreen` sync backend |
| Sonification | `services/sonification.py` (Tone.js) | Cần màn hình nghe dữ liệu |
| Emotion-aware Literature | `services/tts_service.py` (SSML) | Cần UI chọn cảm xúc |
| Color Recognition | `services/vlm_service.py` (Gemini) | Cần xây dựng |
| Mở rộng Object Detection sang mặt hàng siêu thị | `services/object_detection.py` (YOLOv8) | Cần dữ liệu + tinh chỉnh |

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

# SgBe Vision — Trợ lý học tập cho học sinh khiếm thị

Một ứng dụng di động giúp học sinh khiếm thị học tập độc lập thông qua AI: quét sách, mô tả hình ảnh, đọc văn bản thành giọng nói.

---

## 📂 Cấu trúc dự án

```
ai-for-blinds/
├── frontend/          # Flutter mobile app
│   ├── lib/
│   │   ├── screens/       # Màn hình chính
│   │   ├── services/      # TTS, OCR, API service
│   │   ├── models/        # Data models
│   │   ├── widgets/       # Widget tái sử dụng
│   │   └── theme/         # Giao diện tương phản cao
│   ├── android/
│   ├── ios/
│   └── test/
├── backend/           # FastAPI AI gateway & services
│   ├── main.py            # API endpoints
│   └── requirements.txt   # Python dependencies
├── models/            # Pre-trained / fine-tuned AI models
├── data/              # SGK data, embeddings, vector DB files
├── docker/            # Docker Compose cho PostgreSQL, v.v.
│   └── docker-compose.yml
├── docs/              # Documentation
├── notebooks/         # Jupyter notebooks for model training
├── .gitignore
└── README.md
```

## 🚀 Bắt đầu nhanh

### Yêu cầu

- Flutter SDK 3.44.0+
- Python 3.10+
- Docker & Docker Compose (cho PostgreSQL)

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend sẽ chạy tại `http://localhost:8000`.

### 2. Frontend

```bash
cd frontend
flutter run
```

### 3. Docker (tùy chọn)

```bash
cd docker
docker compose up -d
```

## 🤖 Công nghệ

| Thành phần | Công nghệ |
|-----------|-----------|
| **Frontend** | Flutter |
| **Backend** | FastAPI |
| **OCR** | PaddleOCRv5 (on-device: Google ML Kit) |
| **VLM** | Gemini 2.5 Flash |
| **RAG** | ChromaDB + CLIP embeddings |
| **STT/TTS** | Whisper / Edge TTS |
| **Object Detection** | YOLOv8 |
| **Database** | PostgreSQL |

## 🎯 Tính năng

- **📷 Quét sách** — Chụp ảnh trang sách, AI mô tả nội dung hoặc OCR văn bản và đọc to
- **📖 Đọc văn bản** — Gõ hoặc dán văn bản, đọc to với giọng Việt Nam tự nhiên
- **🎤 Ghi chú thoại** — Ghi và quản lý các ghi chú giọng nói
- **⚙️ Cài đặt** — Điều chỉnh tốc độ, cao độ, âm lượng giọng đọc

Thiết kế với khả năng tiếp cận cao: nút bấm lớn, giao diện tương phản cao, hỗ trợ TalkBack/VoiceOver, phản hồi xúc giác.

## 🧪 Chạy kiểm thử

```bash
cd frontend
flutter test
```

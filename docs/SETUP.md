# Hướng dẫn Setup

## Yêu cầu

- Python 3.12+
- Flutter 3.29+
- Docker + Docker Compose (cho PostgreSQL)
- Gemini API key ([đăng ký](https://aistudio.google.com/apikey))
- GPU (khuyến nghị cho Whisper + YOLO, có thể chạy CPU)

## Bước 1: Backend AI Gateway

```bash
cd backend
pip install -r requirements.txt
export GOOGLE_API_KEY='your-key-here'
export DATABASE_URL='postgresql+asyncpg://sgbe_admin:sgbe_secret@localhost:5432/sgbe_vision'

# Start PostgreSQL
cd ../docker && docker compose up -d postgres && cd ../backend

# Run server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

## Bước 2: VLM Server

```bash
cp .env.example .env
# Sửa GEMINI_API_KEY trong .env
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Bước 3: Frontend Flutter

```bash
cd frontend
flutter pub get
flutter run
```

## Chạy bằng Docker (tất cả trong một)

```bash
cd docker
export GOOGLE_API_KEY='your-key-here'
docker compose up -d
```

## Download models

```bash
bash data/scripts/download_models.sh
```

## Seed dữ liệu SGK

```bash
python data/scripts/seed_rag.py
```

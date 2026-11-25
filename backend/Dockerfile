FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/backend
COPY backend/requirements.txt backend/requirements-ai.txt ./
# requirements-ai.txt gồm requirements.txt + phụ thuộc của module AI (VLM_MODE=ai)
RUN pip install --no-cache-dir -r requirements-ai.txt
COPY backend/app ./app
COPY prompts /app/prompts
# Module AI của Phúc (ai/pipeline.py), dùng khi VLM_MODE=ai. Khóa API đưa vào lúc chạy, không nằm trong image.
COPY ai /app/ai
ENV PROMPTS_DIR=/app/prompts DATA_DIR=/app/data AI_DIR=/app/ai
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

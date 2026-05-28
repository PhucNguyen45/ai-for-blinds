import logging
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .vlm import VLMError, ask_vlm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VLM Server",
    description="Server tích hợp Gemini VLM cho app mobile gửi ảnh + câu hỏi",
    version="1.0.0",
)

origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index():
    index_html = STATIC_DIR / "index.html"
    if index_html.exists():
        return FileResponse(index_html)
    return JSONResponse({"message": "VLM Server running", "docs": "/docs"})


@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.gemini_model}


@app.post("/api/ask")
async def ask(
    image: UploadFile = File(..., description="Ảnh để VLM phân tích"),
    question: str = Form(..., description="Câu hỏi về ảnh"),
):
    max_bytes = settings.max_image_mb * 1024 * 1024
    image_bytes = await image.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Ảnh rỗng")
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Ảnh quá lớn (>{settings.max_image_mb}MB)",
        )

    started = time.time()
    try:
        answer = await ask_vlm(
            image_bytes=image_bytes,
            question=question,
            mime_type=image.content_type,
        )
    except VLMError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    elapsed_ms = int((time.time() - started) * 1000)
    logger.info(
        "ask ok: image=%s size=%dB q_len=%d elapsed=%dms",
        image.filename, len(image_bytes), len(question), elapsed_ms,
    )

    return {
        "answer": answer,
        "model": settings.gemini_model,
        "elapsed_ms": elapsed_ms,
    }

import logging
import time
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .tts import TTSError, list_voices, stream_tts
from .vlm import VLMError, VLMRateLimitError, ask_vlm, ask_vlm_voice

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VLM Server",
    description="Server tích hợp STT + VLM + TTS cho app trợ lý hình ảnh",
    version="2.0.0",
)

origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Question", "X-Answer", "X-Elapsed-Ms", "Retry-After"],
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
    return {"status": "ok", "model": settings.gemini_model, "voice": settings.tts_voice}


@app.get("/api/voices")
async def voices():
    try:
        return {"voices": await list_voices("vi")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


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
        raise HTTPException(status_code=413, detail=f"Ảnh quá lớn (>{settings.max_image_mb}MB)")

    started = time.time()
    try:
        answer = await ask_vlm(
            image_bytes=image_bytes,
            question=question,
            mime_type=image.content_type,
        )
    except VLMRateLimitError as e:
        headers = {"Retry-After": str(e.retry_after)} if e.retry_after else {}
        raise HTTPException(status_code=429, detail=str(e), headers=headers) from e
    except VLMError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    elapsed_ms = int((time.time() - started) * 1000)
    logger.info(
        "ask ok: image=%s size=%dB q_len=%d elapsed=%dms",
        image.filename,
        len(image_bytes),
        len(question),
        elapsed_ms,
    )

    return {"answer": answer, "model": settings.gemini_model, "elapsed_ms": elapsed_ms}


@app.post("/api/tts")
async def tts(text: str = Form(...), voice: str = Form(None)):
    """Standalone TTS endpoint - stream MP3 audio for given text."""
    try:

        async def gen():
            async for chunk in stream_tts(text, voice=voice):
                yield chunk

        return StreamingResponse(gen(), media_type="audio/mpeg")
    except TTSError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.post("/api/ask-voice")
async def ask_voice(
    image: UploadFile = File(..., description="Ảnh chụp"),
    audio: UploadFile = File(..., description="Audio câu hỏi (webm/ogg/mp3/wav)"),
):
    """Audio + image in → audio MP3 streamed out. Question/answer text in response headers."""
    max_image_bytes = settings.max_image_mb * 1024 * 1024
    max_audio_bytes = settings.max_audio_mb * 1024 * 1024

    image_bytes = await image.read()
    audio_bytes = await audio.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Ảnh rỗng")
    if len(image_bytes) > max_image_bytes:
        raise HTTPException(status_code=413, detail=f"Ảnh quá lớn (>{settings.max_image_mb}MB)")
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Audio rỗng")
    if len(audio_bytes) > max_audio_bytes:
        raise HTTPException(status_code=413, detail=f"Audio quá lớn (>{settings.max_audio_mb}MB)")

    started = time.time()
    try:
        question, answer = await ask_vlm_voice(
            image_bytes=image_bytes,
            audio_bytes=audio_bytes,
            image_mime=image.content_type,
            audio_mime=audio.content_type,
        )
    except VLMRateLimitError as e:
        headers = {"Retry-After": str(e.retry_after)} if e.retry_after else {}
        raise HTTPException(status_code=429, detail=str(e), headers=headers) from e
    except VLMError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    elapsed_ms = int((time.time() - started) * 1000)
    logger.info(
        "ask-voice ok: image=%dB audio=%dB q=%r elapsed=%dms",
        len(image_bytes),
        len(audio_bytes),
        question[:80],
        elapsed_ms,
    )

    headers = {
        "X-Question": quote(question, safe=""),
        "X-Answer": quote(answer, safe=""),
        "X-Elapsed-Ms": str(elapsed_ms),
        "Cache-Control": "no-store",
    }

    async def audio_stream():
        try:
            async for chunk in stream_tts(answer):
                yield chunk
        except TTSError as e:
            logger.error("TTS error during stream: %s", e)

    return StreamingResponse(audio_stream(), media_type="audio/mpeg", headers=headers)

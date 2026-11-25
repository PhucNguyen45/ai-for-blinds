"""SgBe API v1.

Chạy: cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
Tài liệu tương tác: http://<máy>:8000/docs
"""
import time

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import library, prompts, storage, stt
from .config import settings
from .schemas import (
    AskRequest,
    AskResult,
    BookPages,
    BookSummary,
    DescribeResult,
    Envelope,
    PageType,
    SttResult,
)
from .speech import clean_for_speech
from .vlm import VLMError, VLMTimeout, get_vlm, parse_describe_output

app = FastAPI(title="SgBe API", version="1.0.0", description="Trợ lý đọc học liệu cho học sinh khiếm thị")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

UNREADABLE_FALLBACK = "Mình chưa đọc được trang này. Bạn thử chụp lại, giữ máy thẳng và đủ sáng nhé."


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        self.status, self.code, self.message = status, code, message


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"data": None, "error": {"code": code, "message": message}})


@app.exception_handler(ApiError)
async def _api_error(_: Request, exc: ApiError):
    return _error(exc.status, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def _validation_error(_: Request, exc: RequestValidationError):
    return _error(422, "INVALID_REQUEST", "Yêu cầu gửi lên không hợp lệ.")


@app.exception_handler(StarletteHTTPException)
async def _http_error(_: Request, exc: StarletteHTTPException):
    code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
    return _error(exc.status_code, code, "Không tìm thấy địa chỉ này." if exc.status_code == 404 else str(exc.detail))


@app.exception_handler(Exception)
async def _unexpected(_: Request, exc: Exception):
    return _error(500, "INTERNAL", "Máy chủ gặp lỗi. Bạn thử lại sau nhé.")


def _ms(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000)


def _vlm_failure(exc: VLMError) -> ApiError:
    if isinstance(exc, VLMTimeout):
        return ApiError(504, "VLM_TIMEOUT", "Máy chủ xử lý quá lâu. Bạn thử chụp lại nhé.")
    return ApiError(502, "VLM_ERROR", "Chưa kết nối được mô hình. Bạn thử lại sau ít phút nhé.")


@app.get("/health")
async def health():
    return {
        "data": {
            "status": "ok",
            "vlm_mode": settings.vlm_mode,
            "model": settings.model_name,
            "prompt_version": settings.prompt_version,
            "stt_mode": settings.stt_mode,
        },
        "error": None,
    }


@app.post("/v1/describe", response_model=Envelope[DescribeResult])
async def describe(image: UploadFile = File(...), page_type: PageType = Form("auto")):
    t0 = time.perf_counter()
    raw = await image.read()
    try:
        image_id, sha, jpeg = await run_in_threadpool(storage.prepare_image, raw)
    except storage.ImageTooLarge:
        raise ApiError(413, "IMAGE_TOO_LARGE", f"Ảnh quá lớn, tối đa {settings.max_image_mb:g} MB. Bạn chụp lại nhé.")
    except storage.InvalidImage:
        raise ApiError(400, "INVALID_IMAGE", "Ảnh gửi lên không đọc được. Bạn chụp lại nhé.")

    cached = storage.cache_get(sha, page_type)
    if cached:
        storage.save_image(image_id, jpeg, cached["description"])
        result = DescribeResult(**{**cached, "image_id": image_id, "latency_ms": _ms(t0), "cached": True})
        storage.log_request(endpoint="describe", image_id=image_id, page_type=result.page_type,
                            model=result.model, prompt_version=result.prompt_version,
                            latency_ms=result.latency_ms, cached=True, ok=True)
        return {"data": result, "error": None}

    try:
        messages = prompts.describe_messages(jpeg, page_type)
        raw_text = await get_vlm().describe(messages, page_type)
    except VLMError as exc:
        storage.log_request(endpoint="describe", image_id=image_id, page_type=page_type,
                            model=settings.model_name, prompt_version=settings.prompt_version,
                            latency_ms=_ms(t0), cached=False, ok=False, error=str(exc)[:300])
        raise _vlm_failure(exc)

    description, resolved_type, unreadable = parse_describe_output(raw_text, page_type)
    description = clean_for_speech(description)
    if not description:
        description, unreadable = UNREADABLE_FALLBACK, True

    result = DescribeResult(
        image_id=image_id,
        description=description,
        page_type=resolved_type,
        unreadable=unreadable,
        model=settings.model_name,
        prompt_version=settings.prompt_version,
        latency_ms=_ms(t0),
        cached=False,
    )
    storage.save_image(image_id, jpeg, description)
    storage.cache_put(sha, page_type, result.model_dump(exclude={"image_id", "latency_ms", "cached"}))
    storage.log_request(endpoint="describe", image_id=image_id, page_type=resolved_type,
                        model=result.model, prompt_version=result.prompt_version,
                        latency_ms=result.latency_ms, cached=False, ok=True, unreadable=unreadable)
    return {"data": result, "error": None}


@app.post("/v1/ask", response_model=Envelope[AskResult])
async def ask(req: AskRequest):
    t0 = time.perf_counter()
    found = storage.load_image(req.image_id)
    if not found:
        raise ApiError(404, "IMAGE_NOT_FOUND", "Mình không còn giữ ảnh này. Bạn chụp lại giúp mình nhé.")
    jpeg, description = found
    try:
        messages = prompts.ask_messages(jpeg, description, req.question, [t.model_dump() for t in req.history])
        answer = clean_for_speech(await get_vlm().ask(messages))
    except VLMError as exc:
        storage.log_request(endpoint="ask", image_id=req.image_id, model=settings.model_name,
                            prompt_version=settings.prompt_version, latency_ms=_ms(t0), ok=False,
                            error=str(exc)[:300])
        raise _vlm_failure(exc)
    result = AskResult(image_id=req.image_id, answer=answer or "Mình chưa trả lời được câu này. Bạn hỏi lại theo cách khác nhé.",
                       model=settings.model_name, prompt_version=settings.prompt_version, latency_ms=_ms(t0))
    storage.log_request(endpoint="ask", image_id=req.image_id, model=result.model,
                        prompt_version=result.prompt_version, latency_ms=result.latency_ms, ok=True,
                        question=req.question)
    return {"data": result, "error": None}


@app.post("/v1/stt", response_model=Envelope[SttResult])
async def speech_to_text(audio: UploadFile = File(...)):
    t0 = time.perf_counter()
    raw = await audio.read()
    if not raw:
        raise ApiError(400, "INVALID_AUDIO", "Mình chưa nghe thấy gì. Bạn nói lại nhé.")
    if len(raw) > settings.max_audio_mb * 1024 * 1024:
        raise ApiError(413, "AUDIO_TOO_LARGE", "Đoạn ghi âm quá dài. Bạn nói ngắn hơn nhé.")
    try:
        text = await stt.transcribe(raw, audio.filename or "audio")
    except stt.SttError:
        raise ApiError(503, "STT_UNAVAILABLE", "Chức năng nghe giọng nói chưa sẵn sàng.")
    result = SttResult(text=text, latency_ms=_ms(t0))
    storage.log_request(endpoint="stt", latency_ms=result.latency_ms, ok=True)
    return {"data": result, "error": None}


@app.get("/v1/library", response_model=Envelope[list[BookSummary]])
async def list_library():
    return {"data": library.list_books(), "error": None}


@app.get("/v1/library/{book}/pages", response_model=Envelope[BookPages])
async def book_pages(book: str):
    found = library.get_book(book)
    if not found:
        raise ApiError(404, "BOOK_NOT_FOUND", "Không tìm thấy cuốn sách này trong thư viện.")
    return {"data": found, "error": None}

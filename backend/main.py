import os
import tempfile
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import google.generativeai as genai
import edge_tts

# Cấu hình Gemini — bắt buộc phải có GOOGLE_API_KEY trong môi trường
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError(
        "GOOGLE_API_KEY environment variable is required. "
        "Set it with: export GOOGLE_API_KEY='your-key-here'"
    )
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# Giới hạn kích thước file upload (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/bmp",
}

app = FastAPI(title="SgBe Vision API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validate_image(file: UploadFile) -> bytes:
    """Kiểm tra và đọc file ảnh, raise HTTPException nếu không hợp lệ."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type '{file.content_type}'. "
                   f"Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )
    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(contents)} bytes). Max: {MAX_FILE_SIZE} bytes",
        )
    return contents


@app.get("/")
def health():
    return {"status": "ok", "service": "SgBe Vision Backend"}


@app.post("/describe")
async def describe_image(file: UploadFile = File(...)):
    """Mô tả ảnh bằng tiếng Việt cho học sinh khiếm thị (dùng Gemini 2.5 Flash)."""
    contents = _validate_image(file)
    try:
        response = model.generate_content([
            "Bạn là trợ lý cho học sinh khiếm thị Việt Nam. "
            "Hãy mô tả chi tiết bức ảnh này bằng tiếng Việt một cách tự nhiên, dễ hiểu.",
            {"mime_type": file.content_type, "data": contents},
        ])
        return {"description": response.text}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini API error: {str(e)}")


@app.post("/ocr")
async def ocr_image(file: UploadFile = File(...)):
    """Nhận dạng văn bản từ ảnh (OCR)."""
    _validate_image(file)
    # TODO: Tích hợp PaddleOCRv5
    return {"text": "OCR service sẽ được tích hợp sau"}


@app.post("/tts")
async def text_to_speech(text: str):
    """Chuyển văn bản thành giọng nói tiếng Việt và trả về file audio."""
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    # Tạo file tạm với tên unique để tránh race condition
    tmp_dir = tempfile.gettempdir()
    output_path = os.path.join(tmp_dir, f"sgbe_tts_{uuid.uuid4().hex}.mp3")

    try:
        communicate = edge_tts.Communicate(text, "vi-VN-HoaiMyNeural")
        await communicate.save(output_path)

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="TTS generation failed")

        return FileResponse(
            output_path,
            media_type="audio/mpeg",
            filename="speech.mp3",
            headers={
                "Content-Disposition": 'attachment; filename="speech.mp3"',
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

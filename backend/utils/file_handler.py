"""
File upload validation and processing utilities.

Handles:
- Content type validation
- File size validation
- Temporary file management
"""

import os
import tempfile
import uuid
from typing import Optional

from fastapi import HTTPException, UploadFile

from backend.config import settings


def validate_image(file: UploadFile) -> bytes:
    """
    Validate and read an uploaded image file.

    Args:
        file: The uploaded file from FastAPI.

    Returns:
        Raw file bytes.

    Raises:
        HTTPException: If file type or size is invalid.
    """
    if file.content_type not in settings.allowed_content_types:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported content type '{file.content_type}'. "
                f"Allowed: {', '.join(settings.allowed_content_types)}"
            ),
        )

    contents = file.file.read()
    if len(contents) > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File too large ({len(contents)} bytes). "
                f"Max: {settings.max_file_size} bytes"
            ),
        )
    return contents


def validate_audio(file: UploadFile) -> bytes:
    """
    Validate and read an uploaded audio file.

    Args:
        file: The uploaded audio file.

    Returns:
        Raw file bytes.

    Raises:
        HTTPException: If file type or size is invalid.
    """
    allowed_audio_types = {
        "audio/mpeg",
        "audio/wav",
        "audio/x-wav",
        "audio/mp4",
        "audio/x-m4a",
        "audio/ogg",
        "audio/webm",
    }

    if file.content_type not in allowed_audio_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type '{file.content_type}'.",
        )

    contents = file.file.read()
    if len(contents) > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(contents)} bytes). Max: {settings.max_file_size} bytes",
        )
    return contents


def save_temp_file(contents: bytes, suffix: str = ".tmp") -> str:
    """
    Save bytes to a temporary file.

    Args:
        contents: File contents to write.
        suffix: File extension (e.g., '.png', '.wav').

    Returns:
        Path to the temporary file.
    """
    tmp_path = os.path.join(
        tempfile.gettempdir(),
        f"sgbe_{uuid.uuid4().hex}{suffix}",
    )
    with open(tmp_path, "wb") as f:
        f.write(contents)
    return tmp_path


def cleanup_temp_file(path: str) -> None:
    """Safely delete a temporary file."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass

"""Tests for utility modules."""

import io
import inspect
import pytest


class TestFileHandler:
    def test_validate_image_importable(self):
        """Verify validate_image helper is importable and is a function."""
        from backend.utils.file_handler import validate_image
        assert inspect.isfunction(validate_image)

    def test_validate_audio_importable(self):
        """Verify validate_audio helper is importable and is a function."""
        from backend.utils.file_handler import validate_audio
        assert inspect.isfunction(validate_audio)

    def test_validate_image_rejects_bad_content_type(self):
        """Should raise HTTPException 400 for unsupported content types."""
        from backend.utils.file_handler import validate_image
        from fastapi import UploadFile, HTTPException
        import io

        file = UploadFile(
            filename="test.txt",
            file=io.BytesIO(b"hello"),
            headers={"content-type": "text/plain"},
        )
        with pytest.raises(HTTPException) as exc:
            validate_image(file)
        assert exc.value.status_code == 400

    def test_validate_audio_rejects_bad_content_type(self):
        """Should raise HTTPException 400 for unsupported audio types."""
        from backend.utils.file_handler import validate_audio
        from fastapi import UploadFile, HTTPException
        import io

        file = UploadFile(
            filename="test.txt",
            file=io.BytesIO(b"hello"),
            headers={"content-type": "text/plain"},
        )
        with pytest.raises(HTTPException) as exc:
            validate_audio(file)
        assert exc.value.status_code == 400

    def test_validate_image_accepts_valid_png(self):
        """Should accept valid PNG content type and return bytes."""
        from backend.utils.file_handler import validate_image
        from fastapi import UploadFile
        import io

        file = UploadFile(
            filename="test.png",
            file=io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100),
            headers={"content-type": "image/png"},
        )
        result = validate_image(file)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_validate_audio_accepts_valid_wav(self):
        """Should accept valid WAV content type and return bytes."""
        from backend.utils.file_handler import validate_audio
        from fastapi import UploadFile
        import io

        file = UploadFile(
            filename="test.wav",
            file=io.BytesIO(b"RIFF" + b"\x00" * 100),
            headers={"content-type": "audio/wav"},
        )
        result = validate_audio(file)
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestResponseBuilder:
    def test_success_response_format(self):
        """Verify success_response produces a valid JSONResponse with expected fields."""
        from backend.utils.response_builder import success_response
        resp = success_response(data={"foo": "bar"}, message="OK")
        assert resp.status_code == 200
        body = resp.body.decode()
        assert '"success":true' in body
        assert '"message":"OK"' in body
        assert '"foo":"bar"' in body

    def test_error_response_format(self):
        """Verify error_response produces a valid JSONResponse with expected fields."""
        from backend.utils.response_builder import error_response
        resp = error_response(message="Fail", status_code=400, detail="Something went wrong")
        assert resp.status_code == 400
        body = resp.body.decode()
        assert '"success":false' in body
        assert '"detail":"Something went wrong"' in body

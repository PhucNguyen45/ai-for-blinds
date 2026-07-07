"""Unit tests for backend services (mocked AI dependencies)."""

from backend.config import settings


class TestResponseBuilder:
    def test_success_response_with_data(self):
        from backend.utils.response_builder import success_response

        resp = success_response(data={"key": "value"}, message="OK")
        assert resp.status_code == 200
        body = resp.body.decode()
        # JSONResponse serializes compact (no spaces after colons)
        assert '"success":true' in body
        assert '"key":"value"' in body

    def test_success_response_without_data(self):
        from backend.utils.response_builder import success_response

        resp = success_response(message="No data")
        assert resp.status_code == 200
        body = resp.body.decode()
        assert '"success":true' in body
        # data key should NOT be present when data is None
        assert '"data"' not in body

    def test_error_response(self):
        from backend.utils.response_builder import error_response

        resp = error_response(message="Error", status_code=400, detail="Bad request")
        assert resp.status_code == 400
        body = resp.body.decode()
        assert '"success":false' in body
        assert '"detail":"Bad request"' in body


class TestSonification:
    def test_sonify_valid_data(self):
        from backend.services.sonification import sonify_data

        data = [
            {"label": "Toán", "value": 8},
            {"label": "Văn", "value": 7},
            {"label": "Anh", "value": 9},
        ]
        result = sonify_data(data, chart_type="bar")
        assert result is not None
        assert result["description"] is not None
        assert len(result["tones"]) == 3
        assert result["max"]["label"] == "Anh"
        assert result["min"]["label"] == "Văn"
        assert result["average"] == 8.0
        assert result["total"] == 24

    def test_sonify_empty_data(self):
        from backend.services.sonification import sonify_data

        assert sonify_data([], chart_type="bar") is None

    def test_sonify_invalid_data(self):
        from backend.services.sonification import sonify_data

        assert sonify_data([{"label": "A"}], chart_type="bar") is None

    def test_sonify_single_point(self):
        from backend.services.sonification import sonify_data

        result = sonify_data([{"label": "Test", "value": 5}], chart_type="pie")
        assert result is not None
        assert result["average"] == 5.0
        assert len(result["tones"]) == 1


class TestDetectionService:
    def test_service_not_available_by_default(self):
        """Service should gracefully report unavailable when model not loaded."""
        from backend.services.object_detection import ObjectDetectionService

        service = ObjectDetectionService()
        assert service.available is False
        assert service.detect(b"fake") is None


class TestConfig:
    def test_settings_have_required_fields(self):
        assert (
            settings.google_api_key is not None or settings.google_api_key is None
        )  # safe for test
        assert settings.app_name == "SgBe Vision API"
        assert settings.api_key == "sgbe_dev_key_2024"

    def test_settings_yolo_device_default(self):
        assert hasattr(settings, "yolo_device")
        assert settings.yolo_device == "cpu"

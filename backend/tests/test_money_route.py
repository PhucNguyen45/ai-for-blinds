"""Integration tests for POST /money (VND denomination recognition)."""

from fastapi import status
from backend.services.money_service import money_service


class TestMoneyRoute:
    def test_money_without_auth(self, client):
        client.headers.update({"X-API-Key": "invalid-key"})
        response = client.post(
            "/money", files={"file": ("test.png", b"fake", "image/png")}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_money_no_file(self, client):
        response = client.post("/money")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_money_bad_content_type(self, client):
        response = client.post(
            "/money", files={"file": ("test.txt", b"fake", "text/plain")}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_money_recognized(self, client, sample_image_bytes, monkeypatch):
        monkeypatch.setattr(
            money_service,
            "recognize",
            lambda contents, mime_type: {
                "denomination": "500000",
                "formatted": "500.000 đồng",
                "method": "vlm",
                "confidence": 0.95,
            },
        )
        response = client.post(
            "/money",
            files={"file": ("note.png", sample_image_bytes(), "image/png")},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["denomination"] == "500000"
        assert data["data"]["method"] == "vlm"
        assert data["data"]["confidence"] == 0.95

    def test_money_not_detected(self, client, sample_image_bytes, monkeypatch):
        monkeypatch.setattr(
            money_service,
            "recognize",
            lambda contents, mime_type: {
                "denomination": None,
                "formatted": None,
                "method": "vlm",
                "confidence": 0.0,
            },
        )
        response = client.post(
            "/money",
            files={"file": ("note.png", sample_image_bytes(), "image/png")},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["denomination"] is None

    def test_money_unavailable(self, client, sample_image_bytes, monkeypatch):
        monkeypatch.setattr(money_service, "recognize", lambda contents, mime_type: None)
        response = client.post(
            "/money",
            files={"file": ("note.png", sample_image_bytes(), "image/png")},
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

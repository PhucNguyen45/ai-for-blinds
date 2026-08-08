"""Integration tests for the Persistent Visual Memory (/moments) routes."""

from contextlib import contextmanager
from unittest.mock import PropertyMock, patch

from fastapi import status

from backend.services.moment_service import moment_service


@contextmanager
def _available(value: bool):
    """Mock the read-only `available` property on the moment service class."""
    with patch.object(
        type(moment_service), "available", new_callable=PropertyMock, return_value=value
    ):
        yield


class TestMomentsAuth:
    def test_moments_require_auth(self, client):
        """Should return 403 when invalid API key provided."""
        client.headers.update({"X-API-Key": "invalid-key"})
        response = client.post("/moments", json={"title": "test"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_requires_auth(self, client):
        client.headers.update({"X-API-Key": "invalid-key"})
        response = client.get("/moments")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestMomentsValidation:
    def test_create_missing_device_id(self, client):
        """422 when X-Device-Id header is missing."""
        with _available(True):
            response = client.post("/moments", json={"title": "test"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_missing_title(self, client):
        """422 when title is missing."""
        with _available(True):
            response = client.post(
                "/moments",
                json={"content": "nội dung"},
                headers={"X-Device-Id": "device-1"},
            )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_missing_query(self, client):
        """422 when search query is missing."""
        with _available(True):
            response = client.post(
                "/moments/search",
                json={},
                headers={"X-Device-Id": "device-1"},
            )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestMomentsUnavailable:
    def test_create_returns_503_when_db_unavailable(self, client):
        with _available(False):
            response = client.post(
                "/moments",
                json={"title": "test"},
                headers={"X-Device-Id": "device-1"},
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_list_returns_503_when_db_unavailable(self, client):
        with _available(False):
            response = client.get(
                "/moments", headers={"X-Device-Id": "device-1"}
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestMomentsCreate:
    def test_create_returns_moment(self, client):
        expected = {
            "id": "abc-123",
            "title": "Công thức diện tích",
            "content": "S = πr²",
            "content_type": "text",
            "grade": 9,
            "subject": "Toán",
            "created_at": "2026-01-01T00:00:00+00:00",
        }
        with _available(True), patch(
            "backend.api.routes.moments.moment_service.create",
            return_value=expected,
        ):
            response = client.post(
                "/moments",
                json={
                    "title": "Công thức diện tích",
                    "content": "S = πr²",
                    "content_type": "text",
                    "grade": 9,
                    "subject": "Toán",
                },
                headers={"X-Device-Id": "device-1"},
            )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["id"] == "abc-123"

    def test_create_failure_returns_500(self, client):
        with _available(True), patch(
            "backend.api.routes.moments.moment_service.create",
            return_value=None,
        ):
            response = client.post(
                "/moments",
                json={"title": "test"},
                headers={"X-Device-Id": "device-1"},
            )
        assert response.status_code == 500


class TestMomentsList:
    def test_list_returns_moments(self, client):
        expected = [{"id": "1", "title": "a", "content": "", "content_type": "text"}]
        with _available(True), patch(
            "backend.api.routes.moments.moment_service.list_for_device",
            return_value=expected,
        ):
            response = client.get(
                "/moments", headers={"X-Device-Id": "device-1"}
            )
        assert response.status_code == 200
        assert response.json()["data"] == expected


class TestMomentsDelete:
    def test_delete_existing(self, client):
        with _available(True), patch(
            "backend.api.routes.moments.moment_service.delete",
            return_value=True,
        ):
            response = client.delete(
                "/moments/m1", headers={"X-Device-Id": "device-1"}
            )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_delete_missing_returns_404(self, client):
        with _available(True), patch(
            "backend.api.routes.moments.moment_service.delete",
            return_value=False,
        ):
            response = client.delete(
                "/moments/does-not-exist", headers={"X-Device-Id": "device-1"}
            )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestMomentsSearch:
    def test_search_returns_results(self, client):
        results = [
            {
                "id": "m1",
                "title": "Định lý Pytago",
                "content": "a² + b² = c²",
                "content_type": "text",
                "created_at": "2026-01-01T00:00:00+00:00",
                "distance": 0.1,
            }
        ]
        with _available(True), patch(
            "backend.api.routes.moments.moment_service.search",
            return_value=results,
        ):
            response = client.post(
                "/moments/search",
                json={"query": "Pytago", "n_results": 5},
                headers={"X-Device-Id": "device-1"},
            )
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["query"] == "Pytago"
        assert body["data"]["results"][0]["id"] == "m1"

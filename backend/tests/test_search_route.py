"""Integration tests for POST /search (Internet retrieval)."""

from fastapi import status
from backend.services.ir_service import ir_service


class TestSearchRoute:
    def test_search_without_auth(self, client):
        client.headers.update({"X-API-Key": "invalid-key"})
        response = client.post("/search", json={"query": "Hà Nội"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_search_missing_query(self, client):
        response = client.post("/search", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_empty_query(self, client):
        response = client.post("/search", json={"query": ""})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_n_results_out_of_range(self, client):
        response = client.post("/search", json={"query": "test", "n_results": 0})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_returns_results(self, client, monkeypatch):
        monkeypatch.setattr(
            ir_service,
            "search",
            lambda query, n: [
                {
                    "title": "Hà Nội – Wikipedia",
                    "snippet": "Hà Nội là thủ đô của Việt Nam.",
                    "url": "https://vi.wikipedia.org/wiki/Hà_Nội",
                    "source": "web",
                    "score": 1.0,
                },
                {
                    "title": "Tin Hà Nội hôm nay",
                    "snippet": "Cập nhật tin tức mới nhất về Hà Nội.",
                    "url": "https://vnexpress.net/ha-noi",
                    "source": "news",
                    "score": 0.8,
                },
            ],
        )
        response = client.post("/search", json={"query": "Hà Nội", "n_results": 5})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["query"] == "Hà Nội"
        results = data["data"]["results"]
        assert len(results) == 2
        assert results[0]["source"] == "web"
        assert results[1]["source"] == "news"

    def test_search_no_results(self, client, monkeypatch):
        monkeypatch.setattr(ir_service, "search", lambda query, n: [])
        response = client.post("/search", json={"query": "không tồn tại"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["results"] == []

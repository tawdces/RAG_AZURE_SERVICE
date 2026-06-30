import pytest


class TestHealthEndpoint:

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAPIStructure:

    def test_api_docs_available(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_api_redoc_available(self, client):
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "info" in schema
        assert "RAG Azure Service" in schema["info"]["title"]

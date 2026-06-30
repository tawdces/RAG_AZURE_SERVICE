from types import SimpleNamespace

from azure.core.exceptions import HttpResponseError

from src.api.routes import blob as blob_route
from src.api.routes import indexer as indexer_route
from src.api.routes import knowledge as knowledge_route
from src.api.routes import search as search_route


class TestBlobRoutes:
    def test_blob_upload_route_returns_service_result(self, monkeypatch, client):
        monkeypatch.setattr(blob_route, "upload_pdf_files", lambda: {"uploaded": ["a.pdf"], "total": 1})

        response = client.post("/blob/upload")

        assert response.status_code == 200
        assert response.json() == {"uploaded": ["a.pdf"], "total": 1}


class TestIndexerRoutes:
    def test_indexer_run_route_returns_404_for_missing_indexer(self, monkeypatch, client):
        def raise_value_error():
            raise ValueError("Indexer 'x' not found")

        monkeypatch.setattr(indexer_route, "trigger_indexer", raise_value_error)

        response = client.post("/indexer/run")

        assert response.status_code == 404
        assert response.json() == {"detail": "Indexer 'x' not found"}

    def test_indexer_run_route_returns_502_for_azure_error(self, monkeypatch, client):
        def raise_http_error():
            raise HttpResponseError(message="boom", response=None, error=None)

        monkeypatch.setattr(indexer_route, "trigger_indexer", raise_http_error)

        response = client.post("/indexer/run")

        assert response.status_code == 502
        assert "Azure error" in response.json()["detail"]

    def test_indexer_status_route_returns_404_for_missing_indexer(self, monkeypatch, client):
        monkeypatch.setattr(indexer_route, "get_indexer_status", lambda: (_ for _ in ()).throw(ValueError("missing")))

        response = client.get("/indexer/status")

        assert response.status_code == 404
        assert response.json() == {"detail": "missing"}


class TestKnowledgeRoutes:
    def test_knowledge_route_rejects_empty_query(self, client):
        response = client.post("/knowledge/ask", json={"query": "   "})

        assert response.status_code == 400
        assert response.json() == {"detail": "Query must not be empty"}

    def test_knowledge_route_returns_answer(self, monkeypatch, client):
        monkeypatch.setattr(knowledge_route, "retrieve_answer", lambda query: {"answer": f"answer:{query}"})

        response = client.post("/knowledge/ask", json={"query": "hello"})

        assert response.status_code == 200
        assert response.json() == {"query": "hello", "answer": "answer:hello"}


class TestSearchRoutes:
    def test_search_route_rejects_empty_query(self, client):
        response = client.post("/search/query", json={"query": "   ", "top": 1})

        assert response.status_code == 400
        assert response.json() == {"detail": "Query must not be empty"}

    def test_search_route_returns_results(self, monkeypatch, client):
        monkeypatch.setattr(search_route, "search", lambda query, top: [{"score": 1.0, "title": "t", "chunk": "x" * 600}])

        response = client.post("/search/query", json={"query": "hello", "top": 2})

        assert response.status_code == 200
        assert response.json()["query"] == "hello"
        assert response.json()["results"][0]["chunk"] == "x" * 600

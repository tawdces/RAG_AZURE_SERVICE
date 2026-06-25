import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    monkeypatch.setenv("PROJECT_ENDPOINT", "https://test.cognitiveservices.azure.com/")
    monkeypatch.setenv("PROJECT_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_STORAGE_CONTAINER_NAME", "test-container")
    monkeypatch.setenv("AZURE_STORAGE_CONNECTION_STRING", "test-connection")
    monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://test-search.search.windows.net")
    monkeypatch.setenv("AZURE_SEARCH_INDEX_NAME", "test-index")
    monkeypatch.setenv("AZURE_SEARCH_INDEXER_NAME", "test-indexer")
    monkeypatch.setenv("AZURE_SEARCH_API_KEY", "test-api-key")
    monkeypatch.setenv("KNOWLEDGE_BASE_NAME", "test-kb")
    monkeypatch.setenv("KNOWLEDGE_SOURCE_NAME", "test-source")

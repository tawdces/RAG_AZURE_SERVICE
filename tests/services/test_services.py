from types import SimpleNamespace

import pytest
from azure.core.exceptions import HttpResponseError, ResourceExistsError, ResourceNotFoundError

import src.services.blob_service as blob_service
import src.services.indexer_service as indexer_service
import src.services.knowledge_service as knowledge_service
import src.services.search_service as search_service


class TestBlobService:
    def test_get_container_client_uses_config(self, monkeypatch):
        created = {}

        class FakeBlobServiceClient:
            @classmethod
            def from_connection_string(cls, conn):
                created["conn"] = conn
                return cls()

            def get_container_client(self, name):
                created["container"] = name
                return "container-client"

        monkeypatch.setattr(blob_service, "BlobServiceClient", FakeBlobServiceClient)
        monkeypatch.setattr(blob_service, "AZURE_STORAGE_CONNECTION_STRING", "conn-str")
        monkeypatch.setattr(blob_service, "AZURE_STORAGE_CONTAINER_NAME", "container-name")

        client = blob_service.get_container_client()

        assert client == "container-client"
        assert created == {"conn": "conn-str", "container": "container-name"}

    def test_upload_pdf_files_uploads_and_skips_existing_files(self, monkeypatch, tmp_path):
        pdf_folder = tmp_path / "pdf"
        pdf_folder.mkdir()
        (pdf_folder / "one.pdf").write_bytes(b"one")
        (pdf_folder / "two.pdf").write_bytes(b"two")
        monkeypatch.setattr(blob_service, "PDF_FOLDER", pdf_folder)

        class FakeContainerClient:
            def __init__(self):
                self.uploaded = []

            def upload_blob(self, *, name, data, overwrite=False):
                if name == "two.pdf":
                    raise ResourceExistsError("exists")
                self.uploaded.append((name, overwrite))

        fake_container = FakeContainerClient()
        monkeypatch.setattr(blob_service, "get_container_client", lambda: fake_container)

        result = blob_service.upload_pdf_files()

        assert result == {"uploaded": ["one.pdf"], "total": 1}
        assert fake_container.uploaded == [("one.pdf", False)]


class TestIndexerService:
    def test_get_indexer_client_uses_configuration(self, monkeypatch):
        seen = {}

        class FakeSearchIndexerClient:
            def __init__(self, endpoint, credential):
                seen["endpoint"] = endpoint
                seen["credential"] = credential

        monkeypatch.setattr(indexer_service, "SearchIndexerClient", FakeSearchIndexerClient)
        monkeypatch.setattr(indexer_service, "AzureKeyCredential", lambda key: f"key:{key}")
        monkeypatch.setattr(indexer_service, "AZURE_SEARCH_ENDPOINT", "https://search")
        monkeypatch.setattr(indexer_service, "AZURE_SEARCH_API_KEY", "abc")

        client = indexer_service.get_indexer_client()

        assert isinstance(client, FakeSearchIndexerClient)
        assert seen == {"endpoint": "https://search", "credential": "key:abc"}

    def test_trigger_indexer_reports_running_indexer(self, monkeypatch):
        class FakeClient:
            def __init__(self):
                self.status_calls = []
                self.run_calls = []

            def get_indexer_status(self, name):
                self.status_calls.append(name)
                return SimpleNamespace(last_result=SimpleNamespace(status="inProgress"))

            def run_indexer(self, name):
                self.run_calls.append(name)

        fake_client = FakeClient()
        monkeypatch.setattr(indexer_service, "get_indexer_client", lambda: fake_client)
        monkeypatch.setattr(indexer_service, "AZURE_SEARCH_INDEXER_NAME", "my-indexer")

        result = indexer_service.trigger_indexer()

        assert result == {
            "triggered": False,
            "message": "Indexer is already running",
            "status": "inProgress",
        }
        assert fake_client.status_calls == ["my-indexer"]
        assert fake_client.run_calls == []

    def test_trigger_indexer_raises_when_indexer_missing(self, monkeypatch):
        class FakeClient:
            def get_indexer_status(self, name):
                raise ResourceNotFoundError("missing")

        monkeypatch.setattr(indexer_service, "get_indexer_client", lambda: FakeClient())
        monkeypatch.setattr(indexer_service, "AZURE_SEARCH_INDEXER_NAME", "missing-indexer")

        with pytest.raises(ValueError, match="missing-indexer"):
            indexer_service.trigger_indexer()

    def test_trigger_indexer_returns_running_status_on_conflict(self, monkeypatch):
        class FakeClient:
            def get_indexer_status(self, name):
                return SimpleNamespace(last_result=None)

            def run_indexer(self, name):
                error = HttpResponseError(message="conflict", response=None, error=None)
                error.status_code = 409
                raise error

        monkeypatch.setattr(indexer_service, "get_indexer_client", lambda: FakeClient())
        monkeypatch.setattr(indexer_service, "AZURE_SEARCH_INDEXER_NAME", "my-indexer")

        result = indexer_service.trigger_indexer()

        assert result["status"] == "inProgress"
        assert result["triggered"] is False

    def test_trigger_indexer_raises_on_other_http_errors(self, monkeypatch):
        class FakeClient:
            def get_indexer_status(self, name):
                return SimpleNamespace(last_result=None)

            def run_indexer(self, name):
                raise HttpResponseError(message="boom", response=None, error=None, status_code=500)

        monkeypatch.setattr(indexer_service, "get_indexer_client", lambda: FakeClient())
        monkeypatch.setattr(indexer_service, "AZURE_SEARCH_INDEXER_NAME", "my-indexer")

        with pytest.raises(HttpResponseError):
            indexer_service.trigger_indexer()

    def test_get_indexer_status_reports_last_result_details(self, monkeypatch):
        class FakeClient:
            def get_indexer_status(self, name):
                return SimpleNamespace(
                    last_result=SimpleNamespace(
                        status="succeeded",
                        start_time=SimpleNamespace(isoformat=lambda: "2024-01-01T00:00:00"),
                        end_time=SimpleNamespace(isoformat=lambda: "2024-01-01T01:00:00"),
                        item_count=10,
                        failed_item_count=2,
                        errors=[SimpleNamespace(error_message="one")],
                    )
                )

        monkeypatch.setattr(indexer_service, "get_indexer_client", lambda: FakeClient())
        monkeypatch.setattr(indexer_service, "AZURE_SEARCH_INDEXER_NAME", "my-indexer")

        result = indexer_service.get_indexer_status()

        assert result["status"] == "succeeded"
        assert result["start_time"] == "2024-01-01T00:00:00"
        assert result["end_time"] == "2024-01-01T01:00:00"
        assert result["items_processed"] == 10
        assert result["items_failed"] == 2
        assert result["errors"] == ["one"]

    def test_get_indexer_status_returns_never_run_when_no_last_result(self, monkeypatch):
        class FakeClient:
            def get_indexer_status(self, name):
                return SimpleNamespace(last_result=None)

        monkeypatch.setattr(indexer_service, "get_indexer_client", lambda: FakeClient())
        monkeypatch.setattr(indexer_service, "AZURE_SEARCH_INDEXER_NAME", "my-indexer")

        result = indexer_service.get_indexer_status()

        assert result["status"] == "never_run"
        assert result["items_processed"] == 0
        assert result["items_failed"] == 0
        assert result["errors"] == []


class TestKnowledgeService:
    def test_retrieve_answer_formats_sources_and_strips_refs(self, monkeypatch):
        class FakeClient:
            def retrieve(self, retrieval_request):
                return SimpleNamespace(
                    response=[SimpleNamespace(content=[SimpleNamespace(text="Answer [ref_id:1]")])],
                    references=[
                        SimpleNamespace(title="doc1.pdf", docKey="doc1_pages_0", rerankerScore=0.9, as_dict=lambda: {"title": "doc1.pdf", "docKey": "doc1_pages_0", "rerankerScore": 0.9}),
                        SimpleNamespace(title="doc1.pdf", docKey="doc1_pages_1", rerankerScore=0.95, as_dict=lambda: {"title": "doc1.pdf", "docKey": "doc1_pages_1", "rerankerScore": 0.95}),
                        SimpleNamespace(title="doc2.pdf", docKey="doc2", rerankerScore=0.7, as_dict=lambda: {"title": "doc2.pdf", "docKey": "doc2", "rerankerScore": 0.7}),
                    ],
                    activity=[
                        {"type": "searchIndex", "searchIndexArguments": {"search": "foo"}, "count": 7},
                        {"type": "modelQueryPlanning", "inputTokens": 3, "outputTokens": 4, "elapsedMs": 5, "modelName": "gpt"},
                        {"type": "modelAnswerSynthesis", "inputTokens": 6, "outputTokens": 7, "elapsedMs": 8, "modelName": "o1"},
                        {"type": "agenticReasoning", "reasoningTokens": 9},
                    ],
                )

        monkeypatch.setattr(knowledge_service, "get_kb_client", lambda: FakeClient())
        monkeypatch.setattr(knowledge_service, "KNOWLEDGE_SOURCE_NAME", "source")
        monkeypatch.setattr(knowledge_service, "KNOWLEDGE_BASE_NAME", "base")

        result = knowledge_service.retrieve_answer("hello")

        assert result["answer"].startswith("Answer")
        assert "อ้างอิง:" in result["answer"]
        assert "doc1.pdf" in result["answer"]
        assert "doc2.pdf" in result["answer"]

    def test_helper_functions_format_and_strip_references(self):
        assert knowledge_service._strip_ref_ids("Answer [ref_id:1]") == "Answer"
        assert knowledge_service._format_reference_block([]) == ""
        assert "หน้า 2" in knowledge_service._format_reference_block([
            {"file": "doc.pdf", "page": 2, "reranker_score": 0.5},
        ])

    def test_dump_raw_result_prints_json(self, capsys):
        knowledge_service._dump_raw_result(SimpleNamespace(answer="ok"))

        captured = capsys.readouterr().out
        assert "RAW RESULT DUMP" in captured
        assert '"answer": "ok"' in captured

    def test_print_subqueries_handles_empty_activity(self, capsys):
        knowledge_service._print_subqueries(SimpleNamespace(activity=[]))

        captured = capsys.readouterr().out
        assert "no activity found" in captured


class TestSearchService:
    def test_search_service_returns_trimmed_results(self, monkeypatch):
        class FakeClient:
            def search(self, search_text, top):
                return [{"@search.score": 0.42, "title": "A", "chunk": "abc" * 200}]

        monkeypatch.setattr(search_service, "get_search_client", lambda: FakeClient())

        results = search_service.search("hello", top=3)

        assert results[0]["score"] == 0.42
        assert results[0]["title"] == "A"
        assert len(results[0]["chunk"]) == 500

    def test_search_service_uses_empty_chunk_when_missing(self, monkeypatch):
        class FakeClient:
            def search(self, search_text, top):
                return [{"@search.score": 0.1, "title": "B"}]

        monkeypatch.setattr(search_service, "get_search_client", lambda: FakeClient())

        results = search_service.search("hello", top=1)

        assert results[0]["chunk"] == ""

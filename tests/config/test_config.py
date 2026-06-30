import importlib


def _load_config_module():
    import src.config as config
    return importlib.reload(config)


class TestConfigLoading:

    def test_config_loads_from_env(self):
        config = _load_config_module()

        assert config.AZURE_SEARCH_ENDPOINT is not None
        assert config.AZURE_SEARCH_API_KEY is not None
        assert config.AZURE_SEARCH_INDEX_NAME is not None
        assert config.AZURE_SEARCH_INDEXER_NAME is not None
        assert config.AZURE_STORAGE_CONTAINER_NAME is not None
        assert config.AZURE_STORAGE_CONNECTION_STRING is not None
        assert config.KNOWLEDGE_BASE_NAME is not None
        assert config.KNOWLEDGE_SOURCE_NAME is not None

    def test_config_azure_search_endpoint(self):
        config = _load_config_module()
        assert config.AZURE_SEARCH_ENDPOINT == "https://test-search.search.windows.net"

    def test_config_azure_storage_container(self):
        config = _load_config_module()
        assert config.AZURE_STORAGE_CONTAINER_NAME == "test-container"

    def test_config_knowledge_base(self):
        config = _load_config_module()
        assert config.KNOWLEDGE_BASE_NAME == "test-kb"

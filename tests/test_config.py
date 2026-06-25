import os
import pytest
from src import config


class TestConfigLoading:

    def test_config_loads_from_env(self):
        assert config.PROJECT_ENDPOINT is not None
        assert config.AZURE_SEARCH_ENDPOINT is not None
        assert config.AZURE_STORAGE_CONNECTION_STRING is not None

    def test_config_azure_search_endpoint(self):
        assert config.AZURE_SEARCH_ENDPOINT is not None

    def test_config_azure_storage_container(self):
        assert config.AZURE_STORAGE_CONTAINER_NAME is not None

    def test_config_knowledge_base(self):
        assert config.KNOWLEDGE_BASE_NAME is not None
        assert config.KNOWLEDGE_SOURCE_NAME is not None

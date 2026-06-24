from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_INDEX_NAME,
    AZURE_SEARCH_API_KEY,
)


def get_search_client() -> SearchClient:
    return SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )


def search(query: str, top: int = 5) -> list[dict]:
    client = get_search_client()

    results = client.search(search_text=query, top=top)

    return [
        {
            "score": result.get("@search.score"),
            "title": result.get("title"),
            "chunk": result.get("chunk", "")[:500],
        }
        for result in results
    ]
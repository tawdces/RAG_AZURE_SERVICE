import logging
import time
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_INDEX_NAME,
    AZURE_SEARCH_API_KEY,
)

logger = logging.getLogger("app")


def get_search_client() -> SearchClient:
    return SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )


def search(query: str, top: int = 5) -> list[dict]:
    logger.info(
        f"query: {query} | status: started | top: {top}",
        extra={"pipeline": "query", "stage": "search", "query": query, "top": top},
    )
    start = time.time()

    client = get_search_client()

    try:
        results = client.search(search_text=query, top=top)
        parsed = [
            {
                "score": result.get("@search.score"),
                "title": result.get("title"),
                "chunk": result.get("chunk", "")[:500],
            }
            for result in results
        ]
    except HttpResponseError:
        logger.error(
            f"query: {query} | status: failed",
            extra={"pipeline": "query", "stage": "search", "query": query},
            exc_info=True,
        )
        raise

    duration_ms = round((time.time() - start) * 1000, 2)
    logger.info(
        f"query: {query} | duration: {duration_ms}ms | results: {len(parsed)}",
        extra={
            "pipeline": "query",
            "stage": "search",
            "query": query,
            "result_count": len(parsed),
            "duration_ms": duration_ms,
        },
    )

    return parsed
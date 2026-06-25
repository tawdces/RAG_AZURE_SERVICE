from pathlib import Path
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexerClient
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError

import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_API_KEY,
    AZURE_SEARCH_INDEXER_NAME,
)


def get_indexer_client() -> SearchIndexerClient:
    return SearchIndexerClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )


def trigger_indexer() -> dict:
    client = get_indexer_client()

    try:
        status = client.get_indexer_status(AZURE_SEARCH_INDEXER_NAME)
        last_run = status.last_result
        if last_run and last_run.status == "inProgress":
            return {
                "triggered": False,
                "message": "Indexer is already running",
                "status": "inProgress",
            }
    except ResourceNotFoundError:
        raise ValueError(f"Indexer '{AZURE_SEARCH_INDEXER_NAME}' not found")

    try:
        client.run_indexer(AZURE_SEARCH_INDEXER_NAME)
        return {
            "triggered": True,
            "message": f"Indexer '{AZURE_SEARCH_INDEXER_NAME}' started successfully",
            "status": "running",
        }
    except HttpResponseError as e:
        if e.status_code == 409:
            return {
                "triggered": False,
                "message": "Indexer is already running",
                "status": "inProgress",
            }
        raise


def get_indexer_status() -> dict:
    client = get_indexer_client()

    try:
        status = client.get_indexer_status(AZURE_SEARCH_INDEXER_NAME)
    except ResourceNotFoundError:
        raise ValueError(f"Indexer '{AZURE_SEARCH_INDEXER_NAME}' not found")

    last = status.last_result

    return {
        "indexer": AZURE_SEARCH_INDEXER_NAME,
        "status": last.status if last else "never_run",
        "start_time": last.start_time.isoformat() if last and last.start_time else None,
        "end_time": last.end_time.isoformat() if last and last.end_time else None,
        "items_processed": last.item_count if last else 0,
        "items_failed": last.failed_item_count if last else 0,
        "errors": [e.error_message for e in (last.errors or [])][:5],
    }
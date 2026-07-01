import logging
import time
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

logger = logging.getLogger("app")


def get_indexer_client() -> SearchIndexerClient:
    return SearchIndexerClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )


def trigger_indexer() -> dict:
    logger.info(
        f"indexer: {AZURE_SEARCH_INDEXER_NAME} | status: trigger_requested",
        extra={"pipeline": "ingestion", "stage": "indexer_trigger", "indexer": AZURE_SEARCH_INDEXER_NAME},
    )
    start = time.time()
    client = get_indexer_client()

    try:
        status = client.get_indexer_status(AZURE_SEARCH_INDEXER_NAME)
        last_run = status.last_result
        if last_run and last_run.status == "inProgress":
            logger.info(
                f"indexer: {AZURE_SEARCH_INDEXER_NAME} | status: already_running | trigger_skipped",
                extra={"pipeline": "ingestion", "stage": "indexer_trigger", "indexer": AZURE_SEARCH_INDEXER_NAME},
            )
            return {
                "triggered": False,
                "message": "Indexer is already running",
                "status": "inProgress",
            }
    except ResourceNotFoundError:
        logger.error(
            f"indexer: {AZURE_SEARCH_INDEXER_NAME} | status: not_found",
            extra={"pipeline": "ingestion", "stage": "indexer_trigger", "indexer": AZURE_SEARCH_INDEXER_NAME},
        )
        raise ValueError(f"Indexer '{AZURE_SEARCH_INDEXER_NAME}' not found")

    try:
        client.run_indexer(AZURE_SEARCH_INDEXER_NAME)
        duration_ms = round((time.time() - start) * 1000, 2)
        logger.info(
            f"indexer: {AZURE_SEARCH_INDEXER_NAME} | status: triggered | duration: {duration_ms}ms",
            extra={
                "pipeline": "ingestion",
                "stage": "indexer_trigger",
                "indexer": AZURE_SEARCH_INDEXER_NAME,
                "duration_ms": duration_ms,
            },
        )
        return {
            "triggered": True,
            "message": f"Indexer '{AZURE_SEARCH_INDEXER_NAME}' started successfully",
            "status": "running",
        }
    except HttpResponseError as e:
        if e.status_code == 409:
            logger.warning(
                f"indexer: {AZURE_SEARCH_INDEXER_NAME} | status: conflict_already_running",
                extra={"pipeline": "ingestion", "stage": "indexer_trigger", "indexer": AZURE_SEARCH_INDEXER_NAME},
            )
            return {
                "triggered": False,
                "message": "Indexer is already running",
                "status": "inProgress",
            }
        logger.error(
            f"indexer: {AZURE_SEARCH_INDEXER_NAME} | status: trigger_failed",
            extra={"pipeline": "ingestion", "stage": "indexer_trigger", "indexer": AZURE_SEARCH_INDEXER_NAME},
            exc_info=True,
        )
        raise


def get_indexer_status() -> dict:
    client = get_indexer_client()

    try:
        status = client.get_indexer_status(AZURE_SEARCH_INDEXER_NAME)
    except ResourceNotFoundError:
        logger.error(
            f"indexer: {AZURE_SEARCH_INDEXER_NAME} | status: not_found",
            extra={"pipeline": "ingestion", "stage": "indexer_status", "indexer": AZURE_SEARCH_INDEXER_NAME},
        )
        raise ValueError(f"Indexer '{AZURE_SEARCH_INDEXER_NAME}' not found")

    last = status.last_result
    errors = [e.error_message for e in (last.errors or [])][:5] if last else []

    if last and last.failed_item_count:
        logger.warning(
            f"indexer: {AZURE_SEARCH_INDEXER_NAME} | status: {last.status} | "
            f"processed: {last.item_count} | failed: {last.failed_item_count}",
            extra={
                "pipeline": "ingestion",
                "stage": "indexer_status",
                "indexer": AZURE_SEARCH_INDEXER_NAME,
                "items_failed": last.failed_item_count,
                "items_processed": last.item_count,
            },
        )
    else:
        logger.info(
            f"indexer: {AZURE_SEARCH_INDEXER_NAME} | status: {last.status if last else 'never_run'}",
            extra={
                "pipeline": "ingestion",
                "stage": "indexer_status",
                "indexer": AZURE_SEARCH_INDEXER_NAME,
                "status": last.status if last else "never_run",
            },
        )

    return {
        "indexer": AZURE_SEARCH_INDEXER_NAME,
        "status": last.status if last else "never_run",
        "start_time": last.start_time.isoformat() if last and last.start_time else None,
        "end_time": last.end_time.isoformat() if last and last.end_time else None,
        "items_processed": last.item_count if last else 0,
        "items_failed": last.failed_item_count if last else 0,
        "errors": errors,
    }
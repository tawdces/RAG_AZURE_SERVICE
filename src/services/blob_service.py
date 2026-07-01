import logging
import time
from pathlib import Path
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError, HttpResponseError

import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import (
    AZURE_STORAGE_CONNECTION_STRING,
    AZURE_STORAGE_CONTAINER_NAME,
)

PDF_FOLDER = Path("data/pdf")

logger = logging.getLogger("app")


def get_container_client():
    blob_service_client = BlobServiceClient.from_connection_string(
        AZURE_STORAGE_CONNECTION_STRING
    )
    return blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME)


def upload_pdf_files() -> dict:
    logger.info(
        f"ingestion: blob upload started | source: {PDF_FOLDER}",
        extra={"pipeline": "ingestion", "stage": "blob_upload", "source_folder": str(PDF_FOLDER)},
    )
    start = time.time()

    container_client = get_container_client()
    uploaded = []
    skipped = []
    failed = []

    pdf_files = list(PDF_FOLDER.glob("*.pdf"))

    for pdf_file in pdf_files:
        try:
            with open(pdf_file, "rb") as data:
                container_client.upload_blob(
                    name=pdf_file.name,
                    data=data,
                    overwrite=False,
                )
            uploaded.append(pdf_file.name)
            logger.info(
                f"file: {pdf_file.name} | status: uploaded",
                extra={"pipeline": "ingestion", "stage": "blob_upload", "file": pdf_file.name, "status": "uploaded"},
            )
        except ResourceExistsError:
            skipped.append(pdf_file.name)
            logger.info(
                f"file: {pdf_file.name} | status: skipped_already_exists",
                extra={"pipeline": "ingestion", "stage": "blob_upload", "file": pdf_file.name, "status": "skipped"},
            )
        except HttpResponseError:
            failed.append(pdf_file.name)
            logger.error(
                f"file: {pdf_file.name} | status: failed",
                extra={"pipeline": "ingestion", "stage": "blob_upload", "file": pdf_file.name, "status": "failed"},
                exc_info=True,
            )

    duration_ms = round((time.time() - start) * 1000, 2)
    logger.info(
        f"ingestion summary | found: {len(pdf_files)} | uploaded: {len(uploaded)} | "
        f"skipped: {len(skipped)} | failed: {len(failed)} | duration: {duration_ms}ms",
        extra={
            "pipeline": "ingestion",
            "stage": "blob_upload",
            "total_found": len(pdf_files),
            "uploaded_count": len(uploaded),
            "skipped_count": len(skipped),
            "failed_count": len(failed),
            "duration_ms": duration_ms,
        },
    )

    return {
        "uploaded": uploaded,
        "total": len(uploaded),
    }
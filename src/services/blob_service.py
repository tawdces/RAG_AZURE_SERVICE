from pathlib import Path
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError

import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import (
    AZURE_STORAGE_CONNECTION_STRING,
    AZURE_STORAGE_CONTAINER_NAME,
)

PDF_FOLDER = Path("data/pdf")


def get_container_client():
    blob_service_client = BlobServiceClient.from_connection_string(
        AZURE_STORAGE_CONNECTION_STRING
    )
    return blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME)


def upload_pdf_files() -> dict:
    container_client = get_container_client()
    uploaded = []

    for pdf_file in PDF_FOLDER.glob("*.pdf"):
        try:
            with open(pdf_file, "rb") as data:
                container_client.upload_blob(
                    name=pdf_file.name,
                    data=data,
                    overwrite=False,
                )
            uploaded.append(pdf_file.name)
        except ResourceExistsError:
            pass

    return {
        "uploaded": uploaded,
        "total": len(uploaded),
    }
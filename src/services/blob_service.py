from pathlib import Path
from azure.storage.blob import BlobServiceClient

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


def upload_pdf_files() -> list[str]:
    container_client = get_container_client()
    uploaded = []

    for pdf_file in PDF_FOLDER.glob("*.pdf"):
        with open(pdf_file, "rb") as data:
            container_client.upload_blob(
                name=pdf_file.name,
                data=data,
                overwrite=True,
            )
        uploaded.append(pdf_file.name)

    return uploaded
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from fastapi import APIRouter
from pydantic import BaseModel

from src.services.blob_service import upload_pdf_files

router = APIRouter(prefix="/blob", tags=["Blob Storage"])


class UploadResponse(BaseModel):
    uploaded: list[str]
    total: int


@router.post("/upload", response_model=UploadResponse)
def upload():
    return upload_pdf_files()
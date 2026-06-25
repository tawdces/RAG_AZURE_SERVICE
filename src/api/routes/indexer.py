import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.core.exceptions import HttpResponseError

from src.services.indexer_service import trigger_indexer, get_indexer_status

router = APIRouter(prefix="/indexer", tags=["Indexer"])


class TriggerIndexResponse(BaseModel):
    triggered: bool
    message: str
    status: str


class IndexStatusResponse(BaseModel):
    indexer: str
    status: str
    start_time: str | None
    end_time: str | None
    items_processed: int
    items_failed: int
    errors: list[str]


@router.post("/run", response_model=TriggerIndexResponse)
def trigger_index():
    try:
        return trigger_indexer()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HttpResponseError as e:
        raise HTTPException(status_code=502, detail=f"Azure error: {e.message}")


@router.get("/status", response_model=IndexStatusResponse)
def index_status():
    try:
        return get_indexer_status()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.services.search_service import search

router = APIRouter(prefix="/search", tags=["Search"])


class SearchRequest(BaseModel):
    query: str
    top: int = 5


class SearchResult(BaseModel):
    score: float | None
    title: str | None
    chunk: str | None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


@router.post("/query", response_model=SearchResponse)
def query(body: SearchRequest):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty")

    results = search(body.query, top=body.top)

    return SearchResponse(
        query=body.query,
        results=[SearchResult(**r) for r in results],
    )
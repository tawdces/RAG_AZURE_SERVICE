import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.services.knowledge_service import retrieve_answer

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    answer: str


@router.post("/ask", response_model=QueryResponse)
def ask(body: QueryRequest):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty")

    answer = retrieve_answer(body.query)

    return QueryResponse(query=body.query, answer=answer)
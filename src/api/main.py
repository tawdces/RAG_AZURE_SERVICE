from fastapi import FastAPI

from src.core.logging_config import setup_logging
from src.api.middleware.request_logging import RequestLoggingMiddleware
from src.api.routes import knowledge, search, blob, indexer

# ต้องเรียกก่อนสร้าง app เพื่อให้ instrument ครอบคลุมทุกอย่าง (requests, httpx, etc.)
logger = setup_logging()

app = FastAPI(
    title="RAG Azure Service",
    description="REST API for Azure AI Search & Knowledge Base",
    version="1.0.0",
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(knowledge.router)
app.include_router(search.router)
app.include_router(blob.router)
app.include_router(indexer.router)


@app.get("/health")
def health():
    logger.info("Health check called")
    return {"status": "ok"}
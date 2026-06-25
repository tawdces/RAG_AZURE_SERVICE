from fastapi import FastAPI
from src.api.routes import knowledge, search, blob, indexer

app = FastAPI(
    title="RAG Azure Service",
    description="REST API for Azure AI Search & Knowledge Base",
    version="1.0.0",
)

app.include_router(knowledge.router)
app.include_router(search.router)
app.include_router(blob.router)
app.include_router(indexer.router)


@app.get("/health")
def health():
    return {"status": "ok"}
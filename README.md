# RAG Azure Service

End-to-end Retrieval-Augmented Generation (RAG) implementation using Azure-managed services. Both the ingestion pipeline and query pipeline are fully managed by Azure, minimizing custom code and simplifying maintenance.

---

## Architecture

```
User Request
     │
     ▼
FastAPI Backend (POST /knowledge/ask)
     │
     ▼
Azure AI Content Safety ── Input Guardrails (Jailbreak · Hate · Violence)
     │
     ▼
Azure AI Search Knowledge Base (answerSynthesis)
     │
     ├── Vector + Semantic Retrieval ──► Search Index
     │                                      (chunk · title · text_vector)
     └── Retrieved Context
               │
               ▼
         GPT-4.1-mini
               │
               ▼
Azure AI Content Safety ── Output Guardrails (Toxicity · Protected Material)
               │
               ▼
         Response to User
```

### Ingestion Pipeline (Azure Managed)

```
PDF Files (data/pdf/)
     │
     ▼ scripts/upload_blob.py
Azure Blob Storage
     │
     ▼ trigger
Azure AI Search Indexer
     │
     ▼
Skillset
  ├── 1. Document Intelligence  (PDF → Markdown)
  ├── 2. Split Skill            (2000 chars / 500 overlap)
  └── 3. Embedding Skill        (text-embedding-3-small → 1536-dim vector)
     │
     ▼ index projection
Azure AI Search Index
```

---

## Project Structure

```
rag_azure_service/
├── main.py                    # Entry point — uvicorn
├── .env.example               # Environment variable template
├── Dockerfile                 # Container build
├── requirements.txt
├── pytest.ini
├── run_tests.sh / run_tests.bat
│
├── .github/workflows/
│   ├── ci.yml                 # Test · Lint · Security scan
│   └── docker-build.yml       # Build & push → ghcr.io
│
├── scripts/                   # Developer tools (run directly)
│   ├── upload_blob.py         # Upload PDFs to Blob Storage
│   ├── search_chat.py         # Interactive search test
│   ├── knowledge_chat.py      # Interactive knowledge base test
│   └── search_index.py        # Index inspection
│
├── src/
│   ├── config.py              # Environment config via load_dotenv()
│   ├── api/
│   │   ├── main.py            # FastAPI app
│   │   └── routes/
│   │       ├── blob.py        # POST /blob/upload
│   │       ├── indexer.py     # POST /indexer/run · GET /indexer/status
│   │       ├── search.py      # POST /search/query
│   │       └── knowledge.py   # POST /knowledge/ask
│   └── services/
│       ├── blob_service.py    # BlobServiceClient
│       ├── indexer_service.py # SearchIndexerClient
│       ├── search_service.py  # SearchClient
│       └── knowledge_service.py # KnowledgeBaseRetrievalClient
│
├── data/pdf/                  # PDF source documents
└── tests/
    ├── conftest.py
    ├── test_api.py
    └── test_config.py
```

---

## Prerequisites

- Python 3.14+
- Docker (optional)
- Azure subscription with the following services provisioned:
  - Azure Blob Storage
  - Azure AI Search (with Indexer, Skillset, and Knowledge Base configured)
  - Azure OpenAI (GPT-4.1-mini + text-embedding-3-small deployments)
  - Azure AI Services (Cognitive Services key for Skillset auth)
  - Azure AI Content Safety

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values.

```env
# Azure AI Project
PROJECT_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
PROJECT_API_KEY=<your-key>

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=<your-connection-string>
AZURE_STORAGE_CONTAINER_NAME=<your-container-name>

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://<your-search>.search.windows.net
AZURE_SEARCH_INDEX_NAME=<your-index-name>
AZURE_SEARCH_INDEXER_NAME=<your-indexer-name>
AZURE_SEARCH_API_KEY=<your-search-api-key>

# Knowledge Base
KNOWLEDGE_BASE_NAME=<your-knowledge-base-name>
KNOWLEDGE_SOURCE_NAME=<your-knowledge-source-name>
```

---

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Upload documents to Blob Storage

```bash
python scripts/upload_blob.py
```

Place PDF files in `data/pdf/` before running. The script uploads all PDFs to the configured Blob container and triggers the Azure AI Search Indexer automatically.

### 3. Run the API

```bash
python main.py
```

API will be available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

### 4. Run with Docker

```bash
docker build -t rag-azure-service .
docker run -p 8000:8000 --env-file .env rag-azure-service
```

Or pull the latest image from GitHub Container Registry:

```bash
docker pull ghcr.io/tawdces/rag_azure_service:latest
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/blob/upload` | Upload PDFs from `data/pdf/` to Blob Storage |
| `POST` | `/indexer/run` | Trigger Azure AI Search Indexer |
| `GET` | `/indexer/status` | Get current Indexer status |
| `POST` | `/search/query` | Search the index directly |
| `POST` | `/knowledge/ask` | Ask a question via Knowledge Base (RAG) |

### Example — Ask a question

```bash
curl -X POST http://localhost:8000/knowledge/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is FI e-App?"}'
```

Response:

```json
{
  "query": "What is FI e-App?",
  "answer": "FI e-App is ..."
}
```

### Example — Search the index

```bash
curl -X POST http://localhost:8000/search/query \
  -H "Content-Type: application/json" \
  -d '{"query": "e-App workflow", "top": 5}'
```

---

## Developer Scripts

For quick testing without going through the API:

```bash
# Test search directly against the index
python scripts/search_chat.py

# Test knowledge base retrieval interactively
python scripts/knowledge_chat.py

# Inspect index contents
python scripts/search_index.py
```

---

## Running Tests

```bash
# Linux / macOS
bash run_tests.sh

# Windows
run_tests.bat

# Manual
pytest tests/ -v --cov=src --cov-report=html
```

Coverage report will be available at `htmlcov/index.html`.

---

## CI/CD

### ci.yml — runs on push/PR to `main` and `develop`

| Step | Tool |
|------|------|
| Lint | pylint (threshold 7.0) · black |
| Test | pytest + coverage → Codecov |
| Security | bandit |

### docker-build.yml — runs on push to `main`

Builds multi-platform image (`linux/amd64`, `linux/arm64`) and pushes to GitHub Container Registry:

```
ghcr.io/tawdces/rag_azure_service:latest
ghcr.io/tawdces/rag_azure_service:<commit-sha>
```

> **Note:** Docker image is built and pushed but not yet deployed to a hosting environment.

---

## Guardrails

Azure AI Content Safety is applied at two points in the query pipeline:

**Input Guardrails** (before sending to Knowledge Base)
- Jailbreak detection — Block
- Hate / Self-harm / Sexual / Violence — Medium threshold — Block

**Output Guardrails** (after GPT-4.1-mini generates a response)
- Hate / Self-harm / Sexual / Violence — Medium threshold — Block
- Protected material for code — Annotate
- Protected material for text — Block

---

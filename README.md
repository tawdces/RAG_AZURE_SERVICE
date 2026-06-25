# RAG Azure Service

REST API สำหรับ Azure AI Search และ Knowledge Base ด้วย FastAPI

---

## โครงสร้างโปรเจกต์

```
rag_azure_service/
├── .env
├── .env.example
├── requirements.txt
├── main.py                        ← entry point
│
├── data/
│   └── pdf/                       ← วาง PDF ไฟล์ที่นี่
│
├── src/
│   ├── config.py
│   ├── api/
│   │   ├── main.py                ← FastAPI app
│   │   └── routes/
│   │       ├── knowledge.py
│   │       ├── search.py
│   │       ├── blob.py
│   │       └── indexer.py
│   │
│   └── services/
│       ├── knowledge_service.py
│       ├── search_service.py
│       ├── blob_service.py
│       └── indexer_service.py
│
└── test/
    ├── test_index.py
    ├── test_knowledge.py
    ├── test_search.py
    └── test_blob.py
```

---

## Requirements

- Python 3.10+
- Azure Blob Storage
- Azure AI Search
- Azure OpenAI (text-embedding-3-small)
- Azure AI Services

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Configuration

คัดลอก `.env.example` แล้วสร้าง `.env` และกรอกค่าให้ครบ

```bash
cp .env.example .env
```

```env
PROJECT_ENDPOINT=
PROJECT_API_KEY=

AZURE_STORAGE_CONTAINER_NAME=
AZURE_STORAGE_CONNECTION_STRING=

AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_INDEX_NAME=
AZURE_SEARCH_INDEXER_NAME=
AZURE_SEARCH_API_KEY=

KNOWLEDGE_BASE_NAME=
KNOWLEDGE_SOURCE_NAME=
```

---

## Run

```bash
python main.py
```

เปิด Swagger UI ได้ที่ `http://localhost:8000/docs`

---

## API Endpoints

### Health Check

```
GET /health
```

```json
{ "status": "ok" }
```

---

### Knowledge Base — Answer Synthesis

```
POST /knowledge/ask
```

Request

```json
{
  "query": "คำถามของคุณ"
}
```

Response

```json
{
  "query": "คำถามของคุณ",
  "answer": "คำตอบจาก Knowledge Base"
}
```

---

### Search — Keyword Search

```
POST /search/query
```

Request

```json
{
  "query": "คำค้นหา",
  "top": 5
}
```

Response

```json
{
  "query": "คำค้นหา",
  "results": [
    {
      "score": 0.98,
      "title": "ชื่อเอกสาร",
      "chunk": "เนื้อหาที่เกี่ยวข้อง..."
    }
  ]
}
```

---

### Blob Storage — Upload PDF

```
POST /blob/upload
```

Response

```json
{
  "uploaded": ["file1.pdf", "file2.pdf"],
  "total": 2
}
```

> วาง PDF ไว้ใน `data/pdf/` ก่อนเรียก endpoint นี้
> ไฟล์ที่มีอยู่แล้วใน Blob จะถูกข้ามโดยอัตโนมัติ

---

### Indexer — Trigger & Status

```
POST /indexer/run
```

Response

```json
{
  "triggered": true,
  "message": "Indexer 'jame-rag-indexer' started successfully",
  "status": "running"
}
```

```
GET /indexer/status
```

Response

```json
{
  "indexer": "jame-rag-indexer",
  "status": "success",
  "start_time": "2025-01-01T10:00:00",
  "end_time": "2025-01-01T10:05:00",
  "items_processed": 3,
  "items_failed": 0,
  "errors": []
}
```

---

## Upload Flow

วาง PDF ใหม่ใน `data/pdf/` แล้วเรียก API ตามลำดับ

```
1. POST /blob/upload        → อัพโหลด PDF ไปยัง Blob Storage
2. POST /indexer/run        → trigger indexer ให้ประมวลผล file ใหม่
3. GET  /indexer/status     → poll จนกว่า status = "success"
4. POST /knowledge/ask      → query ได้เลย
```

---

## Test Scripts

รันทดสอบแต่ละ service ได้โดยตรง

```bash
# ทดสอบ Knowledge Base
python test/test_knowledge.py

# ทดสอบ Keyword Search
python test/test_search.py

# ทดสอบ Index
python test/test_index.py

# ทดสอบ Blob Upload
python test/test_blob.py
```

---

## Azure Skillset Pipeline

| ขั้นตอน | Skill                              | หน้าที่                                  |
| ------- | ---------------------------------- | ---------------------------------------- |
| 1       | Document Intelligence Layout Skill | แปลง PDF → Markdown                      |
| 2       | Split Skill                        | ตัดเป็น chunks (2000 chars, 500 overlap) |
| 3       | Azure OpenAI Embedding Skill       | สร้าง vector 1536 มิติ                   |
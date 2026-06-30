import re
from typing import cast, Any
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.search.documents.knowledgebases.models import (
    KnowledgeBaseMessage,
    KnowledgeBaseMessageTextContent,
    KnowledgeBaseRetrievalRequest,
    SearchIndexKnowledgeSourceParams,
)
from azure.core.credentials import AzureKeyCredential

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_API_KEY,
    KNOWLEDGE_BASE_NAME,
    KNOWLEDGE_SOURCE_NAME,
)


def get_kb_client() -> KnowledgeBaseRetrievalClient:
    return KnowledgeBaseRetrievalClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        knowledge_base_name=KNOWLEDGE_BASE_NAME,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )


_PAGE_PATTERN = re.compile(r"_pages_(\d+)\s*$")


def _extract_sources(result: Any) -> list[dict]:
    sources: list[dict] = []
    references = getattr(result, "references", None) or []

    for ref in references:
        ref_dict = ref.as_dict() if hasattr(ref, "as_dict") else (vars(ref) if hasattr(ref, "__dict__") else {})

        file_name = ref_dict.get("title")
        doc_key = ref_dict.get("docKey") or ref_dict.get("doc_key") or ""
        reranker_score = ref_dict.get("rerankerScore") or ref_dict.get("reranker_score")

        page = None
        match = _PAGE_PATTERN.search(doc_key)
        if match:
            page = int(match.group(1)) + 1

        sources.append(
            {
                "file": file_name,
                "page": page,
                "reranker_score": reranker_score,
            }
        )

    deduped: dict[tuple, dict] = {}
    for s in sources:
        key = (s["file"], s["page"])
        if key not in deduped or (s["reranker_score"] or 0) > (deduped[key]["reranker_score"] or 0):
            deduped[key] = s

    return sorted(deduped.values(), key=lambda s: s["reranker_score"] or 0, reverse=True)


_REF_ID_PATTERN = re.compile(r"\s*\[ref_id:\d+\]")


def _strip_ref_ids(text: str) -> str:
    return _REF_ID_PATTERN.sub("", text).strip()


def _format_reference_block(sources: list[dict]) -> str:
    if not sources:
        return ""

    lines = ["", "", "อ้างอิง:"]
    for s in sources:
        file_name = s.get("file") or "ไม่ทราบไฟล์"
        page = s.get("page")
        score = s.get("reranker_score")
        score_str = f"{score:.4f}" if isinstance(score, (int, float)) else "N/A"
        lines.append(f"[file: {file_name}, page: {page}, rerank_score: {score_str}]")

    return "\n".join(lines)


def retrieve_answer(query: str) -> dict:
    client = get_kb_client()

    request = KnowledgeBaseRetrievalRequest(
        messages=[
            KnowledgeBaseMessage(
                role="user",
                content=[KnowledgeBaseMessageTextContent(text=query)],
            )
        ],
        knowledge_source_params=[
            SearchIndexKnowledgeSourceParams(
                knowledge_source_name=KNOWLEDGE_SOURCE_NAME
            )
        ],
        output_mode="answerSynthesis",
    )

    result = client.retrieve(retrieval_request=request)

    content = cast(
        KnowledgeBaseMessageTextContent,
        result.response[0].content[0],
    )

    sources = _extract_sources(result)
    clean_answer = _strip_ref_ids(content.text)
    final_answer = clean_answer + _format_reference_block(sources)

    return {
        "answer": final_answer,
    }
import json
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

# Set to True to print subquery/activity debug info to stdout
DEBUG_PRINT_SUBQUERIES = True


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

    lines = ["", "อ้างอิง:"]
    for i, s in enumerate(sources, 1):
        file_name = s.get("file") or "ไม่ทราบไฟล์"
        page = s.get("page")
        page_str = f"หน้า {page}" if page is not None else "หน้า -"
        score = s.get("reranker_score")
        score_str = f"{score:.2f}" if isinstance(score, (int, float)) else "N/A"
        lines.append(f"  {i}. {file_name} ({page_str}) · score {score_str}")

    return "\n".join(lines)


def _to_dict(obj: Any) -> Any:
    """Best-effort conversion of SDK model objects to plain dict/list for printing."""
    if hasattr(obj, "as_dict"):
        return obj.as_dict()
    if hasattr(obj, "__dict__"):
        return {k: _to_dict(v) for k, v in vars(obj).items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [_to_dict(i) for i in obj]
    return obj


def _dump_raw_result(result: Any) -> None:
    """Dump the entire result object structure - use this first to discover real field names."""
    print("\n========== RAW RESULT DUMP ==========")
    try:
        print(json.dumps(_to_dict(result), indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        print(f"(failed to json-serialize, falling back to repr) {e}")
        print(repr(_to_dict(result)))
    print("======================================\n")


def _print_subqueries(result: Any) -> None:
    """
    Print a clean, condensed view of the query plan: subqueries actually
    sent to the search index, plus a one-line cost/timing summary for the
    planning and synthesis model calls.
    """
    activities = getattr(result, "activity", None) or []
    if not activities:
        print("(no activity found - try _dump_raw_result(result))")
        return

    subqueries: list[str] = []
    planning = None
    synthesis = None
    reasoning_tokens = None

    for act in activities:
        a = _to_dict(act)
        t = a.get("type")

        if t == "searchIndex":
            search_text = (a.get("searchIndexArguments") or {}).get("search")
            if search_text:
                subqueries.append(f"{search_text}  ({a.get('count', '?')} results)")
        elif t == "modelQueryPlanning":
            planning = a
        elif t == "modelAnswerSynthesis":
            synthesis = a
        elif t == "agenticReasoning":
            reasoning_tokens = a.get("reasoningTokens")

    print("\n=== Subqueries sent to search index ===")
    for i, sq in enumerate(subqueries, 1):
        print(f"  {i}. {sq}")

    print("\n=== Model cost summary ===")
    if planning:
        print(f"  Planning : {planning.get('inputTokens')} in / {planning.get('outputTokens')} out "
              f"tokens, {planning.get('elapsedMs')}ms ({planning.get('modelName')})")
    if synthesis:
        print(f"  Synthesis: {synthesis.get('inputTokens')} in / {synthesis.get('outputTokens')} out "
              f"tokens, {synthesis.get('elapsedMs')}ms ({synthesis.get('modelName')})")
    if reasoning_tokens is not None:
        print(f"  Reasoning: {reasoning_tokens} tokens")
    print("========================================\n")


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

    if DEBUG_PRINT_SUBQUERIES:
        _print_subqueries(result)

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
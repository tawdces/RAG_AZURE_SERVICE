from typing import cast
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


def retrieve_answer(query: str) -> str:
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

    return content.text
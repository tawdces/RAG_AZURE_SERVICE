from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX_NAME, AZURE_SEARCH_API_KEY


def test_index():
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )

    print("====================")
    print("Testing Azure AI Search")
    print("Index: ", AZURE_SEARCH_INDEX_NAME)
    print("====================")

    result = search_client.search(
        search_text="*",
        include_total_count=True,
        top=5,
    )

    total = result.get_count()

    print(f"\nTotal chunks: {total}")

    if total == 0:
        print("\nIndex is empty")
        return

    print("\n========== Documents ==========")

    for i, doc in enumerate(result, start=1):
        print(f"\n----- Result {i} -----")

        for key, value in doc.items():
            key = str(key)
            if "vector" not in key.lower():
                print(f"{key}: {value}")


if __name__ == "__main__":
    test_index()
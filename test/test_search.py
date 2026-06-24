import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.services.search_service import search


def run():
    while True:
        query = input("\nEnter query (exit to quit): ")

        if query.lower() == "exit":
            break

        if not query.strip():
            continue

        results = search(query)

        print("\n====================")
        print(f"Query: {query}")
        print("====================")

        if not results:
            print("No results found")
            continue

        for i, result in enumerate(results, start=1):
            print(f"\n===== Result {i} =====")
            print("Score:", result["score"])
            print("Title:", result["title"])
            print("\nChunk:")
            print(result["chunk"])


if __name__ == "__main__":
    run()
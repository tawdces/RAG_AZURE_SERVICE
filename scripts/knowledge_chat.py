import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.services.knowledge_service import retrieve_answer


def run():
    while True:
        query = input("\nEnter query (exit to quit): ")

        if query.lower() == "exit":
            break

        if not query.strip():
            continue

        result = retrieve_answer(query)

        print("\n====================")
        print("Answer")
        print("====================")
        print(result["answer"])


if __name__ == "__main__":
    run()
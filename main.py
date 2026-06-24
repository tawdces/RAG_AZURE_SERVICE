import uvicorn

if __name__ == "__main__":
    print("\n====================")
    print("RAG Azure Service")
    print("====================")
    print("Docs: http://localhost:8000/docs")
    print("====================\n")

    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
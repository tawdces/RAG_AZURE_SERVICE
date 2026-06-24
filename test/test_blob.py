import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.services.blob_service import upload_pdf_files


def run():
    print("====================")
    print("Uploading PDF files")
    print("====================")

    uploaded = upload_pdf_files()

    if not uploaded:
        print("No PDF files found in data/pdf/")
        return

    for filename in uploaded:
        print(f"Uploaded: {filename}")

    print(f"\nTotal: {len(uploaded)} file(s)")


if __name__ == "__main__":
    run()
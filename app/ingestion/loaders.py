from pathlib import Path
import pymupdf


def load_pdf(file_path: str) -> list[dict]:
    """
    Extract text from a PDF page by page.
    """

    document = pymupdf.open(file_path)

    pages = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text("text")

        if not text.strip():
            continue

        pages.append({
            "text": text,
            "metadata": {
                "source": Path(file_path).name,
                "page": page_number,
                "document_type": "pdf",
            }
        })

    document.close()

    return pages
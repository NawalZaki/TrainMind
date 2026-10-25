import pymupdf

from app.ingestion.loaders import load_pdf
from app.ingestion.chunker import chunk_documents


def test_load_pdf_and_chunk_documents(tmp_path):
    # Create a temporary PDF for testing
    pdf_path = tmp_path / "test.pdf"

    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Retrieval-Augmented Generation helps AI retrieve relevant information."
    )
    doc.save(str(pdf_path))
    doc.close()

    # Test PDF loading
    pages = load_pdf(str(pdf_path))

    assert len(pages) == 1
    assert "Retrieval-Augmented Generation" in pages[0]["text"]

    # Test chunking
    chunks = chunk_documents(pages)

    assert len(chunks) >= 1
    assert "Retrieval-Augmented Generation" in chunks[0]["text"]
    assert "metadata" in chunks[0]

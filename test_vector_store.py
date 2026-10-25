from unittest.mock import patch

from app.rag.vector_store import add_chunks


@patch("app.rag.vector_store.collection")
def test_add_chunks_stores_documents(mock_collection):
    chunks = [
        {
            "text": "RAG retrieves relevant information.",
            "metadata": {
                "source": "test_curriculum.pdf",
                "page": 1,
                "document_type": "pdf",
            },
        }
    ]

    embeddings = [[0.1, 0.2, 0.3]]

    add_chunks(chunks, embeddings)

    mock_collection.delete.assert_called_once_with(
        where={"source": "test_curriculum.pdf"}
    )

    mock_collection.add.assert_called_once()

    stored_data = mock_collection.add.call_args.kwargs

    assert stored_data["documents"] == [
        "RAG retrieves relevant information."
    ]
    assert stored_data["metadatas"][0]["source"] == "test_curriculum.pdf"
    assert stored_data["metadatas"][0]["page"] == 1
    assert len(stored_data["embeddings"]) == 1
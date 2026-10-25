from unittest.mock import patch

from app.rag.vector_store import (
    add_chunks,
    delete_indexed_source,
    list_indexed_source_details,
)


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


@patch("app.rag.vector_store.collection")
def test_list_indexed_source_details_counts_pages_and_chunks(mock_collection):
    mock_collection.get.return_value = {
        "metadatas": [
            {"source": "z_curriculum.pdf", "page": 1},
            {"source": "z_curriculum.pdf", "page": 1},
            {"source": "z_curriculum.pdf", "page": 2},
            {"source": "a_curriculum.pdf", "page": 4},
        ]
    }

    assert list_indexed_source_details() == [
        {"source": "a_curriculum.pdf", "pages": 1, "chunks": 1},
        {"source": "z_curriculum.pdf", "pages": 2, "chunks": 3},
    ]


@patch("app.rag.vector_store.collection")
def test_delete_indexed_source_removes_all_source_chunks(mock_collection):
    delete_indexed_source("test_curriculum.pdf")

    mock_collection.delete.assert_called_once_with(
        where={"source": "test_curriculum.pdf"}
    )
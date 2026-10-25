from unittest.mock import patch

from app.rag.retriever import search_curriculum


@patch("app.rag.retriever.create_embedding")
@patch("app.rag.retriever.collection.query")
def test_search_curriculum_without_gemini(mock_query, mock_embedding):
    mock_embedding.return_value = [0.1, 0.2, 0.3]

    mock_query.return_value = {
        "documents": [[
            "RAG retrieves relevant curriculum information before generation."
        ]],
        "metadatas": [[{
            "source": "RAG_Practical_Guide.pdf",
            "page": 1,
        }]],
        "distances": [[0.3]],
    }

    results = search_curriculum("What is RAG?")

    assert len(results) == 1
    assert results[0]["metadata"]["source"] == "RAG_Practical_Guide.pdf"
    assert results[0]["metadata"]["page"] == 1
    mock_embedding.assert_called_once_with("What is RAG?")
    mock_query.assert_called_once()
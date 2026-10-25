
from unittest.mock import patch

from app.rag.answer import answer_question


@patch("app.rag.answer.generate_answer")
@patch("app.rag.answer.search_curriculum")
def test_rag_answer_uses_retrieved_context(
    mock_search,
    mock_generate,
):
    mock_search.return_value = [
        {
            "text": (
                "Retrieval-Augmented Generation (RAG) "
                "retrieves relevant information before generating an answer."
            ),
            "metadata": {
                "source": "test.pdf",
                "page": 1,
            },
            "distance": 0.2,
        }
    ]

    mock_generate.return_value = (
        "RAG retrieves relevant information before generating an answer."
    )

    result = answer_question("What is RAG?")

    assert "RAG" in result["answer"]
    mock_search.assert_called_once()
    mock_generate.assert_called_once()

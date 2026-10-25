
from unittest.mock import patch

from app.tools import generate_quiz_tool


@patch("app.tools.generate_answer")
@patch("app.tools.search_curriculum")
def test_generate_quiz_uses_curriculum_context(
    mock_search,
    mock_generate,
):
    mock_search.return_value = [
        {
            "text": "RAG retrieves relevant information before generating an answer.",
            "metadata": {
                "source": "test.pdf",
                "page": 1,
            },
            "distance": 0.2,
        }
    ]

    mock_generate.return_value = (
        "1. What does RAG do?\n"
        "A. Retrieves relevant information\n"
        "B. Deletes information\n"
        "C. Changes hardware\n"
        "D. None of the above\n"
        "Answer: A"
    )

    result = generate_quiz_tool(
        topic="RAG",
        number_of_questions=1,
    )

    assert "What does RAG do?" in result
    mock_search.assert_called_once()
    mock_generate.assert_called_once()

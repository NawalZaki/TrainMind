from unittest.mock import patch

from app.agent.graph import graph


@patch("app.agent.graph.generate_quiz_tool")
def test_agent_can_generate_quiz_without_gemini(mock_quiz):
    mock_quiz.return_value = "Quiz about RAG"

    result = graph.invoke({
        "query": "Generate a quiz about RAG",
        "intent": "quiz",
        "results": [],
        "answer": "",
        "sources": [],
        "validation": {},
        "revision_count": 0,
    })

    assert result["answer"] == "Quiz about RAG"
    mock_quiz.assert_called_once()

from unittest.mock import patch

from app.agent.graph import graph


@patch("app.agent.graph.generate_answer")
@patch("app.agent.graph.search_curriculum_tool")
def test_agent_answers_rag_question(mock_search, mock_generate):
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
        "RAG retrieves relevant information before generating an answer."
    )

    result = graph.invoke({
        "query": "What is RAG?",
        "intent": "",
        "results": [],
        "answer": "",
        "sources": [],
        "validation": {},
        "revision_count": 0,
    })

    assert "RAG" in result["answer"]
    assert len(result["sources"]) > 0
    mock_search.assert_called_once()
    mock_generate.assert_called_once()
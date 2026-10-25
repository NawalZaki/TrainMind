
from unittest.mock import patch

from app.agent.graph import graph
from app.agent import graph as graph_module


def test_agent_graph_compiles():
    assert graph is not None


@patch("app.agent.graph.generate_quiz_tool")
def test_agent_routes_quiz_request(mock_quiz):
    mock_quiz.return_value = "Mock quiz about RAG"

    result = graph.invoke({
        "query": "Generate a quiz about RAG",
        "intent": "quiz",
        "results": [],
        "answer": "",
        "sources": [],
        "validation": {},
        "revision_count": 0,
    })

    assert result["intent"] == "quiz"
    assert result["answer"] == "Mock quiz about RAG"
    mock_quiz.assert_called_once()

@patch("app.agent.graph.generate_exercise_tool")
def test_agent_routes_exercise_request(mock_exercise):
    mock_exercise.return_value = "Mock exercise about RAG"

    result = graph.invoke({
        "query": "Create a beginner exercise about RAG",
        "intent": "exercise",
        "results": [],
        "answer": "",
        "sources": [],
        "validation": {},
        "revision_count": 0,
    })

    assert result["intent"] == "exercise"
    assert result["answer"] == "Mock exercise about RAG"
    mock_exercise.assert_called_once()


@patch("app.agent.graph.generate_answer")
@patch("app.agent.graph.generate_session_plan_tool")
def test_agent_routes_session_plan_request(
    mock_session_plan,
    mock_generate_answer,
):
    mock_session_plan.return_value = """
        ## Learning Objectives

        Understand RAG.

        ## Introduction

        Introduction to RAG.

        ## Concept Explanation

        Explain the basic RAG concept.

        ## Practical Activity

        Identify the main steps of the RAG process.

        ## Exercise

        Answer questions about the RAG concept.

        ## Quick Quiz

        Answer a few questions about RAG.

        ## Assessment

        Explain the main concept in your own words.

        ## Expected Learning Outcome

        The trainee understands the basic RAG concept.

        0-10 min: Introduction
        10-25 min: Concept Explanation
        25-50 min: Practical Activity
        50-65 min: Exercise
        65-75 min: Quick Quiz
        75-90 min: Assessment
        """
    mock_generate_answer.return_value = "Mock revised session plan"

    result = graph.invoke({
        "query": "Create a 90-minute session plan about RAG",
        "intent": "session_plan",
        "results": [],
        "answer": "",
        "sources": [],
        "validation": {},
        "revision_count": 0,
    })

    assert result["intent"] in ["session", "session_plan"]
    assert "Learning Objectives" in result["answer"]
    assert "Introduction" in result["answer"]
    assert "Concept Explanation" in result["answer"]
    assert "Practical Activity" in result["answer"]
    assert "Exercise" in result["answer"]
    assert "Quick Quiz" in result["answer"]
    assert "Assessment" in result["answer"]
    assert "Expected Learning Outcome" in result["answer"]

    assert "0-10 min" in result["answer"]
    assert "10-25 min" in result["answer"]
    assert "25-50 min" in result["answer"]
    assert "50-65 min" in result["answer"]
    assert "65-75 min" in result["answer"]
    assert "75-90 min" in result["answer"]
    mock_session_plan.assert_called_once()

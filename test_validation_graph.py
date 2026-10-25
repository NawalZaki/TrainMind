
from app.agent.graph import validate_node, should_revise


def test_validation_node_accepts_complete_plan():
    answer = """
    Learning Objectives
    Introduction
    Concept Explanation
    Practical Activity
    Exercise
    Quick Quiz
    Assessment
    Expected Learning Outcome
    """

    result = validate_node({"answer": answer})

    assert result["validation"]["valid"] is True
    assert result["validation"]["missing_sections"] == []


def test_invalid_plan_requests_revision():
    state = {
        "validation": {
            "valid": False,
            "missing_sections": ["Assessment"],
        },
        "revision_count": 0,
    }

    assert should_revise(state) == "revise"

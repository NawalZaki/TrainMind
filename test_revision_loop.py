
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

from app.agent.graph import should_revise


class AgentTestState(TypedDict):
    answer: str
    validation: dict
    revision_count: int


def fake_validate(state: AgentTestState):
    # Simulate an invalid plan on the first pass,
    # then a valid plan after revision.
    if state["revision_count"] == 0:
        return {
            "validation": {
                "valid": False,
                "missing_sections": ["Assessment"],
            }
        }

    return {
        "validation": {
            "valid": True,
            "missing_sections": [],
        }
    }


def fake_revise(state: AgentTestState):
    return {
        "answer": state["answer"] + "\nAssessment",
        "revision_count": state["revision_count"] + 1,
    }


builder = StateGraph(AgentTestState)

builder.add_node("validate", fake_validate)
builder.add_node("revise", fake_revise)

builder.add_edge(START, "validate")

builder.add_conditional_edges(
    "validate",
    should_revise,
    {
        "done": END,
        "revise": "revise",
    },
)

builder.add_edge("revise", "validate")

test_graph = builder.compile()


def test_graph_revises_then_finishes():
    result = test_graph.invoke(
        {
            "answer": "Learning Objectives\nExercise",
            "validation": {},
            "revision_count": 0,
        }
    )

    assert result["revision_count"] == 1
    assert result["validation"]["valid"] is True
    assert "Assessment" in result["answer"]

def test_graph_stops_after_max_revisions():
    def always_invalid(state: AgentTestState):
        return {
            "validation": {
                "valid": False,
                "missing_sections": ["Assessment"],
            }
        }

    builder = StateGraph(AgentTestState)
    builder.add_node("validate", always_invalid)
    builder.add_node("revise", fake_revise)

    builder.add_edge(START, "validate")
    builder.add_conditional_edges(
        "validate",
        should_revise,
        {
            "done": END,
            "revise": "revise",
        },
    )
    builder.add_edge("revise", "validate")

    limited_graph = builder.compile()

    result = limited_graph.invoke(
        {
            "answer": "Learning Objectives\nExercise",
            "validation": {},
            "revision_count": 0,
        }
    )

    assert result["revision_count"] == 2
    assert result["validation"]["valid"] is False

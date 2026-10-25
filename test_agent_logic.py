
from app.agent.graph import should_revise
from app.tools import validate_output


def test_valid_plan_should_finish():
    state = {
        "validation": {"valid": True, "missing_sections": []},
        "revision_count": 0,
    }

    assert should_revise(state) == "done"


def test_invalid_plan_should_be_revised():
    state = {
        "validation": {
            "valid": False,
            "missing_sections": ["Exercise"],
        },
        "revision_count": 0,
    }

    assert should_revise(state) == "revise"


def test_max_revisions_should_finish():
    state = {
        "validation": {
            "valid": False,
            "missing_sections": ["Exercise"],
        },
        "revision_count": 2,
    }

    assert should_revise(state) == "done"


def test_validate_output_with_all_sections():
    output = """
    Learning Objectives
    Exercise
    Quick Quiz
    Assessment
    """

    result = validate_output(
        output,
        ["Learning Objectives", "Exercise", "Quick Quiz", "Assessment"],
    )

    assert result["valid"] is True
    assert result["missing_sections"] == []


def test_validate_output_with_missing_section():
    output = "Learning Objectives\nExercise"

    result = validate_output(
        output,
        ["Learning Objectives", "Exercise", "Assessment"],
    )

    assert result["valid"] is False
    assert result["missing_sections"] == ["Assessment"]

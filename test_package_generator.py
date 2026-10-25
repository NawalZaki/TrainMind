import json

import pytest

from app import package_generator as package_module


def _fake_model_package():
    package = {}
    activities = [
        "Introduction",
        "Concept Explanation",
        "Practical Activity",
        "Exercise",
        "Quick Quiz",
        "Assessment",
    ]
    for level in ("beginner", "intermediate", "advanced"):
        package[level] = {
            "quiz": [
                {
                    "question": f"Question {number} for {level}?",
                    "options": ["A. One", "B. Two", "C. Three", "D. Four"],
                    "correct_answer": "A",
                    "explanation": "Supported by the source.",
                    "evidence": "sample.pdf page 1",
                }
                for number in range(1, 6)
            ],
            "exercise": {
                "title": f"{level.title()} exercise",
                "estimated_time": "20 minutes",
                "prerequisites": [],
                "objective": "Explain the source workflow.",
                "task": "Use only the provided curriculum.",
                "steps": ["Read the source", "Describe the workflow"],
                "expected_outcome": "A source-grounded explanation.",
                "hints": ["Use the uploaded material."],
                "common_mistakes": ["Adding unsupported details."],
                "assessment_criteria": ["Accuracy to source."],
                "support_note": "Limited to source evidence.",
                "sources": [],
            },
            "session_plan": {
                "learning_objectives": ["Explain the concept", "Identify the workflow"],
                "segments": [
                    {
                        "activity": activity,
                        "trainer_actions": "Explain the supported content.",
                        "learner_actions": "Respond using the source.",
                        "materials": "Uploaded curriculum PDF",
                    }
                    for activity in activities
                ],
                "expected_learning_outcome": "Explain the workflow accurately.",
                "support_note": "Use source-supported activities only.",
                "sources": [],
            },
        }
    return package


def test_generate_training_package_creates_all_nine_artifacts(monkeypatch):
    monkeypatch.setattr(
        package_module,
        "search_curriculum",
        lambda *args, **kwargs: [
            {
                "text": "The curriculum describes a RAG workflow.",
                "metadata": {"source": "sample.pdf", "page": 1},
                "distance": 0.2,
            }
        ],
    )
    monkeypatch.setattr(package_module, "generate_json", lambda prompt: json.dumps(_fake_model_package()))

    result = package_module.generate_training_package("RAG")

    assert set(result["levels"]) == {"beginner", "intermediate", "advanced"}
    for level in result["levels"].values():
        assert set(("quiz", "exercise", "session_plan")).issubset(level)
        assert level["timing_validation"]["valid"] is True
        assert level["timing_validation"]["total_minutes"] == 90
        assert "sample.pdf, page 1" in level["quiz"]


def test_generate_training_package_fails_when_no_curriculum_matches(monkeypatch):
    monkeypatch.setattr(package_module, "search_curriculum", lambda *args, **kwargs: [])
    with pytest.raises(ValueError, match="No sufficiently relevant curriculum passages"):
        package_module.generate_training_package("topic absent from the curriculum")

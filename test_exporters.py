from app.exporters import build_exports


def test_exporters_create_pdf_powerpoint_and_word():
    package = {"topic": "RAG", "levels": {}}
    for level in ("beginner", "intermediate", "advanced"):
        package["levels"][level] = {
            "quiz": "## Quiz\nA sample question.",
            "exercise": "## Exercise\nA sample task.",
            "session_plan": "## 90-Minute Session Schedule\n0-10 min: Introduction",
            "timing_validation": {"valid": True, "total_minutes": 90},
        }

    files = build_exports(package)

    assert files["pdf"].startswith(b"%PDF")
    assert files["pptx"].startswith(b"PK")
    assert files["docx"].startswith(b"PK")
    assert all(len(content) > 1000 for content in files.values())

"""Generate a complete three-level TrainMind package in one Gemini request."""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from app.rag.generator import generate_json
from app.rag.retriever import search_curriculum

LEVELS = ("beginner", "intermediate", "advanced")
SCHEDULE = [
    (0, 10, "Introduction"),
    (10, 25, "Concept Explanation"),
    (25, 50, "Practical Activity"),
    (50, 65, "Exercise"),
    (65, 75, "Quick Quiz"),
    (75, 90, "Assessment"),
]


def _get_context(topic: str, top_k: int = 7) -> tuple[str, list[dict]]:
    results = search_curriculum(topic, top_k=top_k, distance_threshold=0.9)
    unique_results = []
    seen = set()
    for item in results:
        metadata = item.get("metadata") or {}
        text = (item.get("text") or "").strip()
        key = (metadata.get("source"), metadata.get("page"), text)
        if text and key not in seen:
            seen.add(key)
            unique_results.append(item)

    if not unique_results:
        return "", []

    context_parts = []
    for item in unique_results:
        metadata = item.get("metadata") or {}
        context_parts.append(
            f"SOURCE: {metadata.get('source', 'Unknown source')} | "
            f"PAGE: {metadata.get('page', 'Unknown')}\n{item['text']}"
        )
    # Keep one request reasonably small, especially for Free Tier usage.
    return "\n\n--- CURRICULUM EXCERPT ---\n\n".join(context_parts)[:12000], unique_results


def _prompt(topic: str, context: str, level: str) -> str:
    return f'''You are TrainMind, an ITI Trainer Copilot. Create a complete training package for the topic below.

TOPIC: {topic}
LEARNER LEVEL: {level}

NON-NEGOTIABLE SOURCE RULES
- Use ONLY the curriculum evidence supplied below. No outside knowledge.
- Do not invent facts, tools, prerequisites, commands, code, procedures, or technologies.
- If evidence is insufficient for a specific task, state this explicitly in that artifact and provide a source-supported alternative.
- Match the cognitive demand to the requested level while using the SAME supported concepts, not adding new content.
- Beginner: identify, define, explain, or sequence concepts explicitly in the source.
- Intermediate: connect concepts, apply the described workflow, or reason about source-described failure modes when supported.
- Advanced: evaluate trade-offs, diagnose source-described failures, or justify decisions only when supported. If the evidence does not support an advanced task, explain the limitation rather than inventing one.
- Do not claim a level is supported just because it is common in training.
- Include source/page references where possible.

RETURN ONE VALID JSON OBJECT ONLY, with no Markdown fences. It must have exactly one top-level key: "{level}". That level must contain these three keys: "quiz", "exercise", and "session_plan".

Each quiz is an array of question objects. Every question object must contain:
- question: string
- options: array of exactly four strings, labelled A, B, C, D
- correct_answer: one letter, A, B, C, or D
- explanation: string
- evidence: short source-grounded evidence, without inventing page numbers

Each exercise is an object containing:
- title, estimated_time, objective, task, expected_outcome, support_note: strings
- prerequisites, steps, hints, common_mistakes, assessment_criteria: arrays of strings

Each session_plan is an object containing:
- learning_objectives: array of strings
- segments: array of exactly six objects. Each object contains activity, trainer_actions, learner_actions, and materials as strings.
- expected_learning_outcome and support_note: strings

The application attaches the actual retrieved source filenames and page numbers after generation. Do not fabricate source metadata.

Detailed output requirements:
- Provide exactly 5 quiz questions, each with exactly 4 options and a correct_answer of A, B, C, or D. Distractors must not introduce unsupported factual claims as if true.
- Exercise fields must all be present. If no prerequisites are explicitly stated in the source, use an empty list.
- The session plan must have 2-4 measurable learning objectives, and exactly six segments with the activity names in this exact order: Introduction, Concept Explanation, Practical Activity, Exercise, Quick Quiz, Assessment.
- Session plans are exactly 90 minutes. The application will assign these exact times, so do not add alternative timings: 0-10, 10-25, 25-50, 50-65, 65-75, 75-90.
- The segments should have enough detail to guide the trainer, but must remain grounded in the source.
- Return valid JSON, with no trailing comments.

CURRICULUM EVIDENCE:
{context}
'''


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Gemini package response is missing '{field}'. Please generate again.")
    return value.strip()


def _render_quiz(questions: list[dict]) -> str:
    if not isinstance(questions, list) or len(questions) != 5:
        raise ValueError("Each level's quiz must contain exactly five questions. Please generate again.")
    if any(not isinstance(question, dict) for question in questions):
        raise ValueError("The generated quiz contains an invalid question object.")
    rendered = ["## Quiz"]
    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            continue
        rendered.append(f"### Question {index}\n{_require_string(question.get('question'), 'quiz question')}")
        options = question.get("options")
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError(f"Quiz question {index} must have exactly four answer choices.")
        rendered.extend(str(option) for option in options)
        answer = _require_string(question.get("correct_answer"), "quiz correct answer").upper()
        if answer not in {"A", "B", "C", "D"}:
            raise ValueError(f"Quiz question {index} has an invalid correct_answer.")
        rendered.append(f"**Correct answer:** {answer}")
        explanation = question.get("explanation", "")
        if explanation:
            rendered.append(f"**Explanation:** {explanation}")
        evidence = question.get("evidence", "")
        if evidence:
            rendered.append(f"**Curriculum evidence:** {evidence}")
    return "\n\n".join(rendered)


def _render_exercise(exercise: dict) -> str:
    if not isinstance(exercise, dict):
        raise ValueError("The generated exercise is not a valid object.")
    fields = [
        ("Exercise Title", "title"),
        ("Estimated Time", "estimated_time"),
        ("Prerequisites", "prerequisites"),
        ("Objective", "objective"),
        ("Task", "task"),
        ("Steps", "steps"),
        ("Expected Outcome", "expected_outcome"),
        ("Hints", "hints"),
        ("Common Mistakes", "common_mistakes"),
        ("Assessment Criteria", "assessment_criteria"),
        ("Curriculum Support Note", "support_note"),
    ]
    lines = []
    for heading, key in fields:
        value = exercise.get(key, [] if key in {"prerequisites", "steps", "hints", "common_mistakes", "assessment_criteria", "sources"} else "")
        lines.append(f"## {heading}")
        if isinstance(value, list):
            lines.extend(f"- {item}" for item in value if str(item).strip())
            if not any(str(item).strip() for item in value):
                lines.append("- Not specified in the provided curriculum.")
        else:
            lines.append(str(value).strip() or "Not sufficiently specified by the provided curriculum.")
    return "\n\n".join(lines)


def _render_session_plan(plan: dict) -> str:
    if not isinstance(plan, dict):
        raise ValueError("The generated session plan is not a valid object.")
    objectives = plan.get("learning_objectives")
    segments = plan.get("segments")
    if not isinstance(objectives, list) or not 2 <= len(objectives) <= 4:
        raise ValueError("Each session plan must contain two to four learning objectives.")
    if not isinstance(segments, list) or len(segments) != 6:
        raise ValueError("The session plan must contain exactly six timed segments.")

    by_activity = {}
    for segment in segments:
        if isinstance(segment, dict) and segment.get("activity"):
            by_activity[str(segment["activity"]).strip().casefold()] = segment

    lines = ["## Learning Objectives"]
    lines.extend(f"- {objective}" for objective in objectives)
    lines.append("\n## 90-Minute Session Schedule")

    for start, end, activity in SCHEDULE:
        segment = by_activity.get(activity.casefold())
        if not segment:
            raise ValueError(f"The session plan is missing the '{activity}' segment.")
        lines.append(f"\n### {start}-{end} min: {activity}")
        lines.append(f"**Trainer actions:** {_require_string(segment.get('trainer_actions'), f'{activity} trainer actions')}")
        lines.append(f"**Learner actions:** {_require_string(segment.get('learner_actions'), f'{activity} learner actions')}")
        materials = segment.get("materials", "")
        if materials:
            lines.append(f"**Materials from curriculum:** {materials}")

    lines.append("\n## Expected Learning Outcome")
    lines.append(_require_string(plan.get("expected_learning_outcome"), "expected learning outcome"))
    lines.append("\n## Curriculum Support Note")
    lines.append(str(plan.get("support_note", "Not specified.")).strip() or "Not specified.")
    sources = plan.get("sources", [])
    return "\n\n".join(lines)


def _parse_json(raw: str) -> dict:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0:
            raise ValueError("Gemini did not return a valid JSON package. Please try again.")
        if end <= start:
            raise ValueError(
                "Gemini returned incomplete JSON. The response may have reached its output limit; "
                "try again, or increase GEMINI_MAX_OUTPUT_TOKENS in your .env file."
            )
        try:
            result = json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Gemini returned incomplete JSON. The response may have reached its output limit; "
                "try again, or increase GEMINI_MAX_OUTPUT_TOKENS in your .env file."
            ) from exc
    if not isinstance(result, dict):
        raise ValueError("Gemini returned an invalid package structure.")
    return result


def validate_session_timing(plan_text: str) -> dict:
    """Validate that a rendered plan includes all six exact continuous time ranges."""
    found = [(int(a), int(b)) for a, b in re.findall(r"(\d+)\s*[-–]\s*(\d+)\s*min", plan_text, re.I)]
    expected = [(start, end) for start, end, _ in SCHEDULE]
    return {"valid": found == expected, "expected_intervals": expected, "found_intervals": found, "total_minutes": found[-1][1] if found else 0}


def generate_training_package(
    topic: str,
    progress_callback: Callable[[str], None] | None = None,
) -> dict:
    """Retrieve curriculum evidence once and generate one level per model call."""
    topic = topic.strip()
    if not topic:
        raise ValueError("Enter a topic before generating the package.")

    context, results = _get_context(topic)
    if not results:
        raise ValueError(
            "No sufficiently relevant curriculum passages were found for this topic. "
            "Upload/index the relevant material or try a topic that appears in it."
        )

    rendered_levels = {}

    for level in LEVELS:
        if progress_callback:
            progress_callback(f"Generating {level.title()} Quiz, Exercise, and Session Plan...")
        try:
            raw = generate_json(_prompt(topic, context, level))
            data = _parse_json(raw)
            level_data = data.get(level)
            if not isinstance(level_data, dict):
                raise ValueError(f"Gemini's response is missing the {level} level.")
            quiz = _render_quiz(level_data.get("quiz"))
            exercise = _render_exercise(level_data.get("exercise"))
            session_plan = _render_session_plan(level_data.get("session_plan"))
            timing = validate_session_timing(session_plan)
            if not timing["valid"] or timing["total_minutes"] != 90:
                raise ValueError("the session plan did not pass the 90-minute timing check.")
            rendered_levels[level] = {
                "quiz": quiz,
                "exercise": exercise,
                "session_plan": session_plan,
                "timing_validation": timing,
            }
        except Exception as exc:
            failure = f"{level.title()} level failed: {exc}"
            if progress_callback:
                progress_callback(failure)
            raise RuntimeError(failure) from exc
        if progress_callback:
            progress_callback(f"{level.title()} level complete (3 artifacts).")

    source_records = []
    seen_sources = set()
    for item in results:
        metadata = item.get("metadata") or {}
        record = {"source": metadata.get("source", "Unknown source"), "page": metadata.get("page", "Unknown")}
        key = (record["source"], record["page"])
        if key not in seen_sources:
            seen_sources.add(key)
            source_records.append(record)

    # Source labels are taken from Chroma metadata, never trusted from model-generated text.
    source_lines = "\n".join(f"- {item['source']}, page {item['page']}" for item in source_records)
    for level in rendered_levels:
        for artifact in ("quiz", "exercise", "session_plan"):
            rendered_levels[level][artifact] += "\n\n## Retrieved Curriculum Sources\n" + (source_lines or "- No source metadata available.")

    return {"topic": topic, "levels": rendered_levels, "sources": source_records}

import json
from app.rag.retriever import search_curriculum
from app.rag.generator import generate_answer



def search_curriculum_tool(query: str, top_k: int = 5) -> list[dict]:
    """
    Search the ITI curriculum for relevant information.
    """

    results = search_curriculum(query, top_k=top_k)

    return results


def analyze_curriculum_tool(
    topic: str,
    top_k: int = 5,
) -> dict:
    """
    Analyze curriculum evidence and identify which training
    activities and difficulty levels it supports.
    """

    queries = [
        topic,
        f"{topic} core concepts definitions",
        f"{topic} practical lab activities steps",
        f"{topic} limitations problems troubleshooting",
    ]

    results = []
    seen = set()

    for query in queries:
        matches = search_curriculum(query, top_k=top_k)

        for item in matches:
            metadata = item.get("metadata", {})
            text = item.get("text", "")

            key = (
                metadata.get("source"),
                metadata.get("page"),
                text,
            )

            if text and key not in seen:
                seen.add(key)
                results.append(item)

    if not results:
        return {
            "topic": topic,
            "context": "",
            "results": [],
            "analysis": {},
            "error": (
                "The curriculum does not contain enough "
                "information to analyze this topic."
            ),
        }

    context_parts = []

    for item in results:
        metadata = item.get("metadata", {})

        context_parts.append(
            f"Source: {metadata.get('source')}\n"
            f"Page: {metadata.get('page')}\n"
            f"Content:\n{item['text']}"
        )

    context = "\n\n---\n\n".join(context_parts)

   

    prompt = f"""
    You are analyzing actual curriculum evidence for an ITI trainer.

    Topic:
    {topic}

    Curriculum evidence:
    {context}

    Return one valid JSON object with this exact structure:

    {{
    "core_concepts": [],
    "explicit_prerequisites": [],
    "supported_levels": {{
        "beginner": {{
        "supported": true,
        "activities": [],
        "evidence": []
        }},
        "intermediate": {{
        "supported": true,
        "activities": [],
        "evidence": []
        }},
        "advanced": {{
        "supported": true,
        "activities": [],
        "evidence": []
        }}
    }},
    "limitations": []
    }}

    Assessment rules:

    1. Assess each level independently. Do not assume advanced is
    supported just because the topic is technical.

    2. Beginner can be supported by accurate definitions,
    explanations of core concepts, conceptual questions,
    and activities that can be completed using the provided text.

    3. Intermediate can be supported by a guided lab or practical
    workflow when the source provides enough information to
    complete the activity. Mention missing implementation details.

    4. Advanced requires evidence supporting genuinely advanced
    work, such as independent design, substantial troubleshooting,
    or evaluation. A definition alone is not sufficient.

    5. The source describes a mini RAG lab involving PDF extraction,
    chunking, embeddings, ChromaDB, retrieval, grounded generation,
    and source metadata. Consider this evidence when assessing
    practical levels. Do not claim that the source provides code
    or detailed setup instructions unless it actually does.

    6. For every supported level, provide at least one concrete
    activity grounded in the source and evidence referencing
    a source page or a short quotation.

    7. If evidence is insufficient for a level, set supported to
    false and explain the gap in limitations.

    8. Do not invent prerequisites. If none are explicitly stated,
    return an empty list.

    9. Do not return an empty limitations list when the source has
    clear gaps relevant to the requested topic or activities.

    10. Use only the provided evidence. Return JSON only, without
        Markdown fences.
    """


    raw_analysis = generate_answer(
        "Analyze the curriculum and return the requested JSON.",
        context + "\n\nAnalysis instructions:\n" + prompt,
    )

    try:
        start = raw_analysis.find("{")
        end = raw_analysis.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No JSON object found.")

        analysis = json.loads(raw_analysis[start:end + 1])

        if not isinstance(analysis, dict):
            raise ValueError("Analysis must be a JSON object.")

        levels = analysis.get("supported_levels", {})

        for level in ("beginner", "intermediate", "advanced"):
            level_data = levels.get(level)

            if (
                not isinstance(level_data, dict)
                or not isinstance(level_data.get("supported"), bool)
            ):
                raise ValueError(
                    f"Missing valid support assessment for {level}."
                )

    except (ValueError, json.JSONDecodeError):
        analysis = {
            "parse_error": (
                "The model did not return valid curriculum analysis JSON."
            ),
            "raw_analysis": raw_analysis,
            "supported_levels": {},
        }

    return {
        "topic": topic,
        "context": context,
        "results": results,
        "analysis": analysis,
        "error": None,
    }

def generate_quiz_tool(
    topic: str,
    number_of_questions: int = 5,
    difficulty: str = "beginner",
) -> str:
    """
    Generate a quiz based on the ITI curriculum.
    """

    results = search_curriculum(topic, top_k=5)

    if not results:
        return (
            "The curriculum does not contain enough information "
            "to generate a quiz on this topic."
        )

    context_parts = []

    for result in results:
        metadata = result["metadata"]

        context_parts.append(
            f"Source: {metadata.get('source')}\n"
            f"Page: {metadata.get('page')}\n"
            f"Content:\n{result['text']}"
        )

    context = "\n\n---\n\n".join(context_parts)

    difficulty = difficulty.lower().strip()
    if difficulty not in {"beginner", "intermediate", "advanced"}:
        difficulty = "beginner"

    prompt = f"""
Create a quiz for an ITI trainer.

Topic:
{topic}

Difficulty:
{difficulty}

Number of questions:
{number_of_questions}

Difficulty guidance:
- Beginner: check understanding of definitions and explicit facts.
- Intermediate: connect concepts or apply a process explicitly described in the source.
- Advanced: analyze or evaluate source-supported concepts and failure modes. If the source does not support an advanced question, state the limitation rather than using outside knowledge.
- Do not introduce concepts outside the provided curriculum at any level.

Use ONLY the provided curriculum context.

STRICT CONTENT RULES:
- Every question must be supported by the curriculum context.
- Do not invent facts.
- Do not introduce technologies, libraries, models, tools,
  algorithms, or terminology that are not explicitly supported
  by the curriculum context.
- Do not use outside knowledge.
- If the context does not contain enough information for a question,
  do not create that question.

For each question:
- Write the question clearly.
- Provide 4 answer choices.
- Mark the correct answer.
- Keep the questions aligned with the provided curriculum.

Curriculum context:
{context}
"""

    return generate_answer(
        "Generate a quiz.",
        prompt,
    )


def generate_exercise_tool(
    topic: str,
    difficulty: str = "beginner",
) -> str:
    """
    Generate a practical exercise based on the ITI curriculum.
    """

    results = search_curriculum(topic, top_k=5)

    if not results:
        return (
            "The curriculum does not contain enough information "
            "to generate an exercise on this topic."
        )

    context_parts = []

    for result in results:
        metadata = result["metadata"]

        context_parts.append(
            f"Source: {metadata.get('source')}\n"
            f"Page: {metadata.get('page')}\n"
            f"Content:\n{result['text']}"
        )

    context = "\n\n---\n\n".join(context_parts)

    difficulty = difficulty.lower().strip()

    if difficulty not in {"beginner", "intermediate", "advanced"}:
        difficulty = "beginner"

    prompt = f"""
Create a practical training exercise for an ITI trainee.

Topic:
{topic}

Difficulty:
{difficulty}

IMPORTANT: The exercise must be grounded ONLY in the curriculum context
provided below.

STRICT CURRICULUM RULES:
1. Do not invent facts.
2. Do not introduce technologies, libraries, frameworks, models, tools,
   algorithms, datasets, programming languages, or implementation
   techniques that are not explicitly supported by the curriculum context.
3. Do not assume prerequisites that are not supported by the curriculum.
4. Do not ask the trainee to build a complete system unless the curriculum
   explicitly describes that activity.
5. Do not use outside knowledge to make the exercise more technical.
6. If the curriculum only provides conceptual information, create a
   conceptual or lightweight practical exercise rather than inventing
   a software implementation.
7. Use the terminology and concepts from the curriculum context.

DIFFICULTY RULES:

Beginner:
- Focus on understanding the main concepts.
- Use simple application or identification tasks.
- Give clear step-by-step instructions.
- Keep prerequisites minimal.
- Do not require building a complete system.
- Avoid advanced troubleshooting.
- Prefer activities such as identifying concepts, explaining steps,
  comparing ideas from the curriculum, or applying a concept to
  a simple provided example.

Intermediate:
- Require the trainee to combine concepts from the curriculum.
- Give less detailed instructions than Beginner.
- Include a small problem-solving or decision-making task.
- Ask the trainee to explain or justify their result.
- Do not introduce concepts outside the curriculum.

Advanced:
- Require independent reasoning using the curriculum concepts.
- Include a realistic problem, constraint, edge case, or decision.
- Ask the trainee to analyze the situation and justify their solution.
- The challenge must still be completely grounded in the curriculum.

The difficulty must change the complexity of the task,
not simply change the wording.

STRUCTURE THE EXERCISE EXACTLY AS:

## Exercise Title

## Difficulty

## Estimated Time

## Prerequisites

## Objective

## Task

## Steps

## Expected Outcome

## Hints

## Common Mistakes

## Assessment Criteria

QUALITY CHECK BEFORE ANSWERING:

Before producing the exercise, verify:
- Every required section is present.
- The exercise is appropriate for the selected difficulty.
- All important concepts come from the curriculum context.
- No unsupported technology or library has been introduced.
- The trainee is not asked to perform an activity that requires
  knowledge outside the curriculum.
- Beginner is substantially simpler than Intermediate and Advanced.

Curriculum context:
{context}
"""

    return generate_answer(
        "Create a practical exercise.",
        prompt,
    )


def generate_session_plan_tool(
    topic: str,
    duration: int = 90,
    difficulty: str = "beginner",
) -> str:
    """
    Generate a practical training session plan based on the ITI curriculum.
    """

    results = search_curriculum(topic, top_k=5)

    if not results:
        return (
            "The curriculum does not contain enough information "
            "to generate a session plan."
        )

    context_parts = []

    for result in results:
        metadata = result["metadata"]

        context_parts.append(
            f"Source: {metadata.get('source')}\n"
            f"Page: {metadata.get('page')}\n"
            f"Content:\n{result['text']}"
        )

    context = "\n\n---\n\n".join(context_parts)

    difficulty = difficulty.lower().strip()

    if difficulty not in {"beginner", "intermediate", "advanced"}:
        difficulty = "beginner"

    prompt = f"""
Create a practical ITI training session plan.

Topic:
{topic}

Session duration:
{duration} minutes

Trainee level:
{difficulty}

IMPORTANT:
The session plan must be based ONLY on the curriculum context below.

STRICT CURRICULUM RULES:

1. Do not invent facts.
2. Do not introduce technologies, libraries, frameworks, models,
   tools, algorithms, or terminology that are not supported by
   the curriculum context.
3. Do not use outside knowledge.
4. Do not introduce implementation requirements simply because
   they are common in real-world RAG systems.
5. If the curriculum is conceptual, keep the activities conceptual
   or lightweight.
6. Use the terminology and concepts that actually appear in the
   curriculum context.

DIFFICULTY RULES:

BEGINNER:
- Focus on understanding the core concepts.
- Use guided activities.
- Use simple identification, explanation, comparison, or application tasks.
- Give clear step-by-step instructions.
- Minimize prerequisites.
- Do NOT ask trainees to build a complete RAG system.
- Do NOT require coding unless coding is explicitly supported by
  the curriculum context.
- Do NOT introduce extra libraries or technologies.

INTERMEDIATE:
- Require trainees to combine multiple concepts from the curriculum.
- Include a guided practical or problem-solving activity.
- Give less detailed instructions than Beginner.
- Ask trainees to explain or justify their decisions.
- Do not introduce concepts outside the curriculum.

ADVANCED:
- Require independent reasoning.
- Include a realistic problem, constraint, edge case, or decision
  supported by the curriculum.
- Ask trainees to analyze and justify their solution.
- The task can be more open-ended, but must remain within the
  curriculum content.

The difficulty must change the actual activity,
not just the wording.

SESSION STRUCTURE:

1. Learning Objectives
2. Introduction
3. Concept Explanation
4. Practical Activity
5. Exercise
6. Quick Quiz
7. Assessment
8. Expected Learning Outcome

TIMING REQUIREMENT:

The session must cover exactly {duration} minutes.

There must be:
- No gaps.
- No overlapping activities.
- No time before minute 0.
- No time after minute {duration}.

For a 90-minute session, use exactly:

0–10 min: Introduction
10–25 min: Concept Explanation
25–50 min: Practical Activity
50–65 min: Exercise
65–75 min: Quick Quiz
75–90 min: Assessment

Do not change these ranges when the session duration is 90 minutes.

For every activity, clearly show its time range.

QUALITY CHECK:

Before producing the final answer, verify:

- The session duration is exactly {duration} minutes.
- All required sections are present.
- The activities match the selected difficulty.
- Beginner is simpler than Intermediate.
- Intermediate is simpler than Advanced.
- No unsupported technology or library has been introduced.
- No outside knowledge has been added.
- The practical activity can actually be completed at the
  selected trainee level.
- The session does not require building a complete system unless
  the curriculum explicitly supports that activity.

Curriculum context:
{context}
"""

    return generate_answer(
        "Create a training session plan.",
        prompt,
    )

def validate_output(
    output: str,
    required_sections: list[str],
) -> dict:
    """
    Validate that a generated output contains the required sections.
    """

    missing_sections = []

    for section in required_sections:
        if section.lower() not in output.lower():
            missing_sections.append(section)

    if missing_sections:
        return {
            "valid": False,
            "missing_sections": missing_sections,
        }

    return {
        "valid": True,
        "missing_sections": [],
    }


def validate_session_plan(
    output: str,
    duration: int = 90,
    difficulty: str = "beginner",
) -> dict:
    """
    Validate the structure, timing, and difficulty level
    of a training session plan.
    """

    required_sections = [
        "Learning Objectives",
        "Introduction",
        "Concept Explanation",
        "Practical Activity",
        "Exercise",
        "Quick Quiz",
        "Assessment",
        "Expected Learning Outcome",
    ]

    validation = validate_output(
        output,
        required_sections,
    )

    if not validation["valid"]:
        return validation

    import re

    time_pattern = re.compile(
        r"(\d+)\s*[–-]\s*(\d+)\s*min",
        re.IGNORECASE,
    )

    matches = time_pattern.findall(output)

    if not matches:
        return {
            "valid": False,
            "missing_sections": [],
            "timing_error": "No timed activities were found.",
        }

    intervals = [
        (int(start), int(end))
        for start, end in matches
    ]

    unique_intervals = []

    for interval in intervals:
        if interval not in unique_intervals:
            unique_intervals.append(interval)

    intervals = unique_intervals

    if duration == 90:
        expected_intervals = [
            (0, 10),
            (10, 25),
            (25, 50),
            (50, 65),
            (65, 75),
            (75, 90),
        ]

        if intervals[:6] != expected_intervals:
            return {
                "valid": False,
                "missing_sections": [],
                "timing_error": (
                    "Session timing is incorrect. "
                    "Expected continuous timing from 0 to 90 minutes."
                ),
            }

    else:
        if intervals[0][0] != 0:
            return {
                "valid": False,
                "missing_sections": [],
                "timing_error": (
                    "The session does not start at minute 0."
                ),
            }

        if intervals[-1][1] != duration:
            return {
                "valid": False,
                "missing_sections": [],
                "timing_error": (
                    f"The session does not end at minute {duration}."
                ),
            }

        for previous, current in zip(intervals, intervals[1:]):
            if previous[1] != current[0]:
                return {
                    "valid": False,
                    "missing_sections": [],
                    "timing_error": (
                        "There is a gap or overlap between "
                        "session activities."
                    ),
                }

    difficulty = difficulty.lower().strip()

    if difficulty == "beginner":
     beginner_red_flags = [
        "build a complete rag",
        "build a full rag",
        "build a rag pipeline",
        "build and test a rag pipeline",
        "build a minimal rag pipeline",
        "create a rag pipeline",
        "creating their own rag pipeline",
        "create your own rag pipeline",
        "implement a rag pipeline",
        "implement the retrieval system",
        "create embeddings",
        "generate embeddings",
        "embedding",
        "sentence transformers",
        "sentencetransformers",
        "chromadb",
        "vector database",
        "configure a vector database",
        "set up a vector database",
        "normal llm prompting",
        "traditional llm prompting",
     ]

     output_lower = output.lower()

     detected_flags = [
            phrase
            for phrase in beginner_red_flags
            if phrase in output_lower
        ]

     if detected_flags:
            return {
                "valid": False,
                "missing_sections": [],
                "timing_error": None,
                "difficulty_error": (
                    "Beginner session contains advanced or "
                    "unsupported requirements: "
                    + ", ".join(detected_flags)
                ),
            }
        
    return {
        "valid": True,
        "missing_sections": [],
        "timing_error": None,
        "difficulty_error": None,
    }

def validate_and_decide(
    output: str,
    required_sections: list[str],
) -> dict:
    """
    Validate an output and decide whether it passes.
    """

    validation = validate_output(
        output,
        required_sections,
    )

    if validation["valid"]:
        return {
            "status": "pass",
            "missing_sections": [],
        }

    return {
        "status": "fail",
        "missing_sections": validation["missing_sections"],
    }
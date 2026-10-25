from typing import TypedDict

from langgraph.graph import StateGraph, START, END


from app.tools import (
    search_curriculum_tool,
    generate_quiz_tool,
    generate_exercise_tool,
    generate_session_plan_tool,
    validate_session_plan,
)

from app.rag.generator import generate_answer


MAX_REVISIONS = 2


class AgentState(TypedDict, total=False):
    query: str
    intent: str
    difficulty: str
    results: list
    answer: str
    sources: list
    validation: dict
    revision_count: int


def router_node(state: AgentState):
    intent = state.get("intent", "").lower()

    if intent == "quiz":
        return {"intent": "quiz"}

    if intent == "exercise":
        return {"intent": "exercise"}

    if intent in ["session", "session_plan"]:
        return {"intent": "session_plan"}

    return {"intent": "answer"}


def search_node(state: AgentState):
    result = search_curriculum_tool(state["query"])

    sources = []
    seen = set()

    for item in result:
        metadata = item.get("metadata", {})

        source = metadata.get("source")
        page = metadata.get("page")

        key = (source, page)

        if key not in seen:
            seen.add(key)
            sources.append({
                "source": source,
                "page": page,
            })

    return {
        "results": result,
        "sources": sources,
    }

def quiz_node(state: AgentState):
    result = generate_quiz_tool(
        state["query"],
        difficulty=state.get("difficulty", "beginner"),
    )

    return {
        "answer": result,
        "intent": "quiz",
    }


def exercise_node(state: AgentState):
    result = generate_exercise_tool(
        state["query"],
        difficulty=state.get("difficulty", "beginner"),
    )
    return {"answer": result, "intent": "exercise"}


def session_node(state: AgentState):
    result = generate_session_plan_tool(
        state["query"],
        difficulty=state.get("difficulty", "beginner"),
    )
    return {
        "answer": result,
        "intent": "session_plan",
    }


def validate_node(state: AgentState):
    result = validate_session_plan(
        state.get("answer", ""),
        difficulty=state.get("difficulty", "beginner"),
    )
    return {"validation": result}

def should_revise(state: AgentState):
    validation = state.get("validation", {})
    revision_count = state.get("revision_count", 0)

    if validation.get("valid", False):
        return "done"

    if revision_count >= MAX_REVISIONS:
        return "done"

    return "revise"


def revise_node(state: AgentState):
    revision_count = state.get("revision_count", 0)
    intent = state.get("intent", "answer")

    if intent == "session_plan":
        revised_answer = generate_session_plan_tool(
            state["query"],
            difficulty=state.get("difficulty", "beginner"),
        )

    elif intent == "exercise":
        revised_answer = generate_exercise_tool(
            state["query"],
            difficulty=state.get("difficulty", "beginner"),
        )

    elif intent == "quiz":
        revised_answer = generate_quiz_tool(
            state["query"],
            difficulty=state.get("difficulty", "beginner"),
        )

    else:
        revised_answer = generate_answer(
            state["query"],
            state.get("answer", ""),
        )

    return {
        "answer": revised_answer,
        "revision_count": revision_count + 1,
    }


def should_route(state: AgentState):
    intent = state.get("intent", "answer")

    if intent == "quiz":
        return "quiz"

    if intent == "exercise":
        return "exercise"

    if intent in ["session", "session_plan"]:
        return "session"

    return "answer"


def generate_node(state: AgentState):
    results = state.get("results", [])

    if isinstance(results, list):
        context_parts = []

        for result in results:
            if isinstance(result, dict):
                text = result.get("text", "")
                if text:
                    context_parts.append(text)
            elif isinstance(result, str):
                context_parts.append(result)

        context = "\n\n".join(context_parts)
    else:
        context = str(results)

    answer = generate_answer(
        state["query"],
        context,
    )

    return {
        "answer": answer,
    }


def refuse_node(state: AgentState):
    return {
        "answer": (
            "The curriculum does not provide enough information "
            "to answer this question."
        )
    }


graph_builder = StateGraph(AgentState)

graph_builder.add_node("router", router_node)
graph_builder.add_node("search", search_node)
graph_builder.add_node("quiz", quiz_node)
graph_builder.add_node("exercise", exercise_node)
graph_builder.add_node("session", session_node)
graph_builder.add_node("validate", validate_node)
graph_builder.add_node("revise", revise_node)
graph_builder.add_node("generate", generate_node)
graph_builder.add_node("refuse", refuse_node)

graph_builder.add_edge(START, "router")

graph_builder.add_conditional_edges(
    "router",
    should_route,
    {
        "answer": "search",
        "quiz": "quiz",
        "exercise": "exercise",
        "session": "session",
    },
)

graph_builder.add_edge("search", "generate")
graph_builder.add_edge("generate", END)

graph_builder.add_edge("quiz", END)
graph_builder.add_edge("exercise", END)

graph_builder.add_edge("session", "validate")

graph_builder.add_conditional_edges(
    "validate",
    should_revise,
    {
        "revise": "revise",
        "done": END,
    },
)

graph_builder.add_edge("revise", "validate")

graph = graph_builder.compile()
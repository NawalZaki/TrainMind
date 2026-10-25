
from app.rag.retriever import search_curriculum
from app.rag.generator import generate_answer


def answer_question(query: str, top_k: int = 3) -> dict:
    """
    Retrieve relevant curriculum chunks, generate an answer,
    and return source references.
    """

    results = search_curriculum(query, top_k=top_k)

    if not results:
        return {
            "answer": (
                "The available curriculum does not contain "
                "enough information to answer this question."
            ),
            "sources": [],
        }

    context_parts = []
    sources = []
    seen_sources = set()

    for result in results:
        metadata = result["metadata"]
        source = metadata.get("source", "Unknown source")
        page = metadata.get("page")

        context_parts.append(
            f"Source: {source}\n"
            f"Page: {page}\n"
            f"Content:\n{result['text']}"
        )

        source_key = (source, page)

        if source_key not in seen_sources:
            sources.append({
                "source": source,
                "page": page,
            })
            seen_sources.add(source_key)

    context = "\n\n---\n\n".join(context_parts)

    answer = generate_answer(query, context)

    return {
        "answer": answer,
        "sources": sources,
    }

from app.rag.embeddings import create_embedding
from app.rag.vector_store import collection


def search_curriculum(
    query: str,
    top_k: int = 5,
    distance_threshold: float = 0.85,
) -> list[dict]:
    """Retrieve semantically similar curriculum chunks from ChromaDB."""
    query_embedding = create_embedding(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]
    matches = []

    for document, metadata, distance in zip(documents, metadatas, distances):
        if document and metadata and distance <= distance_threshold:
            matches.append({"text": document, "metadata": metadata, "distance": distance})
    return matches

"""Local Ollama embeddings used to index and retrieve curriculum chunks."""

import ollama

EMBEDDING_MODEL = "nomic-embed-text"


def _embedding_error(exc: Exception) -> RuntimeError:
    return RuntimeError(
        "TrainMind could not create local embeddings. Make sure Ollama is running "
        "and run `ollama pull nomic-embed-text` in PowerShell."
    )


def create_embedding(text: str) -> list[float]:
    """Convert one text into a local embedding vector."""
    try:
        response = ollama.embed(model=EMBEDDING_MODEL, input=text)
        return response["embeddings"][0]
    except Exception as exc:
        raise _embedding_error(exc) from exc


def create_embeddings(texts: list[str]) -> list[list[float]]:
    """Convert multiple texts into local embedding vectors in one Ollama call."""
    if not texts:
        return []
    try:
        response = ollama.embed(model=EMBEDDING_MODEL, input=texts)
        return response["embeddings"]
    except Exception as exc:
        raise _embedding_error(exc) from exc

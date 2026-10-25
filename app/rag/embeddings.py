"""Gemini embeddings used to index and retrieve curriculum chunks."""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from google import genai

load_dotenv()

EMBEDDING_MODEL = "gemini-embedding-001"


@lru_cache(maxsize=1)
def _get_client(api_key: str):
    return genai.Client(api_key=api_key)


def _client():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to the project's .env file."
        )

    return _get_client(api_key)


def create_embedding(text: str) -> list[float]:
    """Convert one text into a Gemini embedding vector."""
    try:
        response = _client().models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )
        return response.embeddings[0].values

    except Exception as exc:
        raise RuntimeError(
            f"Gemini embedding failed: {exc}"
        ) from exc


def create_embeddings(texts: list[str]) -> list[list[float]]:
    """Convert multiple texts into Gemini embedding vectors."""
    if not texts:
        return []

    try:
        response = _client().models.embed_content(
            model=EMBEDDING_MODEL,
            contents=texts,
        )
        return [embedding.values for embedding in response.embeddings]

    except Exception as exc:
        raise RuntimeError(
            f"Gemini embeddings failed: {exc}"
        ) from exc
"""Persistent ChromaDB storage for curriculum chunks."""

import hashlib
from collections import defaultdict

import chromadb


client = chromadb.PersistentClient(path="data/chroma")
collection = client.get_or_create_collection(
    name="iti_curriculum_local",
    metadata={"hnsw:space": "cosine"},
)


def add_chunks(chunks: list[dict], embeddings: list[list[float]]):
    """Replace existing records for incoming sources and store chunks."""
    if len(chunks) != len(embeddings):
        raise ValueError("The number of chunks must match the number of embeddings.")
    if not chunks:
        return

    ids, documents, metadatas = [], [], []
    sources = set()
    page_counters = defaultdict(int)

    for chunk in chunks:
        metadata = chunk["metadata"].copy()
        source = metadata.get("source")
        if not source:
            raise ValueError("Every chunk must have a 'source' in its metadata.")

        page = metadata.get("page", 0)
        key = (str(source), str(page))
        chunk_index = page_counters[key]
        page_counters[key] += 1
        raw_id = f"{source}|{page}|{chunk_index}"
        chunk_id = "chunk_" + hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:24]

        ids.append(chunk_id)
        documents.append(chunk["text"])
        metadatas.append(metadata)
        sources.add(source)

    for source in sources:
        collection.delete(where={"source": source})

    collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)


def source_is_indexed(source: str, file_hash: str) -> bool:
    """Return True only when every stored chunk for a source matches this file hash."""
    records = collection.get(where={"source": source}, include=["metadatas"])
    metadatas = records.get("metadatas") or []
    return bool(metadatas) and all(meta.get("file_hash") == file_hash for meta in metadatas)


def list_indexed_sources() -> list[str]:
    """List unique source filenames currently represented in ChromaDB."""
    records = collection.get(include=["metadatas"])
    sources = {
        metadata.get("source")
        for metadata in (records.get("metadatas") or [])
        if metadata and metadata.get("source")
    }
    return sorted(sources, key=str.casefold)

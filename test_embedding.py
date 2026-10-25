from app.rag.embeddings import create_embedding


text = """
Retrieval-Augmented Generation (RAG) combines
information retrieval with language generation.
"""

embedding = create_embedding(text)

print("Embedding created successfully!")
print("Vector dimensions:", len(embedding))
print("First 10 values:", embedding[:10])
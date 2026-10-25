from app.rag.retriever import search_curriculum


query = "Define Retrieval-Augmented Generation."

results = search_curriculum(query, top_k=3)

print(f"\nQuery: {query}")
print(f"Found {len(results)} results\n")

for i, result in enumerate(results, start=1):
    print("=" * 60)
    print(f"Result {i}")
    print("Source:", result["metadata"])
    print("Distance:", result["distance"])
    print("\nText:")
    print(result["text"][:500])
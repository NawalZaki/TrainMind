from app.tools import search_curriculum_tool


query = "What is RAG?"

results = search_curriculum_tool(query, top_k=3)

print("\n" + "=" * 60)
print("TOOL TEST")
print("=" * 60)

print(f"\nQuery: {query}")
print(f"Results: {len(results)}")

for i, result in enumerate(results, start=1):
    print("\n" + "-" * 60)
    print(f"Result {i}")
    print("Source:", result["metadata"])
    print("Text:", result["text"][:300])
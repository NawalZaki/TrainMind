
from app.rag.answer import answer_question


query = "What is the capital of Japan?"

result = answer_question(query, top_k=3)

print("\nQuestion:")
print(query)

print("\nTrainMind Answer:")
print(result["answer"])

print("\nSources:")

for source in result["sources"]:
    print(
        f"- {source['source']}, "
        f"page {source['page']}"
    )

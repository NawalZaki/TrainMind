import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.embed_content(
    model="gemini-embedding-001",
    contents="Retrieval-Augmented Generation combines information retrieval with language generation.",
)

embedding = response.embeddings[0].values

print("Gemini embedding created successfully!")
print("Vector dimensions:", len(embedding))
print("First 10 values:", embedding[:10])
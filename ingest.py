from app.ingestion.loaders import load_pdf
from app.ingestion.chunker import chunk_documents
from app.rag.embeddings import create_embeddings
from app.rag.vector_store import add_chunks

PDF_PATH = "data/raw/RAG_Practical_Guide.pdf"


def main():
    print("1. Loading PDF...")
    pages = load_pdf(PDF_PATH)
    print(f"   Loaded {len(pages)} pages.")

    print("2. Creating chunks...")
    chunks = chunk_documents(pages)
    print(f"   Created {len(chunks)} chunks.")

    print("3. Creating embeddings...")
    texts = [chunk["text"] for chunk in chunks]
    embeddings = create_embeddings(texts)
    print(f"   Created {len(embeddings)} embeddings.")

    print("4. Storing in ChromaDB...")
    add_chunks(chunks, embeddings)
    print("   Stored successfully!")

    print("\n✅ Ingestion completed!")


if __name__ == "__main__":
    main()
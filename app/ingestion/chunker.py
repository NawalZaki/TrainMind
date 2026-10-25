
def chunk_documents(
    documents: list[dict],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[dict]:
    """
    Split documents into overlapping chunks while preferring
    paragraph and sentence boundaries.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if not 0 <= chunk_overlap < chunk_size:
        raise ValueError(
            "chunk_overlap must be >= 0 and smaller than chunk_size"
        )

    chunks = []
    step = chunk_size - chunk_overlap

    boundaries = (
        "\n\n", "\n", ". ", "! ", "? ",
        "؟ ", "۔ ", "؛ ", "; ", "。"
    )

    for document in documents:
        text = document["text"].strip()
        metadata = document["metadata"]

        if not text:
            continue

        start = 0

        while start < len(text):
            target_end = min(start + chunk_size, len(text))
            end = target_end

            if target_end < len(text):
                # Prefer a natural boundary in the latter part
                # of the chunk instead of cutting too early.
                min_boundary = start + int(step * 0.6)
                candidates = []

                for boundary in boundaries:
                    position = text.rfind(
                        boundary, min_boundary, target_end
                    )

                    if position != -1:
                        candidates.append(position + len(boundary))

                if candidates:
                    end = max(candidates)
                else:
                    # Fallback: avoid splitting a word when possible.
                    whitespace = text.rfind(
                        " ", min_boundary, target_end
                    )

                    if whitespace != -1:
                        end = whitespace

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "metadata": metadata.copy(),
                })

            if end >= len(text):
                break

            # Preserve overlap while guaranteeing forward progress.
            next_start = max(start + 1, end - chunk_overlap)

            # Prefer starting the next chunk at a word boundary.
            whitespace = text.find(" ", next_start, end)

            if whitespace != -1:
                next_start = whitespace + 1

            start = next_start

    return chunks

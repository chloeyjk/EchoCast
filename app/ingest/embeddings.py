EMBEDDING_BATCH_SIZE = 64


def embed_texts(client, texts: list[str], model: str, batch_size: int = EMBEDDING_BATCH_SIZE) -> list[list[float]]:
    """Embed texts in batches; returns one vector per input, in input order."""
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        response = client.embeddings.create(model=model, input=batch)
        vectors.extend(item.embedding for item in sorted(response.data, key=lambda item: item.index))
    return vectors

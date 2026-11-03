def split_into_chunks(text, chunk_size=800, overlap=120):
    if not text:
        return []
    text = " ".join(str(text).split())

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be between 0 and chunk_size"
        )

    chunks = []

    start = 0

    while start < len(text):

        end = min(start + chunk_size, len(text))

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks
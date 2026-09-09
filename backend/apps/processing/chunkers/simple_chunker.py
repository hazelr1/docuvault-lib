def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 100):
    if not text:
        return []
    if chunk_overlap >= chunk_size:
        chunk_overlap = 0
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        piece = text[start:end]
        if piece:
            chunks.append({"content": piece, "char_start": start, "char_end": end})
        if end == len(text):
            break
        start = end - chunk_overlap
    return chunks

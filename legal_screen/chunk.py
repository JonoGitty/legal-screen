"""Split a document into overlapping chunks that keep their character offsets.

Chunks end at a paragraph or sentence boundary where one is near, and
overlap, so a clause that straddles a boundary is whole in at least one chunk.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    index: int
    start: int  # offset of the first character in the document
    end: int  # offset just past the last character
    text: str


def chunk_text(text: str, size: int = 4000, overlap: int = 400) -> list[Chunk]:
    if size <= overlap:
        raise ValueError("size must be larger than overlap")
    chunks: list[Chunk] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        if end < n:
            # prefer a paragraph break, then a sentence end, in the last quarter
            window = text[start + size * 3 // 4 : end]
            for sep in ("\n\n", "\n", ". ", "; "):
                cut = window.rfind(sep)
                if cut >= 0:
                    end = start + size * 3 // 4 + cut + len(sep)
                    break
        chunks.append(Chunk(len(chunks), start, end, text[start:end]))
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks

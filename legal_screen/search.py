"""Deterministic search: regex hits per checklist item, plus BM25 over chunks.

Search decides the ORDER in which Jeff checks chunks. Whether it can also
decide which chunks to skip is a speed/recall trade-off that is measured,
never assumed (eval/cuad_eval.py).
"""
import math
import re
from collections import Counter

from .checklist import Item
from .chunk import Chunk

_WORD = re.compile(r"[a-z][a-z\-']+")
_STOP = frozenset(
    "a an and are as at be by for from has have if in is it its of on or such that the this to was were which with any all can does do there what who whose upon".split()
)


def tokens(text: str) -> list[str]:
    return [w for w in _WORD.findall(text.lower()) if w not in _STOP]


def regex_hits(item: Item, text: str) -> list[tuple[int, int]]:
    """(start, end) of every pattern match, in order."""
    spans = []
    for p in item.patterns:
        spans.extend(m.span() for m in re.finditer(p, text, re.IGNORECASE | re.DOTALL))
    return sorted(spans)


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.toks = [tokens(d) for d in docs]
        self.k1, self.b = k1, b
        self.avg = sum(map(len, self.toks)) / max(1, len(self.toks))
        df = Counter(t for ts in self.toks for t in set(ts))
        n = len(self.toks)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.tf = [Counter(ts) for ts in self.toks]

    def score(self, query: str, i: int) -> float:
        tf, dl = self.tf[i], len(self.toks[i])
        s = 0.0
        for t in set(tokens(query)):
            if t in tf:
                f = tf[t]
                s += self.idf.get(t, 0.0) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avg))
        return s


def rank_chunks(item: Item, chunks: list[Chunk], bm25: BM25 | None = None) -> list[tuple[int, float]]:
    """Chunk indices, most promising first: regex hits dominate, BM25 breaks ties."""
    bm25 = bm25 or BM25([c.text for c in chunks])
    query = f"{item.name} {item.description}"
    scored = [(c.index, 10.0 * len(regex_hits(item, c.text)) + bm25.score(query, c.index)) for c in chunks]
    return sorted(scored, key=lambda x: -x[1])

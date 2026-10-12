"""Lexical similarity: the numpy-only stand-in for sentence embeddings.

Codebook refinement compares code definitions (to find duplicates) and a
code's examples (to keep varied ones). With sentence-transformers installed it
does that with sentence embeddings, which see meaning. Without it, this module
gives the same two steps a TF-IDF comparison, which sees shared words only:
two definitions that say the same thing in different words do not match, and
two that share their words but disagree ("trust in" against "distrust of")
look alike. Its threshold is therefore its own, calibrated on fixture
codebooks in tests/package/test_lexical_similarity.py, it only ever suggests
merges for the researcher to decide, and every result produced this way says
so (`similarity_method: "lexical-fallback"`).

Vectors are hashed into a fixed number of dimensions, so vectors from two
separate calls can still be compared, as example distribution across split
codes requires.
"""

from __future__ import annotations

import re
import zlib
from collections import Counter
from collections.abc import Sequence

import numpy as np

METHOD = "lexical-fallback"

# Cosine similarity at or above which two definitions are suggested as
# possible duplicates. Calibrated, not borrowed from the embedding threshold
# (0.85), which sits on a different scale: on the fixture it catches 7 of 8
# true duplicates and flags 3 of 15 distinct pairs. No threshold was safe
# enough to merge on, so the fallback suggests and never merges.
SUGGEST_THRESHOLD = 0.45

DIMENSIONS = 1 << 14

_STOPWORDS = frozenset("""
a about above after again against all also an and any are as at be because been
before being between both but by can could did do does doing down during each
either few for from further had has have having he her here hers him his how i
if in into is it its itself just may me might more most must my no nor not of
off on once only or other our out over own same she should so some such than
that the their them then there these they this those through to too under
until up upon very was we were what when where which while who whom why will
with within without would you your one ones use used using when whether e g
eg ie etc code codes
""".split())

_SUFFIXES = ("ations", "ation", "ingly", "ings", "ing", "edly", "ies", "ied",
             "ness", "ment", "ments", "ers", "er", "ed", "es", "ly", "s")


def _stem(word: str) -> str:
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return [_stem(w) for w in words if w not in _STOPWORDS and len(w) > 1]


def _slot(term: str) -> int:
    return zlib.crc32(term.encode("utf-8")) % DIMENSIONS


def tfidf_embed(texts: Sequence[str]) -> np.ndarray:
    """TF-IDF vectors for `texts`, IDF taken over the texts in this call.

    Sublinear term frequency and smoothed IDF; rows are L2-normalised, so a
    dot product is the cosine. An empty text gives a zero row, which the
    codebook's cosine function treats as similarity 0.
    """
    docs = [Counter(tokens(t)) for t in texts]
    n = len(docs)
    df = Counter(term for doc in docs for term in doc)
    out = np.zeros((n, DIMENSIONS), dtype=float)
    for row, doc in enumerate(docs):
        for term, count in doc.items():
            idf = np.log((1 + n) / (1 + df[term])) + 1.0
            out[row, _slot(term)] += (1.0 + np.log(count)) * idf
        norm = np.linalg.norm(out[row])
        if norm:
            out[row] /= norm
    return out

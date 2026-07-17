"""Semantic segmentation of interview transcripts.

Port of the chunking core from the Interview Transcript Semantic Chunker
notebook: speaker/timestamp parsing, embedding-based boundary detection,
and per-chunk coherence scoring. Embeddings are computed in a single pass
and reused for coherence, matching the notebook's verified behavior.

Heavy dependencies (nltk, sentence-transformers) are imported lazily so
the package can be used without them until chunking is invoked.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Optional

from .models import Chunk

# Common speaker label patterns. The delimiter is a colon only, and the
# capitalized catch-all is limited to one or two words (25 characters or
# fewer) immediately followed by ':' so that lines like "Note:" or
# "Background:" and mid-sentence colons do not create phantom speakers.
_SPEAKER_PATTERN = re.compile(
    r'^\s*'
    r'(?:'
    r'(?P<speaker>'
    r'(?:Interviewer|Interviewee|Respondent|Participant|Moderator|Speaker)'
    r'|(?:P|R|S|I|M)\d{0,3}'
    r'|(?:Dr|Mr|Mrs|Ms|Prof)\.?\s+[A-Z][a-z]+'
    r'|(?!(?i:note|notes|background|summary|question|answer|topic|date|time|location|source|transcript|warning|example)\b)'
    r'(?=[^:\n]{1,25}:)'
    r'(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?|[A-Z][A-Z\'\-]{1,24}(?:\s+[A-Z][A-Z\'\-]+)?)'
    r'(?=:)'
    r')'
    r')'
    r'\s*:\s*',
    re.MULTILINE
)

# Timestamp patterns: bracketed [00:12:34], parenthesized (12:34), or a bare
# HH:MM:SS at the start of a line. Bare MM:SS forms are not treated as
# timestamps, so a line beginning "3:30 in the afternoon" is left intact.
_TIMESTAMP_PATTERN = re.compile(
    r'(?:\[\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*\]'
    r'|\(\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*\)'
    r'|(\d{1,2}:\d{2}:\d{2})\b)'
)


@dataclass
class ParsedLine:
    """A single line from a transcript with extracted metadata."""

    text: str = ""
    speaker: str = ""
    timestamp: str = ""
    line_number: int = 0


def parse_transcript(text: str) -> list[ParsedLine]:
    """Parse raw transcript text into structured lines.

    Extracts speaker labels and timestamps where present; a detected
    speaker carries forward to subsequent unlabeled lines.
    """
    lines = text.split('\n')
    parsed_lines: list[ParsedLine] = []
    current_speaker = ""

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Check for timestamp
        timestamp = ""
        ts_match = _TIMESTAMP_PATTERN.match(line)
        if ts_match:
            timestamp = next(g for g in ts_match.groups() if g)
            line = line[ts_match.end():].strip()

        # Check for speaker label
        speaker_match = _SPEAKER_PATTERN.match(line)
        if speaker_match:
            current_speaker = speaker_match.group('speaker').strip()
            line = line[speaker_match.end():].strip()

        if line:
            parsed_lines.append(ParsedLine(
                text=line,
                speaker=current_speaker,
                timestamp=timestamp,
                line_number=i + 1
            ))

    return parsed_lines


_nltk_ready = False


def _sent_tokenize(text: str) -> list[str]:
    """Tokenize text into sentences, preparing NLTK data on first use."""
    global _nltk_ready
    import nltk
    from nltk.tokenize import sent_tokenize

    if not _nltk_ready:
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
        _nltk_ready = True
    return sent_tokenize(text)


_default_embedder: Any = None


def _get_default_embedder() -> Any:
    """Load and cache the all-MiniLM-L6-v2 sentence-transformer model."""
    global _default_embedder
    if _default_embedder is None:
        from sentence_transformers import SentenceTransformer
        _default_embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return _default_embedder


def _cosine_similarity(u: Any, v: Any) -> float:
    """Cosine similarity between two embedding vectors."""
    denom = (float((u * u).sum()) ** 0.5) * (float((v * v).sum()) ** 0.5)
    return float((u * v).sum()) / denom if denom else 0.0


def _compute_chunk_coherence(chunks: list[Chunk], embeddings: Any) -> None:
    """Score each chunk's internal consistency in place.

    Indexes into the sentence embeddings already computed for similarity
    scoring (no re-encoding). Coherence is the mean pairwise cosine
    similarity of the chunk's sentences; a single sentence scores 1.0.
    """
    for chunk in chunks:
        chunk_embeddings = embeddings[chunk.start_sentence:chunk.end_sentence + 1]

        if len(chunk_embeddings) < 2:
            chunk.coherence_score = 1.0  # single sentence is perfectly coherent
            continue

        sims = []
        for i in range(len(chunk_embeddings)):
            for j in range(i + 1, len(chunk_embeddings)):
                sims.append(_cosine_similarity(chunk_embeddings[i], chunk_embeddings[j]))

        chunk.coherence_score = round(sum(sims) / len(sims), 3) if sims else 1.0


def chunk_transcript(text: str, *,
                     source_file: str = "",
                     similarity_threshold: float = 0.5,
                     max_sentences: int = 5,
                     min_sentences: int = 1,
                     preserve_speakers: bool = True,
                     embedder: Any = None,
                     progress: Optional[Callable[[str], None]] = None) -> list[Chunk]:
    """Segment a transcript into semantically coherent chunks.

    Sentences are encoded once; chunk boundaries are placed where the
    cosine similarity between consecutive sentences drops below
    ``similarity_threshold``, subject to the min/max sentence limits.
    With ``preserve_speakers`` enabled, chunks never mix speakers and a
    speaker change splits regardless of ``min_sentences``.

    ``embedder`` is any object with ``.encode(list[str]) -> ndarray``;
    when None, the all-MiniLM-L6-v2 sentence-transformer model is loaded.
    ``progress`` is an optional callable receiving status messages.
    """
    def report(msg: str) -> None:
        if progress:
            progress(msg)

    if min_sentences > max_sentences:
        min_sentences = max_sentences

    parsed_lines = parse_transcript(text)
    if not parsed_lines:
        return []

    # Build sentences from parsed lines (each line may have multiple sentences)
    sentences: list[str] = []
    sentence_metadata: list[dict] = []  # Track speaker/timestamp per sentence

    for pl in parsed_lines:
        for s in _sent_tokenize(pl.text):
            sentences.append(s)
            sentence_metadata.append({
                'speaker': pl.speaker,
                'timestamp': pl.timestamp,
                'line_number': pl.line_number
            })

    if not sentences:
        return []

    if embedder is None:
        report("Loading sentence transformer model...")
        embedder = _get_default_embedder()

    # Single embedding pass, reused for both similarity and coherence
    report(f"Encoding {len(sentences)} sentences...")
    embeddings = embedder.encode(sentences)
    similarities = [_cosine_similarity(embeddings[i], embeddings[i + 1])
                    for i in range(len(sentences) - 1)]

    # Find chunk boundaries. The size counter is incremented at the top of
    # each iteration, so it always equals the number of sentences currently
    # in the chunk when the split decision is made.
    boundaries: list[int] = []
    current_chunk_size = 0

    for i, sim in enumerate(similarities):
        next_idx = i + 1
        current_chunk_size += 1

        should_split = False

        # Speaker boundary split: chunks never mix speakers, regardless of
        # the minimum-sentences setting
        if (preserve_speakers and
                next_idx < len(sentence_metadata) and
                sentence_metadata[next_idx]['speaker'] and
                sentence_metadata[next_idx]['speaker'] != sentence_metadata[i]['speaker']):
            should_split = True

        # Forced split: max sentences reached
        elif current_chunk_size >= max_sentences:
            should_split = True

        # Similarity-based split: topic shift detected
        elif sim < similarity_threshold and current_chunk_size >= min_sentences:
            should_split = True

        if should_split:
            boundaries.append(next_idx)
            current_chunk_size = 0

    # Build chunks from boundaries
    chunk_starts = [0] + boundaries
    chunk_ends = boundaries + [len(sentences)]

    chunks: list[Chunk] = []
    for chunk_id, (start, end) in enumerate(zip(chunk_starts, chunk_ends)):
        chunk_text = ' '.join(sentences[start:end])

        # Determine speaker for this chunk (most common speaker)
        chunk_speakers = [sentence_metadata[i]['speaker']
                          for i in range(start, end) if sentence_metadata[i]['speaker']]
        primary_speaker = max(set(chunk_speakers), key=chunk_speakers.count) if chunk_speakers else ''

        chunks.append(Chunk(
            chunk_id=chunk_id + 1,
            text=chunk_text,
            speaker=primary_speaker,
            start_sentence=start,
            end_sentence=end - 1,
            word_count=len(chunk_text.split()),
            timestamp_start=sentence_metadata[start]['timestamp'] or '',
            timestamp_end=sentence_metadata[end - 1]['timestamp'] or '',
            source_file=source_file
        ))

    # Compute coherence scores from the shared embeddings
    _compute_chunk_coherence(chunks, embeddings)

    report(f"Created {len(chunks)} chunks")
    return chunks


def chunks_to_records(chunks: list[Chunk]) -> list[dict]:
    """Convert chunks to dict records matching the notebook's CSV columns."""
    return [
        {
            'chunk_id': c.chunk_id,
            'text': c.text,
            'speaker': c.speaker,
            'word_count': c.word_count,
            'coherence_score': c.coherence_score,
            'start_sentence': c.start_sentence,
            'end_sentence': c.end_sentence,
            'timestamp_start': c.timestamp_start,
            'timestamp_end': c.timestamp_end,
            'source_file': c.source_file,
        }
        for c in chunks
    ]

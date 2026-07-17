"""Behavioral tests for ai_anthro_toolkit.chunking.

Ports the notebook's verified behavioral coverage: speaker/timestamp
parsing, boundary placement, speaker integrity, single-pass encoding,
coherence scoring, and the export record contract.

    python3.12 -m unittest tests.package.test_chunking -v
"""

import hashlib
import re
import unittest

import numpy as np

from ai_anthro_toolkit.chunking import chunk_transcript, chunks_to_records, parse_transcript


def _hash_embedding(text: str, dim: int = 32) -> np.ndarray:
    """Deterministic pseudo-embedding: similar strings -> similar vectors.

    Bag-of-words over hashed token buckets, L2-normalized, so cosine
    similarity behaves sensibly (shared words => higher similarity).
    """
    vec = np.zeros(dim)
    for tok in re.findall(r"[a-z']+", text.lower()):
        vec[int(hashlib.md5(tok.encode()).hexdigest(), 16) % dim] += 1.0
    n = np.linalg.norm(vec)
    return vec / n if n else vec


class StubEmbedder:
    """Deterministic embedder that counts encode calls."""

    def __init__(self):
        self.calls = []

    def encode(self, sentences, **kwargs):
        self.calls.append(len(sentences))
        return np.array([_hash_embedding(s) for s in sentences])


class TestSpeakerDetection(unittest.TestCase):
    def test_speaker_labels_detected(self):
        text = "\n".join([
            "MARIA: We arrived at dawn.",
            "Interviewer: What did you see?",
            "P1: Many boats near the shore.",
            "Maria Lopez: The tide was very low.",
            "JOSE-LUIS: We waited for hours.",
        ])
        parsed = parse_transcript(text)
        self.assertEqual([p.speaker for p in parsed],
                         ["MARIA", "Interviewer", "P1", "Maria Lopez", "JOSE-LUIS"])
        self.assertEqual(parsed[0].text, "We arrived at dawn.")

    def test_non_speaker_lines_rejected(self):
        for line in ["Note: recorded on site.",
                     "NOTE: check the audio levels.",
                     "Background: village market study.",
                     "The meeting; it ran very long."]:
            parsed = parse_transcript(line)
            self.assertEqual(len(parsed), 1, line)
            self.assertEqual(parsed[0].speaker, "", line)
            self.assertEqual(parsed[0].text, line, line)


class TestTimestampParsing(unittest.TestCase):
    def test_timestamp_formats_captured(self):
        text = "\n".join([
            "[00:12:34] MARIA: We began the interview.",
            "(12:34) The generator stopped working.",
            "00:15:02 MARIA: Another point entirely.",
        ])
        parsed = parse_transcript(text)
        self.assertEqual([p.timestamp for p in parsed],
                         ["00:12:34", "12:34", "00:15:02"])
        self.assertEqual(parsed[0].speaker, "MARIA")
        self.assertEqual(parsed[0].text, "We began the interview.")

    def test_clock_time_of_day_preserved(self):
        parsed = parse_transcript("3:30 in the afternoon we met the vendors.")
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].timestamp, "")
        self.assertEqual(parsed[0].text, "3:30 in the afternoon we met the vendors.")


class TestChunkBoundaries(unittest.TestCase):
    def _sizes(self, chunks):
        return [c.end_sentence - c.start_sentence + 1 for c in chunks]

    def test_uniform_max_split_sizes(self):
        text = "\n".join(["The market opens early every day."] * 7)
        chunks = chunk_transcript(text, max_sentences=3, embedder=StubEmbedder())
        self.assertEqual(self._sizes(chunks), [3, 3, 1])

    def test_min_sentences_respected_on_non_final_chunks(self):
        text = "\n".join([
            "Apples grow on the orchard trees.",
            "Parliament debated the new policy.",
            "Musicians performed joyful festival songs.",
            "Rivers flow toward the distant ocean.",
            "Computers process large digital archives.",
        ])
        chunks = chunk_transcript(text, similarity_threshold=0.5,
                                  max_sentences=10, min_sentences=2,
                                  embedder=StubEmbedder())
        self.assertEqual(self._sizes(chunks), [2, 2, 1])
        for chunk in chunks[:-1]:
            self.assertGreaterEqual(chunk.end_sentence - chunk.start_sentence + 1, 2)

    def test_speaker_integrity_beats_min_sentences(self):
        text = "\n".join([
            "MARIA: The market was crowded today.",
            "JOSE-LUIS: Prices have risen again lately.",
            "JOSE-LUIS: Vendors complain about the heat.",
        ])
        chunks = chunk_transcript(text, similarity_threshold=0.0,
                                  max_sentences=10, min_sentences=3,
                                  preserve_speakers=True,
                                  embedder=StubEmbedder())
        self.assertEqual(self._sizes(chunks), [1, 2])
        self.assertEqual([c.speaker for c in chunks], ["MARIA", "JOSE-LUIS"])


class TestEmbeddingAndCoherence(unittest.TestCase):
    def test_single_encode_pass(self):
        text = "\n".join([
            "MARIA: We sell fish at the market. The market opens at dawn.",
            "JOSE-LUIS: I repair the fishing boats. The boats need constant work.",
        ])
        stub = StubEmbedder()
        chunks = chunk_transcript(text, embedder=stub)
        self.assertTrue(chunks)
        self.assertEqual(len(stub.calls), 1)
        self.assertEqual(stub.calls[0], 4)

    def test_single_sentence_chunk_coherence_is_one(self):
        chunks = chunk_transcript("MARIA: We arrived at dawn.",
                                  embedder=StubEmbedder())
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].coherence_score, 1.0)


class TestRecords(unittest.TestCase):
    def test_records_contract_columns(self):
        text = "\n".join([
            "MARIA: We sell fish at the market.",
            "JOSE-LUIS: I repair the fishing boats.",
        ])
        chunks = chunk_transcript(text, source_file="interview1.txt",
                                  embedder=StubEmbedder())
        records = chunks_to_records(chunks)
        self.assertEqual(len(records), len(chunks))
        expected = ['chunk_id', 'text', 'speaker', 'word_count', 'coherence_score',
                    'start_sentence', 'end_sentence', 'timestamp_start',
                    'timestamp_end', 'source_file']
        for record in records:
            self.assertEqual(list(record.keys()), expected)
        self.assertEqual(records[0]['chunk_id'], 1)
        self.assertEqual(records[0]['source_file'], "interview1.txt")


if __name__ == "__main__":
    unittest.main()

"""Shared data structures for the analysis pipeline.

These mirror the structures used by the toolkit's Colab notebooks so that
package outputs and notebook outputs remain interchangeable.
"""

from dataclasses import dataclass, field, asdict


@dataclass
class Chunk:
    """One semantically coherent transcript segment (Chunker contract)."""

    chunk_id: int = 0
    text: str = ""
    speaker: str = ""
    start_sentence: int = 0
    end_sentence: int = 0
    word_count: int = 0
    coherence_score: float = 0.0
    timestamp_start: str = ""
    timestamp_end: str = ""
    source_file: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CodeEntry:
    """One qualitative code (Codebook Builder contract)."""

    label: str = ""
    definition: str = ""
    inclusion_criteria: list = field(default_factory=list)
    exclusion_criteria: list = field(default_factory=list)
    examples: list = field(default_factory=list)  # [{"text": ..., "source": ...}]
    extraction_type: str = "emergent"  # theoretical | methodological | emergent
    code_group: str = ""
    stance: str = ""  # lens registry key
    frequency: int = 0
    source_documents: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Theme:
    """One theme built from coded data (Coding & Thematic Analysis contract)."""

    name: str = ""
    definition: str = ""
    codes: list = field(default_factory=list)
    sub_themes: list = field(default_factory=list)
    evidence: list = field(default_factory=list)  # [{"chunk_id": ..., "quote": ...}]
    convergence_tag: str = ""  # CONVERGENT | LENS-SPECIFIC | FRICTION | ""

    def to_dict(self) -> dict:
        return asdict(self)

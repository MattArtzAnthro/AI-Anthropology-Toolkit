"""Codebook generation core (Qualitative Codebook Builder contract).

Ported from the verified notebook ``Qualitative_Codebook_Builder 2026 UPDATE
V2.ipynb``. The extraction and refinement logic — prompt text, JSON-response
hardening, label sanitisation, semantic deduplication, definition synthesis,
example-diversity selection, AI consolidation, soft cap, and quality
validation — follows the notebook cell for cell. Two deliberate departures:
widget/Colab I-O is replaced by a ``progress`` callback, and chunk processing
runs sequentially (the MCP layer owns concurrency).

The LLM is an injected callable::

    llm(prompt, *, system=None, temperature=0.3, max_tokens=4096) -> str

In delegated mode the callable raises :class:`ai_anthro_toolkit.llm.WorkPacket`;
that exception always propagates to the caller so the driving model can
complete the prompt and resume.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence

import numpy as np

from .lenses import STANCE_DEFINITIONS, find_lens
from .llm import WorkPacket
from .models import CodeEntry

# ── Notebook parameter constants ────────────────────────────────────────────

MAX_CODE_LABEL_LENGTH = 25   # Config.MAX_CODE_LABEL_LENGTH
MIN_DEFINITION_LENGTH = 20   # Config.MIN_DEFINITION_LENGTH
MAX_EXAMPLES_PER_CODE = 10   # example accumulation cap during extraction/merge
EXAMPLE_TEXT_LIMIT = 300     # stored example truncation length
SYNTHESIS_BATCH_SIZE = 8     # definition-synthesis batch size
DEFAULT_MAX_TOKENS = 4096    # Config.MAX_TOKENS

# ── Prompt constants (verbatim from the notebook; drift-test invariant) ─────
#
# Each constant reproduces the body of the notebook's prompt f-string exactly.
# Simple-name interpolations keep their notebook names; expression
# interpolations map to named placeholders as follows:
#   DEFINITION_SYNTHESIS_PROMPT: {codes_json}   <- {json.dumps(batch_codes, indent=2)}
#   CONSOLIDATION_PROMPT:        {code_count}   <- {len(code_summary)}
#                                {codebook_json} <- {json.dumps(code_summary, indent=2)}

# From get_extraction_prompt(). Rendered with .format(stance_name=...,
# research_block=..., stance_prompt=..., focus_text=..., max_codes=...); the
# result retains a {text} placeholder for the per-chunk second-stage format.
EXTRACTION_PROMPT_TEMPLATE = """You are a qualitative research assistant working within a {stance_name} analytical framework.
{research_block}
ANALYTICAL LENS:
{stance_prompt}

Extract codes from the text below that are relevant to the research context above, interpreted through the {stance_name} lens.

CODE TYPES TO EXTRACT:
{focus_text}

IMPORTANT: Extract at most {max_codes} of the most significant codes from this text.
Keep responses concise to ensure complete JSON output.

For each code provide:
- label: ≤25 characters, alphanumeric only, use_underscores (e.g., "ACTOR_NETWORK_THEORY")
- definition: One clear sentence (max 30 words), framed from the {stance_name} perspective
- extraction_type: "theoretical", "methodological", or "emergent"
- example: A brief quote from the text (max 50 words)
- inclusion: When to use this code, from a {stance_name} perspective (max 20 words)
- exclusion: When NOT to use this code (max 20 words)
- code_group: Category grouping based on thematic similarity

Text to analyze:
{{text}}

Return ONLY a valid JSON array. No markdown, no explanation:
[{{{{"label": "CODE_NAME", "definition": "...", "extraction_type": "...", "example": "...", "inclusion": "...", "exclusion": "...", "code_group": "..."}}}}]
"""

# Focus-specific instruction lines from get_extraction_prompt(), keyed by
# extraction-focus value and assembled in the notebook's fixed order.
FOCUS_INSTRUCTIONS = {
    "theoretical": (
        '- **Theoretical Constructs**: Named theories, frameworks, models, conceptual tools. '
        'Mark these with extraction_type: "theoretical"'),
    "methodological": (
        '- **Methodological Approaches**: Research methods, analytical techniques, study designs. '
        'Mark these with extraction_type: "methodological"'),
    "emergent": (
        '- **Emergent Concepts**: Recurring themes, patterns, and ideas across the text. '
        'Mark these with extraction_type: "emergent"'),
}

# From _synthesize_batch().
DEFINITION_SYNTHESIS_PROMPT = """You are refining code definitions for a {stance_name} qualitative codebook.

For each code below, synthesize the best possible definition by considering:
- The current definition
- The example passages where this code was found
- The {stance_name} analytical lens perspective

Return a JSON array with objects containing "label" and "definition" (max 30 words each).
Only improve definitions that are vague or could better reflect the {stance_name} lens.
Keep definitions that are already good.

Codes to refine:
{codes_json}

Return ONLY a valid JSON array:
[{{"label": "CODE_NAME", "definition": "improved definition..."}}]"""

# From ai_consolidation_pass().
CONSOLIDATION_PROMPT = """You are reviewing a qualitative codebook generated from a {stance_name} analytical lens.{research_context}

Review the codebook below and provide consolidation recommendations:

1. MERGE: Identify codes that substantially overlap and should be merged. For each, specify which code to keep and which to absorb.
2. SPLIT: Identify codes that are too broad and should be split into more specific codes.
3. REGROUP: Suggest improved code_group assignments to create a coherent hierarchical structure.
4. IMPROVE: For any codes with vague or incomplete definitions, provide improved versions.

Current codebook ({code_count} codes):
{codebook_json}

Return ONLY a valid JSON object with this structure:
{{
  "merges": [{{"keep": "LABEL_A", "absorb": "LABEL_B", "rationale": "..."}}],
  "splits": [{{"label": "BROAD_CODE", "into": [{{"label": "NEW_1", "definition": "..."}}, {{"label": "NEW_2", "definition": "..."}}], "rationale": "..."}}],
  "regroups": [{{"label": "CODE", "new_group": "Group Name"}}],
  "improved_definitions": [{{"label": "CODE", "definition": "improved definition"}}]
}}

Be conservative — only recommend changes that meaningfully improve the codebook.
If the codebook is already well-structured, return empty arrays."""


# ── Shared helpers ──────────────────────────────────────────────────────────

def _notify(progress: Callable[[str], None] | None, message: str) -> None:
    """Report a progress message through the optional callback."""
    if progress is not None:
        progress(message)


def _resolve_lens(lens_key: str) -> tuple[str, dict]:
    """Resolve a lens registry key or display name to (key, definition)."""
    if lens_key in STANCE_DEFINITIONS:
        return lens_key, STANCE_DEFINITIONS[lens_key]
    match = find_lens(lens_key)
    if match is not None:
        return match
    raise KeyError(f"Unknown analytical lens: {lens_key!r}")


_embedding_model = None


def _default_embedder(texts: Sequence[str]) -> np.ndarray:
    """Embed texts with sentence-transformers all-MiniLM-L6-v2 (lazy load)."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model.encode(list(texts), show_progress_bar=False)


def _cosine_similarity(a, b) -> float:
    """Cosine similarity between two vectors (0.0 when either is zero)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _sent_tokenize(text: str) -> list[str]:
    """Sentence-split with NLTK punkt, fetching the model data on first use."""
    from nltk.tokenize import sent_tokenize
    try:
        return sent_tokenize(text)
    except LookupError:
        import nltk
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
        return sent_tokenize(text)


# ── Text processing utilities (notebook cell "Text processing utilities") ───

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks of roughly ``chunk_size`` words.

    Sentences are never split; when a chunk fills, a proportional tail of its
    sentences (about ``overlap`` words) seeds the next chunk for continuity.
    """
    sentences = _sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        sentence_size = len(sentence.split())

        if current_size + sentence_size > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            overlap_sentences = int(overlap * len(current_chunk) / current_size) if current_size > 0 else 0
            current_chunk = current_chunk[-overlap_sentences:] if overlap_sentences > 0 else []
            current_size = sum(len(s.split()) for s in current_chunk)

        current_chunk.append(sentence)
        current_size += sentence_size

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def sanitize_code_label(label: str) -> str:
    """Normalise a code label: ≤25 chars, uppercase, underscore-separated."""
    label = label.replace(' ', '_')
    label = re.sub(r'([a-z])([A-Z])', r'\1_\2', label)
    label = re.sub(r'[^a-zA-Z0-9_]', '_', label)
    label = re.sub(r'_+', '_', label)
    label = label[:MAX_CODE_LABEL_LENGTH]
    label = label.strip('_')
    return label.upper()


def normalize_extraction_type(value) -> str:
    """Validate extraction_type against the three expected values.

    Case-insensitive with prefix tolerance; defaults to 'emergent'.
    """
    cleaned = str(value or '').strip().lower()
    if not cleaned:
        return 'emergent'
    for valid in ('theoretical', 'methodological', 'emergent'):
        if cleaned.startswith(valid) or valid.startswith(cleaned):
            return valid
    return 'emergent'


def parse_json_response(raw_text: str) -> list[dict]:
    """Parse JSON from a model response, tolerating markdown fences and
    truncation.

    Tries a direct parse, then extracts the outermost JSON array, then closes
    a truncated array at the last complete object. Returns ``[]`` when no
    valid JSON can be recovered; a lone object is wrapped in a list.
    """
    cleaned = raw_text.strip()

    # Remove markdown code blocks
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # Try direct parsing first
    try:
        result = json.loads(cleaned)
        return result if isinstance(result, list) else [result]
    except json.JSONDecodeError:
        pass

    # Try to find and extract just the JSON array
    array_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
    if array_match:
        try:
            result = json.loads(array_match.group())
            return result if isinstance(result, list) else [result]
        except json.JSONDecodeError:
            pass

    # Try to fix truncated JSON by closing open brackets
    open_brackets = cleaned.count('[') - cleaned.count(']')
    open_braces = cleaned.count('{') - cleaned.count('}')

    if open_brackets > 0 or open_braces > 0:
        last_complete = cleaned.rfind('},')
        if last_complete > 0:
            truncated = cleaned[:last_complete + 1] + ']'
            try:
                result = json.loads(truncated)
                return result if isinstance(result, list) else [result]
            except json.JSONDecodeError:
                pass

    return []


# ── Extraction ──────────────────────────────────────────────────────────────

def render_extraction_prompt(lens_key: str, extraction_focus: list[str],
                             max_codes: int) -> str:
    """Render the lens-shaped extraction prompt template.

    The returned string keeps a ``{text}`` placeholder: call
    ``.format(text=chunk)`` to produce the per-chunk prompt, mirroring the
    notebook's two-stage flow.
    """
    _, lens = _resolve_lens(lens_key)

    focus_instructions = [
        FOCUS_INSTRUCTIONS[focus]
        for focus in ('theoretical', 'methodological', 'emergent')
        if focus in extraction_focus
    ]
    focus_text = "\n".join(focus_instructions)

    return EXTRACTION_PROMPT_TEMPLATE.format(
        stance_name=lens['name'],
        research_block="",
        stance_prompt=lens['prompt_modifier'],
        focus_text=focus_text,
        max_codes=max_codes,
    )


def _integrate_extracted_codes(codebook: dict[str, CodeEntry],
                               extracted_codes: list[dict],
                               chunk_idx: int, doc_name: str,
                               stance_key: str) -> None:
    """Merge one chunk's extracted codes into the codebook in place."""
    for code_data in extracted_codes:
        if not isinstance(code_data, dict):
            continue

        label = sanitize_code_label(code_data.get('label', ''))
        if not label:
            continue

        if label not in codebook:
            code = CodeEntry(
                label=label,
                definition=code_data.get('definition', 'No definition provided'),
                code_group=code_data.get('code_group', 'Uncategorized'),
                extraction_type=normalize_extraction_type(code_data.get('extraction_type')),
                stance=stance_key,
                frequency=1,
            )
            code.source_documents.append(doc_name)
            example_text = code_data.get('example', '')
            if example_text:
                code.examples.append({
                    'text': example_text[:EXAMPLE_TEXT_LIMIT],
                    'source': doc_name,
                    'chunk': chunk_idx,
                })
            if code_data.get('inclusion'):
                code.inclusion_criteria.append(code_data['inclusion'])
            if code_data.get('exclusion'):
                code.exclusion_criteria.append(code_data['exclusion'])

            codebook[label] = code
        else:
            codebook[label].frequency += 1
            if doc_name not in codebook[label].source_documents:
                codebook[label].source_documents.append(doc_name)
            example_text = code_data.get('example', '')
            if example_text and len(codebook[label].examples) < MAX_EXAMPLES_PER_CODE:
                codebook[label].examples.append({
                    'text': example_text[:EXAMPLE_TEXT_LIMIT],
                    'source': doc_name,
                    'chunk': chunk_idx,
                })
            if code_data.get('inclusion') and code_data['inclusion'] not in codebook[label].inclusion_criteria:
                codebook[label].inclusion_criteria.append(code_data['inclusion'])
            if code_data.get('exclusion') and code_data['exclusion'] not in codebook[label].exclusion_criteria:
                codebook[label].exclusion_criteria.append(code_data['exclusion'])


def extract_codes(documents: Mapping[str, str], lens_key: str, *,
                  llm: Callable[..., str],
                  extraction_focus: Iterable[str] = ("theoretical", "emergent"),
                  max_codes: int = 30,
                  chunk_size: int = 400, overlap: int = 50,
                  temperature: float = 0.3,
                  progress: Callable[[str], None] | None = None,
                  ) -> dict[str, CodeEntry]:
    """Extract lens-shaped codes from documents.

    Each document is chunked (:func:`chunk_text`) and every chunk is sent to
    ``llm`` with the rendered extraction prompt. Parsed codes accumulate into
    a codebook keyed by sanitised label, tracking frequency, source documents,
    examples, and inclusion/exclusion criteria. Chunks are processed
    sequentially; concurrency, retries, and rate limiting belong to the
    caller. In delegated mode the ``llm`` raises
    :class:`~ai_anthro_toolkit.llm.WorkPacket`, which propagates.

    Args:
        documents: Mapping of document name to full text.
        lens_key: Analytical lens registry key (or display name).
        llm: Completion callable.
        extraction_focus: Subset of {'theoretical', 'methodological',
            'emergent'} selecting the code types to extract.
        max_codes: Per-chunk cap injected into the prompt.
        chunk_size: Target words per chunk.
        overlap: Word overlap carried between chunks.
        temperature: Sampling temperature for extraction calls.
        progress: Optional callback receiving status strings.

    Returns:
        Codebook mapping sanitised label -> :class:`CodeEntry`.
    """
    key, lens = _resolve_lens(lens_key)
    prompt_template = render_extraction_prompt(key, list(extraction_focus), max_codes)

    tasks: list[tuple[str, int, str]] = []
    for doc_name, content in documents.items():
        chunks = chunk_text(content, chunk_size, overlap)
        for i, chunk in enumerate(chunks):
            tasks.append((doc_name, i, chunk))

    total = len(tasks)
    codebook: dict[str, CodeEntry] = {}
    _notify(progress, f"[{lens['name']}] Starting extraction: "
                      f"{len(documents)} documents, {total} chunks")

    for processed, (doc_name, chunk_idx, chunk) in enumerate(tasks, start=1):
        raw_text = llm(prompt_template.format(text=chunk),
                       temperature=temperature, max_tokens=DEFAULT_MAX_TOKENS)
        extracted = parse_json_response(raw_text)
        if extracted:
            _integrate_extracted_codes(codebook, extracted, chunk_idx, doc_name, key)
        else:
            _notify(progress, f"[{lens['name']}] {doc_name} chunk {chunk_idx}: "
                              f"response could not be parsed — skipped")

        if processed % 10 == 0 or processed == total:
            pct = (processed / total) * 100 if total else 100.0
            _notify(progress, f"[{lens['name']}] Progress: {processed}/{total} "
                              f"({pct:.0f}%) | {len(codebook)} codes")

    type_counts = Counter(code.extraction_type for code in codebook.values())
    _notify(progress, f"[{lens['name']}] Extraction complete: {len(codebook)} codes "
                      f"| By type: {dict(type_counts)}")
    return codebook


# ── Refinement (notebook 7-step pipeline) ───────────────────────────────────

def _find_semantic_merge_candidates(codebook: dict[str, CodeEntry],
                                    threshold: float,
                                    embed: Callable[[Sequence[str]], np.ndarray],
                                    ) -> list[tuple[str, str, float]]:
    """Find code pairs whose definition similarity meets the threshold."""
    labels = list(codebook.keys())
    embeddings = embed([codebook[label].definition for label in labels])
    candidates = []

    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            sim = _cosine_similarity(embeddings[i], embeddings[j])
            if sim >= threshold:
                candidates.append((labels[i], labels[j], sim))

    candidates.sort(key=lambda x: x[2], reverse=True)
    return candidates


def _merge_codes(codebook: dict[str, CodeEntry], label_keep: str,
                 label_remove: str) -> dict[str, CodeEntry]:
    """Merge ``label_remove`` into ``label_keep``, combining their metadata."""
    keep = codebook[label_keep]
    remove = codebook[label_remove]

    keep.frequency += remove.frequency

    for doc in remove.source_documents:
        if doc not in keep.source_documents:
            keep.source_documents.append(doc)

    for ex in remove.examples:
        if len(keep.examples) < MAX_EXAMPLES_PER_CODE:
            keep.examples.append(ex)

    for inc in remove.inclusion_criteria:
        if inc not in keep.inclusion_criteria:
            keep.inclusion_criteria.append(inc)
    for exc in remove.exclusion_criteria:
        if exc not in keep.exclusion_criteria:
            keep.exclusion_criteria.append(exc)

    del codebook[label_remove]
    return codebook


def _semantic_deduplication(codebook: dict[str, CodeEntry], threshold: float,
                            auto_merge: bool,
                            embed: Callable[[Sequence[str]], np.ndarray],
                            progress: Callable[[str], None] | None,
                            ) -> tuple[dict[str, CodeEntry], list[dict]]:
    """Merge (or suggest merging) semantically duplicate codes.

    With ``auto_merge`` the higher-frequency code of each pair absorbs the
    other; otherwise the codebook is returned unchanged alongside the
    suggested pairs.
    """
    initial_count = len(codebook)
    candidates = _find_semantic_merge_candidates(codebook, threshold, embed)

    if not candidates:
        _notify(progress, "Semantic deduplication: no duplicates above threshold")
        return codebook, []

    if not auto_merge:
        suggestions = [
            {'code_a': label_a, 'code_b': label_b, 'similarity': sim}
            for label_a, label_b, sim in candidates
        ]
        _notify(progress, f"Semantic deduplication: auto_merge off — "
                          f"{len(suggestions)} suggested merge pairs (not applied)")
        return codebook, suggestions

    merged_count = 0
    already_merged: set[str] = set()

    for label_a, label_b, sim in candidates:
        if label_a in already_merged or label_b in already_merged:
            continue
        if label_a not in codebook or label_b not in codebook:
            continue

        # Keep the one with higher frequency
        if codebook[label_a].frequency >= codebook[label_b].frequency:
            keep, remove = label_a, label_b
        else:
            keep, remove = label_b, label_a

        _notify(progress, f"Merging '{remove}' -> '{keep}' (similarity: {sim:.3f})")
        codebook = _merge_codes(codebook, keep, remove)
        already_merged.add(remove)
        merged_count += 1

    _notify(progress, f"Semantic deduplication: merged {merged_count} codes "
                      f"({initial_count} -> {len(codebook)})")
    return codebook, []


def _synthesize_definitions(codebook: dict[str, CodeEntry], stance_name: str,
                            llm: Callable[..., str],
                            progress: Callable[[str], None] | None,
                            ) -> dict[str, CodeEntry]:
    """Improve definitions of multi-occurrence codes via the LLM.

    Only codes seen more than once with more than one example are sent, in
    batches of :data:`SYNTHESIS_BATCH_SIZE`. A batch whose response cannot be
    obtained or parsed is skipped; :class:`WorkPacket` propagates.
    """
    codes_to_synthesize = {
        label: code for label, code in codebook.items()
        if code.frequency > 1 and len(code.examples) > 1
    }

    if not codes_to_synthesize:
        _notify(progress, "Definition synthesis: no multi-occurrence codes to synthesize")
        return codebook

    _notify(progress, f"Definition synthesis: {len(codes_to_synthesize)} codes")

    all_code_summaries = []
    for label, code in codes_to_synthesize.items():
        example_texts = [ex['text'][:150] for ex in code.examples[:5]]
        all_code_summaries.append({
            'label': label,
            'current_definition': code.definition,
            'examples': example_texts,
            'frequency': code.frequency,
            'inclusion': code.inclusion_criteria[:3],
            'exclusion': code.exclusion_criteria[:3],
        })

    batches = [all_code_summaries[i:i + SYNTHESIS_BATCH_SIZE]
               for i in range(0, len(all_code_summaries), SYNTHESIS_BATCH_SIZE)]

    updated = 0
    for batch in batches:
        prompt = DEFINITION_SYNTHESIS_PROMPT.format(
            stance_name=stance_name,
            codes_json=json.dumps(batch, indent=2),
        )
        try:
            refined = parse_json_response(
                llm(prompt, temperature=0.3, max_tokens=DEFAULT_MAX_TOKENS))
        except WorkPacket:
            raise
        except Exception:
            refined = []
        for item in refined:
            if isinstance(item, dict) and item.get('label') and item.get('definition'):
                label = item['label']
                if label in codebook and item['definition'] != codebook[label].definition:
                    codebook[label].definition = item['definition']
                    updated += 1

    _notify(progress, f"Definition synthesis: refined {updated} definitions")
    return codebook


def _select_diverse_examples(codebook: dict[str, CodeEntry], max_examples: int,
                             embed: Callable[[Sequence[str]], np.ndarray],
                             progress: Callable[[str], None] | None,
                             ) -> dict[str, CodeEntry]:
    """Keep each code's most diverse examples via farthest-point selection.

    Starting from the first example, iteratively selects the candidate whose
    highest similarity to the already-selected set is lowest, preserving
    original example order in the result.
    """
    for label, code in codebook.items():
        if len(code.examples) <= max_examples:
            continue

        embeddings = embed([ex['text'] for ex in code.examples])

        selected_indices = [0]
        remaining = list(range(1, len(embeddings)))

        while len(selected_indices) < max_examples and remaining:
            best_idx = None
            best_max_sim = None

            for idx in remaining:
                max_sim = max(
                    _cosine_similarity(embeddings[idx], embeddings[s])
                    for s in selected_indices
                )
                # Pick the candidate whose highest similarity to the selected set is lowest
                if best_max_sim is None or max_sim < best_max_sim:
                    best_max_sim = max_sim
                    best_idx = idx

            selected_indices.append(best_idx)
            remaining.remove(best_idx)

        code.examples = [code.examples[i] for i in sorted(selected_indices)]

    _notify(progress, f"Example diversity: kept up to {max_examples} most "
                      f"diverse examples per code")
    return codebook


def _distribute_examples_to_children(parent: CodeEntry,
                                     children: list[CodeEntry],
                                     embed: Callable[[Sequence[str]], np.ndarray],
                                     ) -> None:
    """Assign each parent example to the most similar child of a split.

    Similarity compares the example text against each child's label plus
    definition. If assignment fails, every child receives copies of all
    parent examples.
    """
    if not parent.examples or not children:
        return
    try:
        child_texts = [f"{child.label.replace('_', ' ')}: {child.definition}"
                       for child in children]
        child_embeddings = embed(child_texts)
        example_embeddings = embed([ex['text'] for ex in parent.examples])
        for ex, ex_emb in zip(parent.examples, example_embeddings):
            sims = [_cosine_similarity(ex_emb, c_emb) for c_emb in child_embeddings]
            children[int(np.argmax(sims))].examples.append(ex)
    except Exception:
        for child in children:
            child.examples = [dict(ex) for ex in parent.examples]


def _ai_consolidation_pass(codebook: dict[str, CodeEntry], stance_name: str,
                           llm: Callable[..., str],
                           embed: Callable[[Sequence[str]], np.ndarray],
                           progress: Callable[[str], None] | None,
                           ) -> dict[str, CodeEntry]:
    """Apply an LLM consolidation review: merges, splits, regroups, and
    definition improvements.

    Split children inherit the parent's group, type, stance, criteria, and
    source documents, with frequency divided among them and examples
    distributed by similarity. The response is parsed with the hardened
    parser; on any failure other than :class:`WorkPacket` the codebook is
    returned unchanged.
    """
    code_summary = []
    for label, code in sorted(codebook.items(), key=lambda x: x[1].frequency, reverse=True):
        code_summary.append({
            'label': label,
            'definition': code.definition,
            'code_group': code.code_group,
            'extraction_type': code.extraction_type,
            'frequency': code.frequency,
        })

    prompt = CONSOLIDATION_PROMPT.format(
        stance_name=stance_name,
        research_context="",
        code_count=len(code_summary),
        codebook_json=json.dumps(code_summary, indent=2),
    )

    try:
        response_text = llm(prompt, temperature=0.3, max_tokens=DEFAULT_MAX_TOKENS)

        # Parse with the hardened parser so truncated responses degrade gracefully
        parsed = parse_json_response(response_text)
        if not parsed or not isinstance(parsed[0], dict):
            _notify(progress, "Consolidation response could not be parsed "
                              "(possibly truncated) — no changes applied")
            return codebook

        recommendations = parsed[0]

        # Apply merges
        merge_count = 0
        for merge in recommendations.get('merges', []):
            keep = merge.get('keep', '')
            absorb = merge.get('absorb', '')
            if keep in codebook and absorb in codebook:
                _notify(progress, f"Consolidation merge: '{absorb}' -> '{keep}' "
                                  f"({merge.get('rationale', '')})")
                codebook = _merge_codes(codebook, keep, absorb)
                merge_count += 1

        # Apply splits
        split_count = 0
        for split in recommendations.get('splits', []):
            original_label = split.get('label', '')
            new_codes = split.get('into', [])
            if original_label in codebook and len(new_codes) >= 2:
                original = codebook[original_label]
                created = []
                for new_code_data in new_codes:
                    new_label = sanitize_code_label(new_code_data.get('label', ''))
                    if new_label and new_label not in codebook:
                        new_code = CodeEntry(
                            label=new_label,
                            definition=new_code_data.get('definition', original.definition),
                            code_group=original.code_group,
                            extraction_type=original.extraction_type,
                            stance=original.stance,
                            frequency=max(1, original.frequency // len(new_codes)),
                            source_documents=list(original.source_documents),
                            inclusion_criteria=list(original.inclusion_criteria),
                            exclusion_criteria=list(original.exclusion_criteria),
                        )
                        codebook[new_label] = new_code
                        created.append(new_label)
                if created:
                    _distribute_examples_to_children(
                        original, [codebook[l] for l in created], embed)
                    del codebook[original_label]
                    split_count += 1
                    _notify(progress, f"Consolidation split: '{original_label}' -> {created}")

        # Apply regroups
        regroup_count = 0
        for regroup in recommendations.get('regroups', []):
            label = regroup.get('label', '')
            new_group = regroup.get('new_group', '')
            if label in codebook and new_group:
                codebook[label].code_group = new_group
                regroup_count += 1

        # Apply improved definitions
        improve_count = 0
        for imp in recommendations.get('improved_definitions', []):
            label = imp.get('label', '')
            new_def = imp.get('definition', '')
            if label in codebook and new_def:
                codebook[label].definition = new_def
                improve_count += 1

        if merge_count or split_count or regroup_count or improve_count:
            _notify(progress, f"Consolidation applied: {merge_count} merges, "
                              f"{split_count} splits, {regroup_count} regroups, "
                              f"{improve_count} improved definitions")
        else:
            _notify(progress, "Consolidation: codebook is well-structured — "
                              "no changes recommended")

    except WorkPacket:
        raise
    except Exception as exc:
        _notify(progress, f"Consolidation pass skipped (error: {str(exc)[:60]})")

    return codebook


def refine_codebook(codebook: dict[str, CodeEntry], lens_key: str, *,
                    llm: Callable[..., str] | None = None,
                    min_frequency: int = 2,
                    similarity_threshold: float = 0.85,
                    auto_merge: bool = True,
                    max_examples: int = 3,
                    soft_cap: int = 30,
                    embedder: Callable[[Sequence[str]], np.ndarray] | None = None,
                    progress: Callable[[str], None] | None = None,
                    ) -> tuple[dict[str, CodeEntry], dict]:
    """Run the notebook's seven-step refinement pipeline on a codebook.

    Steps, in order: frequency filtering, semantic deduplication, definition
    synthesis, example-diversity selection, AI consolidation, soft cap, and
    quality validation.

    Args:
        codebook: Codebook from :func:`extract_codes` (not mutated as a
            mapping; entries themselves are updated in place).
        lens_key: Analytical lens registry key (or display name).
        llm: Completion callable used for synthesis and consolidation. When
            None, those two steps are skipped and only the deterministic
            steps run (frequency filter, dedup, diversity, cap, validation).
        min_frequency: Codes seen fewer times are dropped.
        similarity_threshold: Cosine similarity at or above which code
            definitions count as duplicates.
        auto_merge: Apply duplicate merges automatically; when False the
            pairs are reported in the quality report's ``merge_suggestions``
            without being merged.
        max_examples: Maximum examples retained per code.
        soft_cap: Keep at most this many codes, by descending frequency.
        embedder: Callable mapping a list of texts to embedding vectors;
            defaults to lazy sentence-transformers all-MiniLM-L6-v2.
        progress: Optional callback receiving status strings.

    Returns:
        ``(refined_codebook, quality_report)`` where the report carries the
        notebook's validation block (quality score, issue summary, counts),
        code-group tallies, and any unapplied merge suggestions.
    """
    key, lens = _resolve_lens(lens_key)
    embed = embedder if embedder is not None else _default_embedder
    codebook = dict(codebook)
    initial_count = len(codebook)

    _notify(progress, f"Refining codebook [{lens['name']}]: {initial_count} codes")

    # Step 1: Frequency filtering
    codes_below_frequency = [
        label for label, code in codebook.items()
        if code.frequency < min_frequency
    ]
    for label in codes_below_frequency:
        del codebook[label]
    if codes_below_frequency:
        _notify(progress, f"Frequency filtering: removed {len(codes_below_frequency)} "
                          f"codes below threshold ({min_frequency})")

    # Step 2: Semantic deduplication
    merge_suggestions: list[dict] = []
    if len(codebook) > 1:
        codebook, merge_suggestions = _semantic_deduplication(
            codebook, similarity_threshold, auto_merge, embed, progress)

    # Step 3: Definition synthesis (LLM step; skipped when llm is None)
    if llm is not None:
        codebook = _synthesize_definitions(codebook, lens['name'], llm, progress)

    # Step 4: Example diversity
    codebook = _select_diverse_examples(codebook, max_examples, embed, progress)

    # Step 5: AI consolidation pass (LLM step; skipped when llm is None)
    if llm is not None and len(codebook) > 3:
        codebook = _ai_consolidation_pass(codebook, lens['name'], llm, embed, progress)

    # Step 6: Soft cap
    if len(codebook) > soft_cap:
        sorted_codes = sorted(codebook.items(), key=lambda x: x[1].frequency, reverse=True)
        removed_by_cap = len(codebook) - soft_cap
        codebook = dict(sorted_codes[:soft_cap])
        _notify(progress, f"Soft cap: kept top {soft_cap} codes by frequency "
                          f"(removed {removed_by_cap})")

    # Step 7: Quality validation
    validation_issues = {
        'missing_definitions': 0,
        'short_definitions': 0,
        'missing_examples': 0,
    }
    for label, code in codebook.items():
        if not code.definition or code.definition == 'No definition provided':
            validation_issues['missing_definitions'] += 1
        elif len(code.definition) < MIN_DEFINITION_LENGTH:
            validation_issues['short_definitions'] += 1
        if len(code.examples) < 1:
            validation_issues['missing_examples'] += 1

    total_codes = len(codebook)
    if total_codes > 0:
        issue_count = sum(validation_issues.values())
        # Two issue families are checked per code (definition quality, example presence)
        quality_score = max(0, 1 - (issue_count / (total_codes * 2)))
    else:
        quality_score = 0

    group_counts = Counter(code.code_group for code in codebook.values())

    quality_report = {
        'validation': {
            'quality_score': quality_score,
            'summary': validation_issues,
            'initial_count': initial_count,
            'final_count': len(codebook),
            'stance': key,
        },
        'groups': dict(group_counts),
        'merge_suggestions': merge_suggestions,
    }

    _notify(progress, f"Refinement complete [{lens['name']}]: {initial_count} -> "
                      f"{len(codebook)} codes | quality score {quality_score:.2f}")

    return codebook, quality_report


# ── End-to-end and export helpers ───────────────────────────────────────────

_EXTRACT_OPTION_KEYS = frozenset(
    ('extraction_focus', 'max_codes', 'chunk_size', 'overlap', 'temperature'))
_REFINE_OPTION_KEYS = frozenset(
    ('min_frequency', 'similarity_threshold', 'auto_merge', 'max_examples',
     'soft_cap', 'embedder'))


def build_codebook(documents: Mapping[str, str], lens_key: str, *,
                   llm: Callable[..., str],
                   **options) -> tuple[dict[str, CodeEntry], dict]:
    """Extract and refine a codebook in one call.

    Keyword options are routed to :func:`extract_codes`
    (``extraction_focus``, ``max_codes``, ``chunk_size``, ``overlap``,
    ``temperature``) and :func:`refine_codebook` (``min_frequency``,
    ``similarity_threshold``, ``auto_merge``, ``max_examples``, ``soft_cap``,
    ``embedder``); ``progress`` is shared by both stages.

    Returns:
        ``(refined_codebook, quality_report)``.
    """
    progress = options.pop('progress', None)
    extract_options = {k: options.pop(k) for k in list(options)
                       if k in _EXTRACT_OPTION_KEYS}
    refine_options = {k: options.pop(k) for k in list(options)
                      if k in _REFINE_OPTION_KEYS}
    if options:
        raise TypeError(f"Unknown build_codebook options: {sorted(options)}")

    codebook = extract_codes(documents, lens_key, llm=llm,
                             progress=progress, **extract_options)
    return refine_codebook(codebook, lens_key, llm=llm,
                           progress=progress, **refine_options)


def codebook_to_records(codebook: dict[str, CodeEntry],
                        lens_key: str) -> list[dict]:
    """Flatten a codebook into export records matching the notebook's CSV.

    Columns, in order: code_label, definition, extraction_type, code_group,
    stance (display name), stance_key, inclusion_criteria,
    exclusion_criteria, example_1..example_3, frequency, source_documents.
    Records are sorted by descending frequency.
    """
    key, lens = _resolve_lens(lens_key)
    stance_name = lens['name']

    rows = []
    for label, code in codebook.items():
        rows.append({
            'code_label': label,
            'definition': code.definition,
            'extraction_type': code.extraction_type,
            'code_group': code.code_group,
            'stance': stance_name,
            'stance_key': key,
            'inclusion_criteria': '; '.join(code.inclusion_criteria),
            'exclusion_criteria': '; '.join(code.exclusion_criteria),
            'example_1': code.examples[0]['text'] if code.examples else '',
            'example_2': code.examples[1]['text'] if len(code.examples) > 1 else '',
            'example_3': code.examples[2]['text'] if len(code.examples) > 2 else '',
            'frequency': code.frequency,
            'source_documents': '; '.join(code.source_documents),
        })

    rows.sort(key=lambda row: row['frequency'], reverse=True)
    return rows

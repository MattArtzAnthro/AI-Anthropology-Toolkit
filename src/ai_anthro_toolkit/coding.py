"""Deductive, inductive, and hybrid coding of transcript chunks.

Port of the coding core from ``Coding_and_Thematic_Analysis_2026_UPDATE_v16``.
Prompts are carried over verbatim as module-level constants; the pipeline runs
sequentially (the MCP layer owns concurrency) and reports progress through
callbacks rather than printed output.
"""

import random
import re
from collections.abc import Callable

from .lenses import find_lens
from .models import CodeEntry

# Prompt sent as the system message for every deductive coding call.
# Placeholders: lens_context, codebook_text, valid_codes_list.
DEDUCTIVE_CODING_PROMPT = """You are a qualitative research assistant specializing in deductive coding. Your task is to analyze text segments and identify which codes from the codebook apply.

{lens_context}{codebook_text}

CODING INSTRUCTIONS:
1. Read each text segment carefully
2. Apply ALL relevant codes from the codebook that match the content
3. **CRITICAL: You may ONLY use codes from the VALID CODES list below. Do NOT invent, modify, or abbreviate code names.**
4. Return codes as a comma-separated list (e.g., "CODE1,CODE2,CODE3")
5. If no codes apply, return "NO_CODES"
6. Be consistent - similar content should receive similar codes
7. Match codes exactly as written - do not paraphrase or create similar-sounding codes

VALID CODES (use ONLY these exact codes):
{valid_codes_list}

Return only the comma-separated codes from the valid codes list above. No explanations."""

# Retry prompt sent (at temperature 0.0, with the coding system prompt) when a
# response contains codes outside the codebook.
# Placeholders: invalid_codes, valid_codes_str, text.
VALIDATION_RETRY_PROMPT = """The following codes you returned are NOT in the valid codebook: {invalid_codes}

Please re-analyze the text and ONLY use codes from this list:
{valid_codes_str}

Text to code: {text}

Return ONLY valid codes from the list above, comma-separated. If none apply, return NO_CODES."""

# Prompt used to discover emergent inductive codes from a sample of chunks.
# Placeholders: lens_context, chunks_text.
INDUCTIVE_GENERATION_PROMPT = """You are conducting INDUCTIVE CODING on interview transcripts.
{lens_context}Your task is to identify EMERGENT THEMES that are NOT captured by the existing deductive codes.

SAMPLE CHUNKS FOR ANALYSIS:
{chunks_text}

TASK: Identify 8-12 EMERGENT INDUCTIVE CODES that capture important patterns NOT covered by deductive codes.

For each code provide:
**INDUCTIVE CODE: [SHORT_NAME]**
Definition: [Clear description]
Rationale: [Why this is important]
Example: "[Direct quote]"
When to Apply: [Clear criteria]

Ensure there is a blank line between codes."""

# System prompt used when applying discovered inductive codes to each chunk.
# Placeholder: codes_text.
INDUCTIVE_APPLICATION_PROMPT = """Apply these INDUCTIVE CODES to text chunks.

INDUCTIVE CODES:
{codes_text}

Instructions:
1. Apply ONLY codes that clearly match
2. Return codes as comma-separated list
3. If no codes apply, return "NONE"

Return ONLY the code names."""

# Sample size for inductive code discovery (run_single_stance_analysis default).
INDUCTIVE_SAMPLE_SIZE = 60

_DEDUCTIVE_CHECKPOINT_INTERVAL = 15
_INDUCTIVE_CHECKPOINT_INTERVAL = 25


def build_lens_context(lens_key: str = "", research_context: dict | None = None) -> str:
    """Build the research context + analytical lens framing for prompt injection.

    Args:
        lens_key: Lens registry key or display name (resolved case-insensitively
            via :func:`ai_anthro_toolkit.lenses.find_lens`). An unresolvable
            value produces a generic framing block; the MCP layer is
            responsible for surfacing the mismatch to the researcher.
        research_context: Optional dict with ``project_name``,
            ``research_question``, and ``study_description`` keys.

    Returns:
        The framing string, or ``""`` when no lens or context is available.
    """
    parts = []
    ctx = research_context or {}

    rq = str(ctx.get("research_question", "") or "").strip()
    sd = str(ctx.get("study_description", "") or "").strip()
    pn = str(ctx.get("project_name", "") or "").strip()

    if rq or sd or pn:
        parts.append("RESEARCH CONTEXT:")
        if pn:
            parts.append(f"Project: {pn}")
        if rq:
            parts.append(f"Research Question: {rq}")
        if sd:
            parts.append(f"Study Context: {sd}")
        parts.append("")

    if lens_key:
        found = find_lens(lens_key)
        if found:
            _, entry = found
            display_name = entry["name"]
            modifier = entry["prompt_modifier"]
        else:
            display_name = lens_key
            modifier = (f"Analytical lens: {lens_key}. "
                        f"Apply codes through this analytical framework.")
        parts.append(f"ANALYTICAL FRAMEWORK ({display_name}):")
        parts.append(modifier)
        parts.append("")
        parts.append("Apply codes with attention to these analytical priorities.")
        parts.append("")

    return "\n".join(parts)


def match_code_to_list(code: str, valid_codes: list[str]) -> str | None:
    """Match a returned code against a list of valid codes.

    Accepts exact matches, case-insensitive matches, and truncation recovery
    when the code is a prefix of exactly one valid code and is at least 10
    characters long (or at least 60% of that code's length). Returns the
    matched valid code, or None when no reliable match exists.
    """
    code_clean = code.strip()
    if not code_clean:
        return None

    if code_clean in valid_codes:
        return code_clean

    lower_map = {c.lower(): c for c in valid_codes}
    if code_clean.lower() in lower_map:
        return lower_map[code_clean.lower()]

    prefix_matches = [c for c in valid_codes if c.startswith(code_clean)]
    if len(prefix_matches) == 1:
        full_code = prefix_matches[0]
        if len(code_clean) >= 10 or len(code_clean) >= 0.6 * len(full_code):
            return full_code

    return None


def _present(value) -> bool:
    """True when a field value carries content (None/NaN/blank-safe)."""
    return value is not None and value == value and str(value).strip() != ""


def _criteria_text(value) -> str:
    """Normalize an inclusion/exclusion criteria field to a single string."""
    if isinstance(value, (list, tuple)):
        return "; ".join(str(v) for v in value if _present(v))
    return str(value).strip() if _present(value) else ""


def normalize_codebook(codebook: list[dict] | dict) -> dict:
    """Normalize a codebook into ``{code_label: {definition, inclusion, exclusion, examples}}``.

    Accepts either Codebook Builder records (``code_label`` / ``definition`` /
    ``inclusion_criteria`` / ``exclusion_criteria`` / ``example_1..3``) or a
    dict of :class:`ai_anthro_toolkit.models.CodeEntry` keyed by label.
    """
    code_dict = {}

    if isinstance(codebook, dict):
        for key, entry in codebook.items():
            if isinstance(entry, CodeEntry):
                label = entry.label or str(key)
                examples = []
                for ex in entry.examples:
                    text = ex.get("text") if isinstance(ex, dict) else ex
                    if _present(text):
                        examples.append(str(text))
                code_dict[label] = {
                    "definition": entry.definition,
                    "inclusion": _criteria_text(entry.inclusion_criteria),
                    "exclusion": _criteria_text(entry.exclusion_criteria),
                    "examples": examples,
                }
            else:
                entry = dict(entry)
                entry.setdefault("code_label", str(key))
                code_dict.update(normalize_codebook([entry]))
        return code_dict

    for row in codebook:
        code = row["code_label"]
        examples = []
        for field in ("example_1", "example_2", "example_3"):
            if _present(row.get(field)):
                examples.append(row[field])
        code_dict[code] = {
            "definition": row["definition"],
            "inclusion": _criteria_text(row.get("inclusion_criteria", "")),
            "exclusion": _criteria_text(row.get("exclusion_criteria", "")),
            "examples": examples,
        }

    return code_dict


def _render_system_prompt(code_dict: dict, lens_context: str) -> str:
    """Render the deductive coding system prompt from a normalized codebook."""
    codebook_text = "DEDUCTIVE CODING CODEBOOK:\n\n"
    for code, details in code_dict.items():
        codebook_text += f"CODE: {code}\n"
        codebook_text += f"Definition: {details['definition']}\n"
        if details["inclusion"]:
            codebook_text += f"Include when: {details['inclusion']}\n"
        if details["exclusion"]:
            codebook_text += f"Exclude when: {details['exclusion']}\n"
        codebook_text += "\n"

    valid_codes_list = ", ".join(code_dict.keys())

    return DEDUCTIVE_CODING_PROMPT.format(
        lens_context=lens_context,
        codebook_text=codebook_text,
        valid_codes_list=valid_codes_list,
    )


def render_coding_prompt(chunk_text: str, codebook_records: list[dict],
                         lens_context: str) -> str:
    """Render one complete deductive coding prompt for delegated execution.

    Combines the system prompt (codebook, lens framing, valid-code
    constraints) with the per-chunk user turn, so a delegating model receives
    everything needed to code the chunk in a single prompt.
    """
    system_prompt = _render_system_prompt(normalize_codebook(codebook_records),
                                          lens_context)
    return f"{system_prompt}\n\nCode this text: {chunk_text}"


def _validate_codes(codes_list: list[str], valid_codes: list[str]) -> tuple[list[str], list[str]]:
    """Split returned codes into (valid, invalid) using the tolerant matcher."""
    valid = []
    invalid = []
    for code in codes_list:
        code_clean = code.strip()
        if not code_clean:
            continue
        matched = match_code_to_list(code_clean, valid_codes)
        if matched:
            valid.append(matched)
        else:
            invalid.append(code_clean)
    return list(dict.fromkeys(valid)), invalid


def parse_coding_response(text: str, valid_codes: list[str]) -> list[str]:
    """Parse a deductive coding response into validated code labels.

    ``NO_CODES`` (case-insensitive) and empty responses yield an empty list;
    everything else is comma-split and validated against ``valid_codes`` via
    :func:`match_code_to_list`, with unmatched codes dropped and duplicates
    removed while preserving order.
    """
    raw = text.strip()
    if raw == "" or raw.upper() == "NO_CODES":
        return []
    codes_list = [c.strip() for c in raw.split(",") if c.strip()]
    valid, _ = _validate_codes(codes_list, valid_codes)
    return valid


def _code_chunk_deductive(llm: Callable[..., str], system_prompt: str,
                          text: str, valid_names: list[str]) -> list[str]:
    """Code one chunk deductively, retrying once at temperature 0.0 on invalid codes."""
    raw = llm(f"Code this text: {text}", system=system_prompt,
              temperature=0.1, max_tokens=150).strip()

    if raw == "" or raw.upper() == "NO_CODES":
        return []

    codes_list = [c.strip() for c in raw.split(",") if c.strip()]
    valid, invalid = _validate_codes(codes_list, valid_names)

    if invalid:
        retry_prompt = VALIDATION_RETRY_PROMPT.format(
            invalid_codes=invalid,
            valid_codes_str=", ".join(valid_names),
            text=text,
        )
        retry_raw = llm(retry_prompt, system=system_prompt,
                        temperature=0.0, max_tokens=150).strip()

        if retry_raw == "" or retry_raw.upper() == "NO_CODES":
            # On retry, if the model says no codes, keep the valid codes
            # from the first attempt.
            return valid

        retry_list = [c.strip() for c in retry_raw.split(",") if c.strip()]
        retry_valid, _ = _validate_codes(retry_list, valid_names)
        return list(dict.fromkeys(valid + retry_valid))

    return valid


def parse_inductive_codes(analysis_text: str) -> dict:
    """Parse discovered inductive codes from a generation response.

    Returns ``{code_name: {definition, rationale, example, application}}``.
    """
    codes = {}

    if not analysis_text:
        return codes

    code_blocks = re.split(r"\*\*INDUCTIVE CODE: (.+?)\*\*\s*\n", analysis_text,
                           flags=re.DOTALL | re.IGNORECASE)

    if len(code_blocks) < 2:
        return codes

    for i in range(1, len(code_blocks), 2):
        code_name = code_blocks[i].strip()
        block_content = code_blocks[i + 1].strip() if i + 1 < len(code_blocks) else ""

        codes[code_name] = {
            "definition": "",
            "rationale": "",
            "example": "",
            "application": "",
        }

        definition_match = re.search(
            r"Definition: (.+?)(?:\nRationale:|\nExample:|\nWhen to Apply:|$)",
            block_content, re.DOTALL)
        if definition_match:
            codes[code_name]["definition"] = definition_match.group(1).strip()

        rationale_match = re.search(
            r"Rationale: (.+?)(?:\nDefinition:|\nExample:|\nWhen to Apply:|$)",
            block_content, re.DOTALL)
        if rationale_match:
            codes[code_name]["rationale"] = rationale_match.group(1).strip()

        example_match = re.search(
            r"Example: (.+?)(?:\nDefinition:|\nRationale:|\nWhen to Apply:|$)",
            block_content, re.DOTALL)
        if example_match:
            codes[code_name]["example"] = example_match.group(1).strip()

        application_match = re.search(
            r"When to Apply: (.+?)(?:\nDefinition:|\nRationale:|\nExample:|$)",
            block_content, re.DOTALL)
        if application_match:
            codes[code_name]["application"] = application_match.group(1).strip()

    return codes


def _sample_chunks(records: list[dict], sample_size: int) -> list[dict]:
    """Seeded sample of chunks with text, for inductive code discovery."""
    candidates = [r for r in records if _present(r.get("text"))]
    k = min(sample_size, len(candidates))
    if k == len(candidates):
        return candidates
    return random.Random(42).sample(candidates, k)


def code_chunks(chunks: list[dict], codebook: list[dict] | dict, *,
                llm: Callable[..., str], approach: str = "hybrid",
                lens_key: str = "", research_context: dict | None = None,
                progress: Callable[[str, int, int], None] | None = None,
                checkpoint: Callable[[int, list[dict]], None] | None = None) -> list[dict]:
    """Code transcript chunks against a codebook.

    Runs the coding pipeline sequentially: a deductive pass with invalid-code
    retry (temperature 0.0, coding system prompt included), then — for the
    ``hybrid`` and ``inductive`` approaches — inductive code discovery over a
    seeded sample followed by application of the discovered codes to every
    chunk (validated against the discovered set).

    Args:
        chunks: Chunk records; each needs ``text`` and ideally ``chunk_id``.
        codebook: Codebook Builder records or a dict of
            :class:`ai_anthro_toolkit.models.CodeEntry` keyed by label.
        llm: Completion callable ``llm(prompt, *, system, temperature,
            max_tokens) -> str``. In delegated mode this raises
            :class:`ai_anthro_toolkit.llm.WorkPacket`, which propagates to
            the caller.
        approach: ``"deductive"``, ``"inductive"``, or ``"hybrid"``.
        lens_key: Optional analytical lens for prompt framing.
        research_context: Optional project/question/description dict.
        progress: Optional callable ``progress(stage, done, total)`` with
            stage in ``{"deductive", "inductive"}``.
        checkpoint: Optional callable ``checkpoint(processed, records)``
            invoked at the notebook's checkpoint intervals.

    Returns:
        One record per input chunk: the input fields plus ``Deductive_Codes``,
        ``Inductive_Codes``, ``All_Codes`` (inductive codes suffixed
        ``_IND``), and ``Coding_Status`` (``Deductive_Only`` /
        ``Inductive_Only`` / ``Both_Deductive_Inductive`` / ``No_Codes``).
    """
    approach_key = approach.strip().lower()
    if approach_key not in ("deductive", "inductive", "hybrid"):
        raise ValueError(f"unknown coding approach: {approach!r}")

    code_dict = normalize_codebook(codebook)
    lens_context = build_lens_context(lens_key, research_context)

    records = []
    for chunk in chunks:
        record = dict(chunk)
        record["Deductive_Codes"] = ""
        record["Inductive_Codes"] = ""
        records.append(record)
    total = len(records)

    # Phase 1: deductive coding.
    if approach_key in ("deductive", "hybrid"):
        system_prompt = _render_system_prompt(code_dict, lens_context)
        valid_names = list(code_dict.keys())

        for i, record in enumerate(records):
            text = record.get("text")
            if _present(text):
                codes = _code_chunk_deductive(llm, system_prompt, str(text), valid_names)
                record["Deductive_Codes"] = ",".join(codes)
            if progress:
                progress("deductive", i + 1, total)
            if checkpoint and (i + 1) % _DEDUCTIVE_CHECKPOINT_INTERVAL == 0:
                checkpoint(i + 1, records)

    # Phase 2: inductive discovery and application.
    if approach_key in ("inductive", "hybrid"):
        sample = _sample_chunks(records, INDUCTIVE_SAMPLE_SIZE)
        chunks_text = ""
        for record in sample:
            chunks_text += (f"\nChunk {record.get('chunk_id')}:\n{record['text']}\n"
                            f"Deductive codes: {record.get('Deductive_Codes', '')}\n---\n")

        generation_prompt = INDUCTIVE_GENERATION_PROMPT.format(
            lens_context=lens_context, chunks_text=chunks_text)
        analysis = llm(generation_prompt, temperature=0.4, max_tokens=3000)
        discovered = parse_inductive_codes(analysis)

        if discovered:
            codes_text = "\n".join(
                f"{code}: {details['definition']} (Apply when: {details['application']})"
                for code, details in discovered.items())
            apply_system = INDUCTIVE_APPLICATION_PROMPT.format(codes_text=codes_text)
            discovered_names = list(discovered.keys())

            for i, record in enumerate(records):
                text = record.get("text")
                if _present(text):
                    result = llm(f"Text: {text}", system=apply_system,
                                 temperature=0.1, max_tokens=100).strip()
                    if result and result.upper() != "NONE":
                        applied = []
                        for c in result.split(","):
                            matched = match_code_to_list(c.strip(), discovered_names)
                            if matched:
                                applied.append(matched)
                        applied = list(dict.fromkeys(applied))
                        if applied:
                            record["Inductive_Codes"] = ",".join(applied)
                if progress:
                    progress("inductive", i + 1, total)
                if checkpoint and (i + 1) % _INDUCTIVE_CHECKPOINT_INTERVAL == 0:
                    checkpoint(i + 1, records)

    # Integration: status and unified code column (inductive codes suffixed _IND).
    for record in records:
        deductive = [c.strip() for c in record["Deductive_Codes"].split(",") if c.strip()]
        inductive = [c.strip() for c in record["Inductive_Codes"].split(",") if c.strip()]
        all_codes = deductive + [c + "_IND" for c in inductive]
        record["All_Codes"] = ", ".join(all_codes)
        if deductive and inductive:
            record["Coding_Status"] = "Both_Deductive_Inductive"
        elif deductive:
            record["Coding_Status"] = "Deductive_Only"
        elif inductive:
            record["Coding_Status"] = "Inductive_Only"
        else:
            record["Coding_Status"] = "No_Codes"

    if checkpoint:
        checkpoint(total, records)

    return records

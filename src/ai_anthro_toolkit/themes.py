"""Theme building from coded chunks.

Port of the thematic synthesis core from
``Coding_and_Thematic_Analysis_2026_UPDATE_v16`` (IntegratedThemeBuilder plus
the theme parser from ThematicAnalyzer). The theme-building prompt is carried
over verbatim; the convergence-tagging variant is activated by passing
``convergence_info``.
"""

import math
import re
from collections import Counter, defaultdict
from collections.abc import Callable

from .coding import build_lens_context
from .models import Theme

# Prompt for building hierarchical themes from integrated coding results.
# Placeholders: lens_context, total_code_applications, unique_codes,
# top_deductive_codes, top_inductive_codes, cross_lens_section,
# pattern_examples, convergence_task_line, convergence_format_line.
# The convergence placeholders are filled with the constants below in
# multi-lens runs and left empty otherwise.
THEME_BUILDING_PROMPT = """You are a qualitative research expert building THEMES from mixed-method coding results.

{lens_context}CODING OVERVIEW:
- Total code applications: {total_code_applications}
- Unique codes: {unique_codes}

TOP DEDUCTIVE CODES:
{top_deductive_codes}

TOP INDUCTIVE CODES:
{top_inductive_codes}

{cross_lens_section}SAMPLE CODED CHUNKS:
{pattern_examples}

TASK: Create 5-7 HIERARCHICAL THEMES that:
1. Integrate insights from both deductive and inductive codes
2. Have clear main themes with 2-3 sub-themes each
3. Are actionable and relevant
{convergence_task_line}

Format each theme as:

THEME [Number]: [Clear, Descriptive Name]
Core Concept: [2-3 sentences explaining what this theme captures]
Sub-themes:
  a) [Sub-theme name]: [Brief description]
  b) [Sub-theme name]: [Brief description]
  c) [Sub-theme name]: [Brief description]
Key Finding: [The main insight this theme reveals, including which codes support it]
Supporting Codes: [List the exact code names that support this theme, e.g., VALUE_BASED_CARE_TRANSFOR, OUTCOME_BASED_SUBSIDY_MODELS_IND]
Evidence Strength: [Strong/Moderate/Emerging] ([Total code count] combined code applications: [CODE_NAME]=[count], [CODE_NAME]=[count], ...)
{convergence_format_line}

CRITICAL: The "Supporting Codes" line MUST list the actual code names from the TOP CODES lists above that relate to this theme. Use the exact uppercase code names with underscores.
"""

# Convergence-tagging variant: extra task instruction and format line inserted
# into THEME_BUILDING_PROMPT when convergence_info is provided.
THEME_CONVERGENCE_TASK_LINE = ("4. Tag each theme as CONVERGENT (supported by multiple lenses) "
                               "or LENS-SPECIFIC (primarily one lens) "
                               "or FRICTION (lenses disagree on this theme)")

THEME_CONVERGENCE_FORMAT_LINE = ("Lens Convergence: [CONVERGENT: supported by X, Y lenses "
                                 "| LENS-SPECIFIC: primarily from X lens "
                                 "| FRICTION: lenses disagree on this theme]")

# Cross-lens context block inserted before SAMPLE CODED CHUNKS in multi-lens
# runs. Placeholder: summary.
CROSS_LENS_SECTION = """
CROSS-LENS ANALYSIS:
{summary}

When building themes, note:
- Where themes are supported across multiple lenses (CONVERGENT) vs. primarily one lens (LENS-SPECIFIC)
- Build at least one theme around high-friction chunks where lenses diverge — these reveal what each framework foregrounds or obscures
"""

_NON_CODE_WORDS = {"THEME", "STRONG", "MODERATE", "EMERGING", "IND", "WEAK"}


def _chunk_codes(record: dict) -> list[str]:
    """All codes applied to a chunk (deductive plus inductive, unsuffixed)."""
    codes = []
    for column in ("Deductive_Codes", "Inductive_Codes"):
        raw = record.get(column, "")
        if raw is not None and raw == raw and str(raw).strip():
            codes.extend(c.strip() for c in str(raw).split(",") if c.strip())
    return codes


def code_patterns(coded: list[dict]) -> dict:
    """Analyze frequency and co-occurrence patterns in integrated codes.

    Returns the notebook's pattern dict (total applications, unique codes,
    frequencies, frequent combinations) plus a pairwise ``cooccurrence``
    matrix over the top 20 codes with self-pairs excluded.
    """
    all_codes_list = []
    deductive_codes_list = []
    inductive_codes_list = []
    code_combinations = defaultdict(int)

    for record in coded:
        raw = record.get("All_Codes", "")
        if raw is not None and raw == raw and str(raw).strip():
            codes = [c.strip() for c in str(raw).split(",") if c.strip()]
            all_codes_list.extend(codes)

            deductive = [c for c in codes if not c.endswith("_IND")]
            inductive = [c for c in codes if c.endswith("_IND")]
            deductive_codes_list.extend(deductive)
            inductive_codes_list.extend(inductive)

            if len(codes) > 1:
                code_combinations[tuple(sorted(codes))] += 1

    all_freq = Counter(all_codes_list)
    deductive_freq = Counter(deductive_codes_list)
    inductive_freq = Counter(inductive_codes_list)

    # Co-occurrence matrix over the top 20 codes, self-pairs excluded.
    top_codes = list(dict(all_freq).keys())[:20]
    cooccurrence = {c1: {c2: 0 for c2 in top_codes} for c1 in top_codes}
    for record in coded:
        raw = record.get("All_Codes", "")
        if raw is not None and raw == raw and str(raw).strip():
            codes = [c.strip() for c in str(raw).split(",") if c.strip()]
            codes = [c for c in codes if c in top_codes]
            for i, code1 in enumerate(codes):
                for code2 in codes[i + 1:]:
                    cooccurrence[code1][code2] += 1
                    if code1 != code2:
                        cooccurrence[code2][code1] += 1

    return {
        "total_code_applications": len(all_codes_list),
        "unique_codes": len(set(all_codes_list)),
        "all_codes_frequency": dict(all_freq),
        "deductive_frequency": dict(deductive_freq.most_common(15)),
        "inductive_frequency": dict(inductive_freq.most_common(15)),
        "frequent_combinations": dict(sorted(code_combinations.items(),
                                             key=lambda x: x[1], reverse=True)[:15]),
        "cooccurrence": cooccurrence,
    }


def _format_top_codes(freq_dict: dict, limit: int) -> str:
    """Format top codes for the theme prompt."""
    lines = []
    for code, freq in list(freq_dict.items())[:limit]:
        lines.append(f"• {code}: {freq} occurrences")
    return "\n".join(lines)


def _agreement_value(record: dict) -> float | None:
    """A record's Agreement_Score as a float, or None when absent/NaN."""
    value = record.get("Agreement_Score")
    if value is None:
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(score) else score


def _pattern_examples(coded: list[dict], include_friction: bool) -> str:
    """Sample chunks (mixed-coded, plus friction chunks in multi-lens runs)."""
    examples = []

    mixed = [r for r in coded if r.get("Coding_Status") == "Both_Deductive_Inductive"][:3]
    for record in mixed:
        text_preview = str(record.get("text", ""))[:200] + "..."
        ded_codes = record.get("Deductive_Codes", "None")
        ind_codes = record.get("Inductive_Codes", "None")
        examples.append(f"\nChunk {record.get('chunk_id')}:\nText: {text_preview}\n"
                        f"Deductive: {ded_codes}\nInductive: {ind_codes}")

    if include_friction:
        scored = [(r, _agreement_value(r)) for r in coded]
        scored = [(r, s) for r, s in scored if s is not None]
        for record, score in sorted(scored, key=lambda pair: pair[1])[:2]:
            text_preview = str(record.get("text", ""))[:200] + "..."
            examples.append(f"\nFriction Chunk {record.get('chunk_id')}:\nText: {text_preview}\n"
                            f"All codes: {record.get('All_Codes', '')}\nAgreement: {score:.3f}")

    return "\n".join(examples) if examples else "No examples available"


def _clean_md(text: str) -> str:
    """Strip markdown bold markers from a parsed text field."""
    return re.sub(r"\*\*([^*]+)\*\*", r"\1", text) if text else ""


def _parse_sub_themes(section: str) -> list[dict]:
    """Parse the Sub-themes block of one theme section."""
    sub_themes = []
    subtheme_match = re.search(
        r"\*\*Sub-themes:\*\*\s*([\s\S]*?)(?=\*\*Key Finding|\*\*Evidence Strength|---|##|$)",
        section, re.IGNORECASE)
    if not subtheme_match:
        subtheme_match = re.search(
            r"Sub-themes:\s*([\s\S]*?)(?=Key Finding|Evidence|---|##|$)",
            section, re.IGNORECASE)
    if not subtheme_match:
        return sub_themes

    subtheme_text = subtheme_match.group(1)
    items = re.split(r"(?:^|\s+)([a-e])\)\s*", subtheme_text)

    i = 1
    while i < len(items) - 1:
        content = items[i + 1].strip() if i + 1 < len(items) else ""
        if content:
            name_match = re.match(r"\*\*([^:*]+):\*\*\s*(.+)", content, re.DOTALL)
            if name_match:
                name = name_match.group(1).strip()
                desc = name_match.group(2).strip()
                desc = re.sub(r"\s+", " ", desc)
                desc = desc.replace("**", "").replace("*", "")
                desc = re.sub(r"\s+[b-e]\)\s*$", "", desc)
                sub_themes.append({"name": name, "description": desc[:500]})
            else:
                name_match2 = re.match(r"([^:]+):\s*(.+)", content, re.DOTALL)
                if name_match2:
                    name = name_match2.group(1).strip().replace("**", "")
                    desc = name_match2.group(2).strip()
                    desc = re.sub(r"\s+", " ", desc).replace("**", "").replace("*", "")
                    sub_themes.append({"name": name, "description": desc[:500]})
        i += 2

    if not sub_themes:
        bullet_items = re.findall(r"[-•]\s*\*\*([^:*]+):\*\*\s*([^\n]+)", subtheme_text)
        for name, desc in bullet_items:
            sub_themes.append({"name": name.strip(),
                               "description": desc.strip().replace("**", "")})

    return sub_themes


def _theme_evidence(coded: list[dict], theme_codes: list[str]) -> list[dict]:
    """Chunks whose applied codes match the theme's supporting codes."""
    evidence = []
    for record in coded:
        all_codes = _chunk_codes(record)
        for theme_code in theme_codes:
            if any(theme_code.lower() in code.lower() for code in all_codes):
                evidence.append({"chunk_id": record.get("chunk_id"),
                                 "quote": str(record.get("text", ""))})
                break
    return evidence


def parse_themes(themes_text: str, coded: list[dict],
                 tag_convergence: bool = False) -> list[Theme]:
    """Parse a theme-building response into :class:`Theme` objects.

    Extracts each theme's name, core concept (definition), supporting codes
    (from the Key Finding, Evidence Strength, and Supporting Codes lines),
    sub-themes, and evidence chunks. Convergence tags are read from the
    ``Lens Convergence`` line only when ``tag_convergence`` is set.
    """
    themes = []
    theme_sections = re.split(r"(?:^|\n)(?:##\s*)?THEME\s+(\d+):", themes_text,
                              flags=re.IGNORECASE)

    for i in range(1, len(theme_sections), 2):
        if i + 1 >= len(theme_sections):
            break
        theme_num = theme_sections[i].strip()
        section = theme_sections[i + 1]

        title_match = re.search(r"^\s*([^\n]+)", section)
        if not title_match:
            continue
        theme_title = re.sub(r"\*\*", "", title_match.group(1).strip())
        theme_name = f"Theme {theme_num}: {theme_title}"

        codes = set()

        # Code extraction runs with the Lens Convergence line removed so its
        # tag keywords (CONVERGENT, LENS-SPECIFIC, FRICTION) never leak into
        # the code list; the tag itself is parsed from the full section below.
        code_section = re.sub(r"(?im)^.*Lens Convergence.*$", "", section)

        finding_match = re.search(
            r"\*\*Key Finding[s]?:\*\*\s*([^\n]+(?:\n(?!\*\*|##)[^\n]+)*)",
            code_section, re.IGNORECASE)
        if not finding_match:
            finding_match = re.search(
                r"Key Finding[s]?:\s*([^\n]+(?:\n(?!\*\*|##)[^\n]+)*)",
                code_section, re.IGNORECASE)
        if finding_match:
            codes.update(re.findall(r"\b([A-Z][A-Z0-9_]+(?:_IND)?)\b",
                                    finding_match.group(1).strip()))

        ev_match = re.search(
            r"\*\*Evidence Strength:\*\*\s*([^\n]+(?:\n(?!\*\*|##)[^\n]+)*)",
            code_section, re.IGNORECASE)
        if not ev_match:
            ev_match = re.search(r"Evidence Strength:\s*([^\n]+)", code_section,
                                 re.IGNORECASE)
        if ev_match:
            codes.update(re.findall(r"\b([A-Z][A-Z0-9_]+(?:_IND)?)\b",
                                    ev_match.group(1).strip()))

        supp_match = re.search(r"Supporting Codes:\s*([^\n]+)", code_section,
                               re.IGNORECASE)
        if supp_match:
            codes.update(re.findall(r"\b([A-Z][A-Z0-9_]+(?:_IND)?)\b",
                                    supp_match.group(1)))

        codes = sorted(c for c in codes if len(c) > 3 and c not in _NON_CODE_WORDS)

        insight_match = re.search(
            r"\*\*Core (?:Insight|Concept):\*\*\s*([^\n]+(?:\n(?!\*\*)[^\n]+)*)",
            section, re.IGNORECASE)
        if not insight_match:
            insight_match = re.search(r"Core (?:Insight|Concept):\s*([^\n]+)",
                                      section, re.IGNORECASE)
        core_insight = insight_match.group(1).strip() if insight_match else ""
        core_insight = re.sub(r"^\*\*\s*", "", core_insight)

        convergence_tag = ""
        if tag_convergence:
            conv_match = re.search(r"Lens Convergence:\s*([^\n]+)", section, re.IGNORECASE)
            if conv_match:
                tag_match = re.search(r"\b(CONVERGENT|LENS-SPECIFIC|FRICTION)\b",
                                      conv_match.group(1))
                if tag_match:
                    convergence_tag = tag_match.group(1)

        themes.append(Theme(
            name=theme_name,
            definition=_clean_md(core_insight),
            codes=codes,
            sub_themes=_parse_sub_themes(section),
            evidence=_theme_evidence(coded, codes),
            convergence_tag=convergence_tag,
        ))

    return themes


def build_themes(coded: list[dict], *, llm: Callable[..., str],
                 lens_key: str = "", research_context: dict | None = None,
                 convergence_info: dict | None = None) -> list[Theme]:
    """Build hierarchical themes from coded chunks.

    Renders the theme-building prompt from the coding patterns and sample
    chunks, completes it with ``llm``, and parses the response into
    :class:`ai_anthro_toolkit.models.Theme` objects.

    Args:
        coded: Output records of :func:`ai_anthro_toolkit.coding.code_chunks`
            (multi-lens merges may add ``Agreement_Score`` per chunk).
        llm: Completion callable ``llm(prompt, *, system, temperature,
            max_tokens) -> str``.
        lens_key: Optional analytical lens for prompt framing.
        research_context: Optional project/question/description dict.
        convergence_info: Optional cross-lens context. When provided, the
            prompt switches to the convergence-tagging variant (its
            ``summary`` value fills the CROSS-LENS ANALYSIS block, friction
            chunks join the samples) and parsed themes carry
            ``convergence_tag`` values.

    Returns:
        The parsed themes with codes, sub-themes, and evidence chunks.
    """
    patterns = code_patterns(coded)
    lens_context = build_lens_context(lens_key, research_context)

    multi_lens = convergence_info is not None
    cross_lens_section = ""
    convergence_task_line = ""
    convergence_format_line = ""
    if multi_lens:
        cross_lens_section = CROSS_LENS_SECTION.format(
            summary=convergence_info.get("summary", ""))
        convergence_task_line = THEME_CONVERGENCE_TASK_LINE
        convergence_format_line = THEME_CONVERGENCE_FORMAT_LINE

    theme_prompt = THEME_BUILDING_PROMPT.format(
        lens_context=lens_context,
        total_code_applications=patterns["total_code_applications"],
        unique_codes=patterns["unique_codes"],
        top_deductive_codes=_format_top_codes(patterns["deductive_frequency"], 10),
        top_inductive_codes=_format_top_codes(patterns["inductive_frequency"], 10),
        cross_lens_section=cross_lens_section,
        pattern_examples=_pattern_examples(coded, include_friction=multi_lens),
        convergence_task_line=convergence_task_line,
        convergence_format_line=convergence_format_line,
    )

    themes_analysis = llm(theme_prompt, temperature=0.3, max_tokens=4000)
    return parse_themes(themes_analysis, coded, tag_convergence=multi_lens)

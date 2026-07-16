# Skills Library Design

Architectural rationale and shared parameter framework for the AI Anthropology
Toolkit skills library. Individual SKILL.md files cite this document for the
canonical stance list and cross-skill conventions; it is not itself a skill.

## Architecture

Each skill is a self-contained folder under `skills/` following the Agent
Skills progressive-disclosure model:

1. **Metadata** (`name` + `description` frontmatter, ~100 tokens) — loaded at
   startup for every skill; the description carries trigger phrases and
   explicit "Do NOT use" routing to neighboring skills.
2. **Instructions** (SKILL.md body, under 5,000 tokens) — loaded when the
   skill activates.
3. **References** (`references/*.md`) — loaded only when the workflow calls
   for them.

Conventions:

- Skill names are kebab-case and match their directory name.
- Reference files are one level deep from SKILL.md and are each cited in the
  SKILL.md body with instructions on when to load them.
- Cross-skill handoffs name the target skill exactly (e.g., "use the
  research-writing skill"); descriptions must never route to skills that do
  not exist in this library.
- SKILL.md bodies follow a shared skeleton: Quick Reference → Workflow →
  Parameters → Guardrails → Common Failure Modes → Examples.
- All content is anthropology-specific. If output could appear unchanged in a
  generic social science methods textbook, it fails the library's bar.

## Shared Parameter Framework

Skills share a common set of design parameters so that a project can move
through the research lifecycle without re-specifying its identity at each
phase:

- **Epistemic stance** — the user's theoretical orientation; the canonical
  list is below. Stance is a first-class design parameter: it shapes question
  grammar, method compatibility, analysis, writing voice, and how
  "contribution" is framed.
- **Genre / audience** — journal article, dissertation prospectus, grant
  application, committee document, public writing, applied/consulting output.
- **Field configuration** — single site, multi-sited, digital, archival,
  hybrid, comparative.
- **Career stage** — undergraduate, MA, PhD, postdoc, faculty; calibrates
  scope and scaffolding.
- **Risk posture** — low-risk, vulnerable populations, high-surveillance,
  politically sensitive; escalates consent, governance, and harm handling.
- **Formality register** — working draft, committee-ready, publication-ready.

## Canonical Epistemic Stances (42)

Select a primary stance; most researchers combine a primary with one or two
secondary influences.

Interpretive, Phenomenological, Hermeneutic, Ontological, Critical, Political
economy / Marxian, Critical race, Critical medical, Postcolonial, Feminist,
Queer theory, Decolonial, Indigenous methodologies, STS / actor-network,
Multispecies / more-than-human, Infrastructure studies, Environmental /
political ecology, Practice theory, Performance / performativity, Cognitive,
Psychological, Linguistic, Semiotic, Applied / evaluation, Design
anthropology, Business / organizational, Public / engaged, Mixed-methods,
Computational / digital, Visual / sensory, Historical / archival, Multi-sited,
Structuralist / post-structuralist, Psychoanalytic, Narrative / life history,
Affect theory, Material culture / object-oriented, Economic anthropology,
Legal / rights-based, Medical / health (interpretive), Migration / mobility
studies, Anarchist / anti-authoritarian.

For method compatibility by stance family, see the methodology-selection
skill's `references/method-stance-compatibility.md`.

## Terminology Note: Stance vs. Analytical Lens

The toolkit's computational notebooks (Codebook Builder, Coding and Thematic
Analysis) expose the same framework under the label **analytical lens**,
because several registry entries (Business/Organizational, Mixed-methods,
Evaluation) are not epistemologies in the strict philosophical sense. The
notebook LENS_REGISTRY uses compact labels — e.g., "STS/Actor-Network" for
STS / actor-network, "Interpretive" for interpretive — but the two lists
describe the same design parameter. Skills say "epistemic stance"; notebooks
say "analytical lens"; a codebook generated under a lens can be read by any
skill as a stance commitment.

## Lifecycle Coverage

Skills are organized by research lifecycle phase (see README.md for the
per-skill table): research design → ethics & compliance → fieldwork → funding
→ analysis → writing & review → dissemination → career. The
qualitative-analysis skill bridges the plugin to the toolkit's computational
notebooks (Semantic Chunker → Codebook Builder → Coding and Thematic
Analysis).

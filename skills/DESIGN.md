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
- Cross-plugin handoffs — to companion plugins that own a capability this
  library deliberately does not duplicate — live in the SKILL.md body, never
  in the description, so companion plugins keep winning their own routing
  triggers. The handoff names the companion's capabilities rather than its
  versions or tool counts, checks for the companion's presence in the
  session, and carries a fallback for when it is absent (an install pointer
  plus whatever this library can do alone).
- SKILL.md bodies follow a shared skeleton: Quick Reference → Workflow →
  Parameters → Guardrails → Common Failure Modes → Examples. Skills adopting
  the Friction by Design conventions at Tier 1 insert What This Skill Will
  and Will Not Do and Calibrating the Depth immediately after Quick
  Reference; the remaining sections follow as usual (see Friction by Design,
  below).
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

### Carrying the parameters

Declaring the parameters shared is not the same as sharing them. Before this
convention, one parameter had a carrier and the rest did not: the depth
setting is asked once by the advisor at dispatch and passed into every skill
invocation, and a skill that receives it does not re-ask. Everything else was
re-elicited by each skill in turn, which is how a researcher ends up stating
their epistemic stance three times in one engagement.

The convention generalizes that carrier to the whole framework.

**Establish only what the current work needs, when it needs it.** Not all six
parameters bear on every engagement. Collecting them as an opening
questionnaire is the failure mode the framework names elsewhere, the gate that
becomes a form, and it puts intake between the researcher and the work they
came to do.

**Infer and confirm wherever the material supports it.** A draft, a research
question, or a description of a fieldsite usually carries the stance, the
genre, and the field configuration. Proposing what was read and asking one
confirm-or-revise question is faster than asking, and it is more accurate,
because researchers describe their own stance in the vocabulary of whoever
taught them. Ask outright only where the material does not support an
inference. This is the legitimate inference already named under depth
calibration, applied to the rest.

**Carry what is established, and do not re-ask it.** The agent is the carrier,
the same role it holds for the depth setting. A skill activated directly,
outside any agent, establishes for itself what it needs.

**Career stage calibrates scaffolding, not authority.** It sets how much is
explained and how much is assumed, never how much the researcher's judgment is
worth. It is never inferred from how confidently someone writes: fluency about
one's own material is not seniority, and a postdoc entering an unfamiliar
subfield needs more scaffolding than a fourth-year doctoral student in their
own.

**Say which parameter drove an output when it drove one.** Where a stance
determined a method recommendation or a risk posture determined a consent
approach, name it. A researcher who can see which parameter moved the output
can correct the parameter rather than arguing with the output.

## Friction by Design

The toolkit's design philosophy: build deliberate resistance into AI-assisted
research at the points where a researcher's judgment could otherwise be
displaced. Placed well, friction is what keeps the researcher the author of
the judgments that make the work theirs. The claim is placement, not
quantity — three stops in the right places beat fifteen, and logistics
(installing, invoking, re-running) are never where judgment lives.

The philosophy has two layers.

**Analytic friction.** Divergence between machine readings, and between
machine readings and the researcher's own, sustained as data rather than
resolved as noise: multiple analytical lenses run in parallel, disagreement
surfaced as friction points, convergence tagged rather than assumed
(Artz 2026c). It is operationalized in the analysis pipeline (cross-lens
comparison, friction reports) and governed by the
digital-computational-methods and qualitative-analysis skills. Slowing
reasoning down with machine friction is a documented technique in its own
right (Madsen, Munk, and Søltoft 2023); this library inherits that technique
and does not rename it. Full citations live in
`digital-computational-methods/references/relationship-framework.md`.

**Interactional friction.** The same philosophy applied to the interaction
between researcher and machine: gates and questions that withhold production
where a judgment is not the machine's to make. It has five elements, each
with a canonical form:

1. **Division of labour.** A section headed
   `## What This Skill Will and Will Not Do`, carrying two bolded lead-ins.
   `**Will not do, under any setting.**` lists the judgments that belong to
   the researcher, stated for that skill specifically, and closes with why:
   an output whose judgments came from elsewhere is one the researcher
   cannot defend. When asked for one of these directly, the skill proposes
   options and asks which; it does not decide, and it does not lecture.
   `**Will do, on request.**` lists the assembly work — formatting,
   restating the researcher's own answers, listing what remains unresolved —
   and anything produced this way is marked in the output.
2. **Depth calibration.** A section headed `## Calibrating the Depth`: a
   full pass, where the skill stops at each decision, or an advisory pass,
   where it raises what it sees and the researcher directs. Asked once at
   the start of an engagement, not once per skill activation when several
   skills run inside one session — and the carrier of that "once" is the
   advisor agent: an agent whose engagement will use a Tier 1 skill asks at
   dispatch and passes the setting into every skill invocation, and a skill
   that receives a setting does not re-ask. A skill activated directly,
   outside any agent, asks for itself. Skills with a declared variance keep
   their documented default either way. The depth setting is never inferred
   from how confident someone sounds. Inferring and then confirming a
   substantive parameter, such as epistemic stance, is a different act and
   remains legitimate.
3. **Questioning over production.** Where the researcher's judgment is the
   deliverable, the skill proceeds by questioning rather than by producing:
   one high-leverage question at a time. Two boundaries keep this honest.
   Anti-batching applies to decisions, not facts — project facts (field
   configuration, scale, access, resources) may be collected together;
   batching decision questions is what turns a dialogue into a form.
   Anti-atomizing forbids the reverse failure: one decision is one question,
   and a classification is one table with one confirm-or-revise question,
   not nine questions the researcher stops reading.
4. **Record registers.** Output artifacts carry an Unresolved list, which
   must not be tidied — an artifact with nothing unresolved after a full
   pass has usually been tidied rather than finished — and an "Assembled
   rather than authored" register marking what the machine supplied on
   request as distinct from what the researcher decided. Several skills
   already carry instances of this register under other names: the
   AI-assistance disclosure in literature-review, the evidence-versus-
   extrapolation marking in applied-practice, the provenance rules in
   qualitative-analysis, the instrument-adaptation documentation in
   fieldwork-methods. The register names and unifies existing practice.
5. **Method-facing failure modes.** An adopting skill's failure modes
   include failures of this framework itself, not only failures of the
   output. The canonical three: the gate that becomes a form (people learn
   which answers let a stage proceed); friction added to look rigorous
   (quantity mistaken for placement); the interrogation that exhausts
   (questioning past usefulness produces abandonment). Each skill carries
   the ones that fit its work.

One further rule: what the framework gates is the decision, not the
conversation. Where a skill's method is
draft-and-react — produce an artifact early and revise against reactions —
the researcher's reaction to the artifact is an acceptable carrier of the
decision, and the skill documents that as its calibrated default instead of
asking the depth question. The variance is recorded in the adoption table
below.

### The builder-side counterpart

Friction by Design governs the loop of use: gates that route judgment to the
researcher. The same discipline has a builder-side form governing the loop of
building, stated as a working principle at the top of the repository's agent
files (CLAUDE.md, AGENTS.md, GEMINI.md) and binding any model working on this
repository before anything reaches a gate:

> Be adversarial toward your own output. Trust what survives an attempt to
> break it, and be most suspicious of what arrived easily.

This is earned confidence rather than hedging: test, then commit to what
survives, and be direct about it. It does not license performed doubt,
blanket qualification, or refusing to decide. A structural test holds the
principle's core sentences identical across the four files that carry it, and
the behavioral evals in `tests/evals/test_working_principle.py` sample
whether it is enacted rather than merely present.

### How each surface carries the philosophy

The toolkit runs on three surfaces, and friction takes the form each surface
can actually hold. The plugin's skills carry conversational gates — the
sections above. The MCP server and Python package carry analytic friction
natively (cross-lens comparison, friction points, per-code validation). The
Colab notebooks carry analytic friction the same way, and their
interactional layer is structural rather than conversational: execution is
cell-gated, every stage's output is reviewed before the next cell runs, and
ratification happens by editing the artifact between cells. A notebook that
interrogated its user would be ceremony; the cell boundary already stops
exactly where review belongs.

### Proportionality

Friction is proportional to what the researcher could plausibly get wrong,
not applied at uniform depth to everyone. Uniform adoption would itself be
the failure mode the framework names: a skill that formats a CV does not
interrogate its user. Adoption is therefore tiered, and a tier of none is a
legitimate assignment whose reason is recorded — friction not placed, and
why, is part of the account.

### Adoption tiers

- **Tier 1 — full framework.** All five elements. For skills where the
  researcher's substantive judgment is itself the deliverable.
- **Tier 2 — division of labour and record registers.** Elements 1 and 4
  only. For skills that produce documents from judgments largely already
  made, where some judgments still leak to the machine. No depth ceremony,
  no questioning protocol.
- **Tier 3 — none.** Genre mechanics over a factual record. Existing
  guardrails do the boundary work; added friction would be ceremony.

A skill declares its adoption with one line in the SKILL.md body, in this
form: "This skill adopts the Friction by Design conventions at Tier N."
The declarations, the table below, and the structural tests must agree.

| Skill | Tier | Reason, and any variance |
|---|---|---|
| tool-building | 1 | What an instrument is for, and what counts as correct, are the researcher's; the sort is an additional hard gate |
| paper-planning | 1 | The claim, the position, and the sequence are the author's |
| research-question | 1 | The question is the highest-leverage judgment in the lifecycle. Variance: proceeds draft-and-react; its two-question cap before producing a draft is its documented calibrated default, and full-pass probing runs against the drafted artifact |
| methodology-selection | 1 | Method choice is an argument that must survive reviewers. Intake of project facts stays batched; judgment-bearing moments are gates |
| qualitative-analysis | 1 | Machine judgment flows into findings by default through the pipeline; codebook ratification and theme confirmation are gates |
| ethnographic-generalization | 1 | What a case is a case of, the kind of generalization, the scope conditions, and the confidence level are inferential commitments only the researcher can sign |
| academic-review | 1 | A signed review is a non-delegable scholarly judgment |
| manuscript-markup | 1 | Which comments to accept, which to contest, and what a structural comment implies for the argument are the author's; the sort by kind is an additional gate |
| research-plan | 2 | Assembles judgments made upstream; what constitutes a finding, and the positionality statement, stay with the researcher |
| dissertation-prospectus | 2 | The committee document, not the design judgments, is the product; theoretical positioning stays with the researcher |
| grant-proposal | 2 | Funder compliance and genre rhetoric are legitimately assembled; aims and the contribution claim are not |
| fieldwork-methods | 2 | Instruments are corrected in piloting; sampling justification and observation domains stay with the researcher |
| informed-consent | 2 | Consent drafting is template work; the modality choice and what confidentiality can honestly be promised are not |
| irb-protocol | 2 | A regulated document the researcher signs; risk classification stays with the researcher |
| literature-review | 2 | Search and matrices are procedure; inclusion criteria and the gap statement are the argument |
| research-writing | 2 | Drafting prose from a decided argument is the work; the argument itself is gated in paper-planning |
| proof-review | 2 | Comparing proof against manuscript is mechanical verification and is run in full; whether a difference is an error, an acceptable house-style change, or a breach of an anonymization commitment, and whether the proof is approved, stay with the author. Depth ceremony would be noise on a diff, so uncertainty is routed to the author as a classification in the report rather than as an interruption mid-pass |
| digital-computational-methods | 2 | Register diagnosis is proposed and confirmed; sessions are short and consultative, so depth ceremony would be noise |
| applied-practice | 2 | The interpretation is the product the client bought; the so-what and what to withhold stay with the researcher |
| repeated-work | 2 | Sessions are short, consultative, and usually end without an instrument, so depth ceremony would be noise; whether a step is mechanical or interpretive stays with the researcher |
| career-statements | 2 | The through-line is a self-knowledge judgment; the skill proposes candidates and asks which is true |
| public-engagement | 2 | Public words appear under the scholar's byline; the take and the consent scope are the scholar's |
| job-materials | 3 | Genre mechanics over a factual record; honesty and voice guardrails already do the boundary work |
| conference-materials | 3 | Compressions of an argument decided elsewhere; limits and formats are rule-checkable |
| teaching-materials | 3 | Instructor-corrected scaffolding; classroom iteration is the corrective loop |

### Standing checks over durable artifacts

A researcher who would benefit from a standing check over their codebook or
their coded data does not ask for one, because they do not know that is the
name of the thing that would have saved them. So a skill that produces a
durable artifact runs the checks over it without being asked, and says in
one sentence what ran. This is the same reasoning that already licenses
test-first work in `tool-building`: judgment stops for the researcher, and
mechanics run smoothly without them.

**This convention takes no adoption tier and no row in the table above.**
Tiers attach to skills with a `SKILL.md`, and this is a cross-cutting
behavior with none. It inherits the tier of whatever skill it runs inside
and may never introduce a depth question of its own.

Three rules govern it.

**Running the checks is mechanics; answering a fired one is judgment.** A
fired check names a commitment the artifact implies. Whether that commitment
is the researcher's is theirs to say, and a skill that answers for them has
converted the finding back into a restatement of its own assumptions.

**A class-level check may assert formal properties of an artifact and may
never assert a methodological commitment about its use.** "Every code
carries a definition" is a property of a codebook. "No two codes overlap" is
a property of certain traditions' use of one, and grounded theory and
several interpretive traditions decline it. Checks of the second kind are
stance-gated: they run only once the researcher has said the commitment is
theirs, and they name the stance as the reason they ran.

**A quiet run is not an all-clear.** A check that could not run is reported
as unrun rather than passed, and a run in which nothing capable of surprising
anyone was executed is reported as such. What these are called, and why
anyone writes them, is worth saying once at the moment one first fires, and
not before.

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
Analysis) present the same framework as **analytical lenses** in user-facing
text, because several entries (Business / Organizational, Mixed-methods,
Applied / evaluation) are not epistemologies in the strict philosophical
sense. Internally the notebooks keep stance naming: the Codebook Builder
defines the lenses in a `STANCE_DEFINITIONS` dictionary with title-case
labels (e.g., "STS / Actor-Network") and exports codebooks with a `stance`
column. The two lists describe the same design parameter — skills say
"epistemic stance," notebook interfaces say "analytical lens," and a codebook
generated under a lens can be read by any skill as a stance commitment.

## Lifecycle Coverage

Skills are organized by research lifecycle phase (see README.md for the
per-skill table): research design → ethics & compliance → fieldwork → funding
→ analysis → writing & review → dissemination → career. The
qualitative-analysis skill bridges the plugin to the toolkit's computational
notebooks (Semantic Chunker → Codebook Builder → Coding and Thematic
Analysis).

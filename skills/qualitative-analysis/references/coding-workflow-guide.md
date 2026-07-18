# Coding Workflow Guide

Reference file for qualitative coding, codebook development, and thematic
analysis. Loaded by the qualitative-analysis SKILL.md when the user is
building a codebook, coding data, or constructing themes.

---

## Codebook Construction

### The five-part code

Every code entry needs all five parts before it enters the codebook:

| Part | Function | Failure when missing |
|------|----------|----------------------|
| Label | Short, distinctive handle (2-4 words) | Codes become interchangeable |
| Definition | What the code captures, in one or two sentences | Coders drift toward private meanings |
| Inclusion criteria | What qualifies a segment for this code | Over-application to loosely related material |
| Exclusion criteria | Near-misses that do NOT qualify, and where they go instead | Boundary disputes between adjacent codes |
| Example | At least one verbatim or realistic segment that earns the code | Definitions stay abstract and unapplicable |

### Sources of deductive codes

- The theoretical framework the project's stance makes relevant (concepts
  with established definitions in the literature)
- Prior codebooks from the same research program
- The research question's own terms, decomposed into observable expressions

Derive candidate codes from source literature systematically: for each key
text, extract the concepts it operationalizes, then consolidate across texts
before writing definitions. Record which source motivated each code — code
provenance is part of the audit trail.

### Worked example: codes from a named literature

What makes a code anthropological is that it names a cultural or relational
process from a literature, at the specificity the literature earns. Deriving
from the exchange literature (Mauss 1925; Sahlins 1972), a market-fieldwork
codebook gets:

| | Generic code | Anthropological code |
|---|---|---|
| Label | HELPING | RECIPROCITY_DEFERRED |
| Definition | Participant helps another person | Giving that creates an open obligation to return, with the return deliberately unscheduled (generalized reciprocity, Sahlins 1972) |
| Inclusion | Any assistance between participants | Transfers where repayment is expected but unstated, and pressing for it would damage the relationship |
| Exclusion | — | Simultaneous or negotiated exchange → RECIPROCITY_BALANCED; extraction without return expectation → RECIPROCITY_NEGATIVE |
| Example | "She helped her neighbor" | "He never charges the stallholders for repairs — 'they remember,' he says" |

The generic code could come from any discipline's project; the
anthropological codes carry a typology (generalized/balanced/negative), an
argument about obligation, and exclusion criteria that other codes in the
family absorb. The same move works from any literature the stance makes
relevant — ritual (liminality, communitas), kinship (fictive kin,
obligation), value, care, infrastructure.

### Consolidation before coding

Run the codebook through three checks before applying it to data:

1. **Semantic distinctness.** For every pair of codes, articulate a segment
   that fits one but not the other. If no such segment exists, merge them.
2. **Level consistency.** Codes should sit at a similar level of abstraction.
   "Resistance" next to "eye-rolling during safety briefings" signals a
   hierarchy (parent code + sub-code), not a flat list.
3. **Size cap.** 15-40 codes for most single-researcher projects. Beyond
   that, application consistency collapses. Prefer sub-codes under parents to
   flat sprawl.

### Versioning

Freeze a numbered codebook version before each coding pass. When inductive
discovery adds or splits codes, increment the version and record what
changed and why. Any coded segment must be interpretable against the
codebook version in force when it was coded; recode earlier material when a
definition changes materially.

---

## Coding Passes

### Deductive coding

Apply the frozen codebook to each segment. For each assignment, the
inclusion criteria must license it — "feels related" is not a criterion.
Permit multiple codes per segment; record all of them. When a segment
resists every code but seems analytically alive, mark it for the inductive
pass rather than forcing a fit.

### Inductive coding

After (or instead of) the deductive pass, ask what the codebook failed to
see. Candidate inductive codes must earn entry with the same five-part
structure, and must name something the data shows repeatedly or something
singular but analytically consequential. Resist inventing a code for every
interesting sentence — inductive coding is discovery under discipline.

### Hybrid integration

Complete deductive first, then inductive, then integrate: merge inductive
candidates into the codebook (new version), and re-examine segments coded
before the integration. Track each segment's status —

- `Deductive_Only` — existing codebook covered it
- `Inductive_Only` — only discovered codes apply
- `Both` — deductive and inductive codes co-apply
- `No_Codes` — nothing applies

The distribution of statuses is itself diagnostic: a corpus that is mostly
`Inductive_Only` says the literature-derived codebook missed the field; a
corpus with many `No_Codes` segments says either the segmentation is wrong
or the data includes material outside the research question's scope.

### Segmentation

Code meaning units: a claim, an exchange, an episode — not fixed word
counts, and not whole documents. If the data arrives unsegmented, segment
first by topic shift, never splitting inside a speaker's turn unless the
turn itself changes topic. Each segment carries: an identifier, source
document, speaker (if applicable), and position, so every later claim can be
traced back.

### What is being coded: data types carry different evidentiary weight

Ethnographic corpora are not homogeneous transcript streams, and coding
should track what kind of record each segment is:

- **Interview transcripts** record what people say about what they do —
  accounts, framings, justifications. Strong evidence for meaning and
  ideology; weak, on their own, for behavior.
- **Fieldnotes** are the researcher's own inscriptions, already
  interpretive at the moment of writing (Emerson, Fretz, and Shaw 2011):
  a jotting expanded hours later is a different evidentiary object than a
  verbatim quote captured in the moment, and in-process memos are analysis,
  not data — code them separately or not at all. Sanjek (1990) makes the
  fieldnote record itself the warrant of ethnographic validity: preserve
  the chain from jotting to expanded note to claim.
- **Artifacts and documents** (policies, posters, chat logs, objects
  photographed) evidence what circulates and what institutions assert —
  code them for what they are, not as if they were testimony.

Carry a record-type field per segment. When a theme rests mostly on one
record type ("all the evidence for this is what people *said*"), that is a
finding about the theme's standing, and the disconfirming-evidence search
should deliberately cross types.

### Co-occurrence

Record which codes appear together within segments. Recurrent
co-occurrences are theme candidates; unexpected co-occurrences (codes whose
definitions suggest they should repel) are analytic leads worth memo-ing.

---

## Theme Building

A theme is an analytical claim about patterned meaning that answers part of
the research question. For each theme, produce:

1. **The claim.** One sentence asserting something about the data — not a
   topic label. "Trust" is a topic; "health workers extend institutional
   trust only through named individuals, not roles" is a claim.
2. **Constituent codes.** Which codes, in which combinations, ground the
   claim.
3. **Evidence.** Verbatim quotes with segment identifiers. Two to four
   strong exemplars beat ten weak ones.
4. **Boundary.** What the theme does not cover, and known counter-examples.
5. **Contribution.** What the theme adds to the argument the project is
   making — which part of the research question it answers.

Sub-themes are permitted when a theme's claim has distinct variants; a theme
with more than four sub-themes is usually two themes.

### Multi-lens convergence tagging

When the same data has been coded under more than one stance/lens, tag each
theme:

- **Convergent** — the pattern surfaces under multiple lenses (robust across
  interpretive commitments)
- **Lens-specific** — visible only under one lens (a finding about what that
  lens uniquely reveals)
- **Friction** — lenses disagree about the same segments (a finding about
  the object's contested character; report the disagreement, do not average
  it away)

---

## Validation

- **Spot-check licensing.** Sample coded segments and verify each
  assignment against the code's inclusion criteria. Recode systematically if
  the error rate is material.
- **Disconfirming evidence.** For each theme, actively search the corpus for
  segments that undercut the claim. A theme that survives stated
  counter-evidence is defensible; a theme never tested against any is not.
- **Saturation reporting.** State when new data stopped yielding new codes,
  and what was still emerging at the analysis boundary. "We reached
  saturation" without this is a ritual phrase, not a finding.
- **Consistency across coders or passes.** When more than one coder (or an
  AI-assisted pass plus a human pass) codes the same material, compare
  assignments on a sample, discuss divergences, and revise definitions —
  agreement statistics are less important than the definitional repairs the
  comparison forces.

---

## Export Formats

| Format | Use | Must preserve |
|--------|-----|---------------|
| CSV / Excel | Audit, co-analysis, archiving | Segment ID, source, speaker, codes, status, codebook version |
| QDPX (REFI-QDA) | Transfer into NVivo, MAXQDA, ATLAS.ti | Codes with definitions, segment boundaries, source documents |
| Markdown / Word report | Committee and collaborator review | Theme claims, constituent codes, quoted evidence with identifiers |
| JSON | Downstream computational work | Full structure including analysis parameters and metadata |

When QDPX import fails in the target application (importers vary), fall back
to a manual import guide: codebook as a structured document plus coded data
as a spreadsheet keyed by segment ID.

---

## Citations

- Emerson, Robert M., Rachel I. Fretz, and Linda L. Shaw. 2011. *Writing
  Ethnographic Fieldnotes*. 2nd ed. Chicago: University of Chicago Press.
- Mauss, Marcel. 1925. *The Gift: Forms and Functions of Exchange in
  Archaic Societies*. (English trans., multiple editions.)
- Sahlins, Marshall. 1972. *Stone Age Economics*. Chicago: Aldine.
- Sanjek, Roger, ed. 1990. *Fieldnotes: The Makings of Anthropology*.
  Ithaca, NY: Cornell University Press.

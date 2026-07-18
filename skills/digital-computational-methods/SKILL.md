---
name: digital-computational-methods
description: >
  Use this skill whenever a user needs digital or computational research
  methods for anthropology — studying online communities and platforms,
  analyzing cultural material at computational scale, or deciding how to
  bring AI into the research relationship. Triggers include: "digital
  ethnography," "netnography," "study an online community," "subreddit,"
  "social media data," "trace data," "platform research," "topic
  modeling," "text network," "named entity recognition," "computational
  anthropology," "embeddings," "talk with my data," "should I use AI to
  analyze my data." Covers digital fieldwork design and platform ethics,
  and matching computational methods to corpus and question. Do NOT use
  for offline fieldwork instruments (use fieldwork-methods), broad
  method-stance alignment (use methodology-selection), or executing
  qualitative coding (use qualitative-analysis).
---

# Digital & Computational Methods

Guide research design across anthropology's three ways of working with
machines: studying digital technologies and the social worlds they
mediate, computing over cultural material at scale, and collaborating
with AI systems in analysis. These are relationships, not toolkits — the
same platform or model can be the object of study, an instrument of
analysis, or an interlocutor in interpretation, and the design
obligations differ in each case (Artz 2026, "A Call for an AI
Anthropology," General Anthropology 33(1)).

## Quick Reference

| Task | Reference |
|------|-----------|
| The three relationships, their history, and when each fits | Read [references/relationship-framework.md](references/relationship-framework.md) |
| Digital ethnography and netnography design, platform ethics | Read [references/digital-fieldwork-guide.md](references/digital-fieldwork-guide.md) |
| Matching computational methods to corpus and question | Read [references/computational-methods-guide.md](references/computational-methods-guide.md) |
| AI-collaborative analysis execution | Hand off to the qualitative-analysis skill |

## Workflow

### Step 1: Diagnose the Relationship

Before choosing methods, establish what relationship the project enacts
with the machine — read
[references/relationship-framework.md](references/relationship-framework.md)
for the framework and its disciplinary history:

1. **Studying it** — digital technology and its social worlds are the
   object: platform cultures, algorithmic systems, online communities,
   how people live with and through the digital. → Step 2.
2. **Computing with it** — computation is the instrument: analyzing
   cultural material (text, networks, media) at a scale manual reading
   cannot reach, on the researcher's instructions. → Step 3.
3. **Collaborating with it** — an AI system participates in the
   interpretive work itself: conversational, steered in real time, its
   divergent readings treated as analytically productive. → Step 4.

Projects are rarely one register from start to finish: a study *of* a
platform may compute over its trace data; computational results may feed
AI-collaborative interpretation. Re-diagnose at phase boundaries, and
name the register in the research design — each carries different
methodological and ethical obligations.

### Step 2: Design Digital Fieldwork (studying it)

Read [references/digital-fieldwork-guide.md](references/digital-fieldwork-guide.md)
before designing.

- Select sites by where the phenomenon lives, not platform convenience;
  document why this platform, these spaces, this period.
- Decide the presence stance — observation only, participation,
  announced researcher identity — and justify it ethically, not just
  practically. Publicness is not consent.
- Plan capture: what is recorded (posts, threads, screenshots,
  ephemera), how permanence and deletion are handled, what the platform's
  terms permit.
- Combine trace data with elicited data (interviews, walkthroughs) when
  the question concerns meaning rather than only behavior.
- Route consent design to informed-consent and protocol writing to
  irb-protocol; digital contexts change the answers, not the obligations.

### Step 3: Match Computational Methods (computing with it)

Read [references/computational-methods-guide.md](references/computational-methods-guide.md)
for method-by-method guidance and the toolkit notebooks that implement
each.

- Match method to material and question: topic modeling for exploring
  large corpora, named entity recognition for structured extraction,
  text networks for relational patterns in discourse, embedding
  similarity for organizing and comparing documents.
- Check scale honestly: below a few hundred documents, careful reading
  and qualitative coding usually beat computation — see the
  qualitative-analysis skill and its pipeline.
- Treat computation as extending interpretation, never replacing it:
  computational output is something to read, not a finding in itself.
  Validate by returning to the material — read the documents behind the
  topic, the passages behind the network edge.
- Report parameters and preprocessing: tokenization, thresholds, and
  model choices shape results and belong in the methods section.

### Step 4: Design AI Collaboration (collaborating with it)

When the project brings AI into interpretation itself:

- Keep interpretive authority with the researcher: AI proposes, the
  researcher adjudicates. The value of multiple machine readings lies in
  the divergence they sustain, not in resolving it automatically.
- Treat friction as data: when a system's reading of your material feels
  wrong in ways that clarify what you actually think, that
  disconcertment is an analytic event — record it, don't smooth it over.
- Two established patterns: multi-agent analysis under competing
  analytical lenses (execute through the qualitative-analysis skill and
  the toolkit pipeline), and conversational engagement with archived
  data through retrieval-augmented interlocutors (Søltoft, Kocksch, and
  Munk 2024).
- Document the collaboration as method: which system, which
  configurations, what it contributed, how its outputs were validated —
  AI participation is a methods-section fact, not a footnote.

## Guardrails

- **Publicness is not consent.** Visible data is not thereby fair game;
  platform terms, community norms, and member expectations all bind the
  design. When in doubt, route to irb-protocol.
- **Scale is not significance.** A pattern across a million posts is not
  automatically more meaningful than a pattern across ten interviews;
  the question determines the evidence that counts.
- **Computation extends interpretation; it does not replace it.**
  Anything a model outputs must survive a return to the material.
- **AI collaboration is disclosed, validated, and steered.** Never
  present machine-generated analysis as unassisted; never accept it
  without validation against the data.
- **Cite the published literature.** The framework here rests on
  published work — see the references files for the citation set.

## Common Failure Modes

**Register confusion.** Running a topic model does not make a project
computational anthropology, and using a chatbot does not make it
AI-collaborative research — the register is defined by the designed
relationship, not by which software appears in the workflow.

**Platform-convenience sampling.** Studying a subreddit because its data
is easy to collect, then generalizing to "online communities." Site
selection needs the same justification online as any field site.

**The big-corpus reflex.** "The corpus is large, so topic model it."
Method follows question; a large corpus with a meaning-centered question
may need sampling and close reading instead.

**Model output as ground truth.** Reporting topics, entities, or
clusters as findings without reading back into the material that
produced them.

**One-shot register diagnosis.** Designing the whole project in one
register and never revisiting it, when the work has actually shifted —
computing over data gathered ethnographically, or conversing with a
system built as an instrument.

## Examples

**Example 1: Online community study**

Input: "I want to study how a Discord server for migrant workers builds
mutual aid. Where do I start?"

Output approach: Register 1 (studying it). Read the digital-fieldwork
guide; design presence and consent for a semi-private community (Discord
is not public space); combine observation with member interviews; plan
capture around ephemerality; route consent design to informed-consent.
If the corpus grows large, revisit Step 3 for computational support.

**Example 2: Large corpus, exploratory question**

Input: "I scraped 40,000 forum posts about traditional medicine. How do
I analyze them?"

Output approach: Register 2 (computing with it). Check the question
first: for broad thematic terrain, topic modeling with validation by
close reading of exemplar posts; for who-and-what structure, NER; for
discourse relations, text networks. Then hand representative subsets to
the qualitative-analysis pipeline for interpretive coding — computation
to map the terrain, coding to read it.

**Example 3: AI in the analysis itself**

Input: "Can I have AI code my interviews under different theoretical
perspectives and compare the results?"

Output approach: Register 3 (collaborating with it). Multi-lens design
through the qualitative-analysis skill and toolkit pipeline; the
researcher adjudicates divergence between lenses and treats friction
points as findings; the collaboration is documented as method, with
validation and provenance throughout.

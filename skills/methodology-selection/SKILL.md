---
name: methodology-selection
description: >
  Use this skill whenever a user needs help selecting, justifying, or
  evaluating research methods for anthropological or qualitative research.
  Triggers include: any mention of "methods," "methodology," "method
  selection," "which methods should I use," "how to choose methods," "how
  do I justify my methods," "method-stance alignment," "my reviewer says my
  methods don't match my theory," "multi-method design," "mixed methods in
  anthropology," or "what methods fit an interpretivist / critical / STS /
  feminist / phenomenological / applied / cognitive / linguistic /
  computational project." Also trigger when users ask about epistemic
  coherence between theory and methods, evidence types needed for a research
  question, how to compose a multi-method system, how to write a methods
  justification narrative, or how to handle data governance as a design
  decision. Covers all anthropological subfields and qualitative social
  science approaches. Do NOT use for writing a full research plan (use
  research-plan skill), grant proposals targeting a specific funder (use
  grant-proposal skill), or designing specific instruments like interview
  guides or surveys (use fieldwork-instruments skill when available). This
  skill handles the upstream design decision of which methods and why.
---

# Methodology Selection

Select and justify research methods for anthropological research by treating
method choice as an epistemic-design problem: specifying a warranted path
from an epistemic stance and research question to defensible claims, using
evidence types the stance treats as meaningful, through a coherent
multi-method system whose internal logic is explicit. Method selection is
not "picking tools" — it is an argument about why these methods, for this
question, from this stance, will produce the evidence needed to support
the claims you intend to make.

## Quick Reference

| Task | Reference |
|------|-----------|
| Decision workflow, criteria, failure modes, checklist | Read [references/methodology-selection-guide.md](references/methodology-selection-guide.md) |
| Method-stance compatibility matrix, justification templates, worked examples | Read [references/method-stance-compatibility.md](references/method-stance-compatibility.md) |
| Method module details (evidence, claims, limitations, ethics), multi-method patterns | Read [references/method-modules.md](references/method-modules.md) |

## Workflow

### Step 1: Identify What the User Needs

Determine the entry point:

- **Selecting methods from scratch.** The user has a research question and
  stance but hasn't chosen methods yet. Load the guide and run the full
  decision workflow.
- **Justifying existing choices.** The user already has methods but needs
  help writing a defensible justification narrative. Load the compatibility
  map for stance-specific templates and the guide for phrasing patterns.
- **Checking stance-method coherence.** The user wants to know if their
  proposed methods fit their epistemic stance (often prompted by reviewer
  feedback). Load the compatibility map to check S/C/I/T ratings.
- **Writing a methods justification narrative.** The user needs proposal-ready
  or paper-ready prose explaining their method system. Load the compatibility
  map for stance-family templates and the guide for phrasing patterns.

### Step 2: Gather Context

Before generating any content, collect these inputs:

**Required:**
1. **Research question(s).** What is the user trying to answer? This
   determines what evidence is needed.
2. **Epistemic stance.** Which theoretical orientation(s) does the researcher
   work within? Ask for primary and secondary. The stance determines what
   counts as evidence and what methods are epistemically coherent.
3. **Field configuration.** Single site, multi-sited, digital, archival,
   hybrid? This constrains which methods are practical.

**Important but can be inferred:**
4. **Scale and temporality.** Small-N intensive, multi-population, longitudinal,
   cross-sectional? Affects the design logic.
5. **Access constraints.** Where observation is impossible or risky, trace and
   documentary methods become more central; where recruitment is constrained,
   sampling logic must shift.
6. **Risk posture.** Low-risk, vulnerable populations, high-surveillance,
   politically sensitive. Affects ethics and data governance requirements.
7. **Resources, skills, time.** Methods that cannot be implemented with rigor
   are not "best" methods. Short timelines may favor rapid assessment.

**Helpful but not required:**
- Downstream target: will this feed into a proposal, research plan, or paper?
- Career stage (affects ambition calibration)
- Language competencies
- Whether methods have already been partially chosen

### Step 3: Load Appropriate References

- **Always load** `references/methodology-selection-guide.md` for the
  decision workflow, criteria, and checklist.
- **Load** `references/method-stance-compatibility.md` when the user needs
  stance-specific guidance: compatibility ratings, justification templates,
  or worked examples.
- **Load** `references/method-modules.md` when comparing method options or
  composing a multi-method system: evidence types, claims supported,
  limitations, ethical considerations, and multi-method design patterns.

### Step 4: Run the Decision Workflow

Follow this sequence (detailed in the guide reference file):

1. **Define the claim envelope.** Based on the epistemic stance, state what
   kinds of claims are admissible and what kinds are not. An interpretivist
   project makes claims about meaning, not prevalence. A critical project
   makes claims about power, not neutral description.

2. **Decompose the question into evidence needs.** Translate the research
   question into required evidence types: embodied practices (requires
   observation), meaning-making (requires interpretive elicitation plus
   context), distributions (requires standardized measurement), discourse-in-use
   (requires recordings and transcription), historical sequence (requires
   archives), network/process across sites (requires multi-sited or trace
   strategies), materiality (requires object-oriented or sensory methods).

3. **Generate candidate method modules.** From the 14 method modules in the
   method-modules reference, identify which could produce the required evidence.

4. **Check epistemic coherence.** Using the compatibility matrix, rate each
   candidate method against the user's stance: Standard (S), Coherent (C),
   Innovative/defensible (I), or High-tension (T). Flag any T-rated methods
   and explain what reframing would be needed to make them defensible.

5. **Check field constraints.** Filter candidates by access, risk, consent
   feasibility, platform terms, legality, and resource availability.

6. **Compose the multi-method system.** Assign each surviving method a role:
   primary evidence generation, complementary perspective, contextualization,
   or validation. Ensure the system has internal logic — methods should relate
   to each other, not just coexist.

7. **Specify the integration plan.** State when and where evidence streams
   are joined, what analytic strategy governs integration, and what
   meta-inferences result. Do not use "triangulation" without specifying
   the type (data, method, theory) and what convergence or divergence means.

### Step 5: Generate Output

Produce one or more of these deliverables depending on user needs:

- **Method justification narrative.** Stance-grounded prose explaining the
  method system. Use the stance-family templates from the compatibility
  reference. Every method gets a role statement: what evidence it produces,
  what claims it supports, what its limitations are.
- **Method-system composition.** A structured overview of the method system
  showing each module, its role, its evidence contribution, and how it
  integrates with other modules.
- **Integration plan.** When and how evidence streams are combined, what
  analytic strategy governs integration, and what meta-inferences result.
- **Ethics and data governance plan.** Consent strategy, identifiability
  analysis, storage and embargo choices, platform-specific ethics for digital
  methods, and rules for future sharing.

### Step 6: Quality Check

Before presenting output, verify using the full checklist:

- [ ] Epistemic stance is named and the claim envelope is stated
- [ ] Each research question is translated into specific evidence needs
- [ ] Every method module has a role statement (evidence -> claim -> limitation)
- [ ] Each method is justified in relation to stance AND question, not as a
      generic disciplinary standard
- [ ] Sampling logic is specified and sample sizes are justified using
      information power or defensible saturation reasoning
- [ ] Implementation details are sufficient: sites, recruitment, instruments,
      recording, transcription, fieldnote protocols
- [ ] Integration plan is explicit for multi-method projects
- [ ] If computational methods: validation plan is specified
- [ ] If digital methods: internet-specific ethics are addressed
- [ ] Ethics and data governance plan is included
- [ ] Limitations and what the design cannot know are stated
- [ ] Timeline and feasibility are realistic
- [ ] If funder-required: data management and sharing plan is consistent with
      ethnographic ethics

## Parameters

- **Epistemic stance:** All 42 stances are relevant, grouped into stance
  families for compatibility mapping (interpretive/hermeneutic,
  phenomenological, critical/political economy, feminist/queer, STS/ANT,
  applied/design, cognitive/psychological, linguistic, computational/digital,
  plus an unspecified-family template). See DESIGN.md for the full list.
- **Genre/audience:** Methods section (for proposal, plan, or paper),
  standalone methodology design memo, methods justification narrative.
- **Compression:** Brief design sketch (1-2 paragraphs), methods rationale
  (1-2 pages), full methods section (3-8 pages).
- **Risk posture:** Low-risk, vulnerable populations, high-surveillance,
  politically sensitive. Higher risk postures require more detailed ethics
  and data governance.
- **Field configuration:** Single site, multi-sited, digital, archival,
  hybrid, comparative.
- **Scale:** Small-N intensive, multi-population, longitudinal,
  cross-sectional.

## Guardrails

- **Do not generate without knowing the epistemic stance.** Stance determines
  what counts as evidence, what methods are coherent, and what claims are
  admissible. "Methods" without a stance is an incoherent request — ask
  the user to identify their stance before proceeding.
- **Do not produce methods as a grocery list.** Every method must have a
  role statement: what evidence it produces, what claim it supports, what
  its limitation is. "I will use participant observation, interviews, and
  surveys" is a failure mode unless each method's contribution is specified.
- **Do not claim triangulation without specification.** Require the type of
  triangulation (data, method, theory) and state what convergence or
  divergence would mean for inference. "Triangulation" as a magic word is
  a documented failure mode.
- **Flag stance-method tension explicitly.** When a proposed method is rated
  High-tension (T) for the user's stance in the compatibility matrix,
  explain the tension and what reframing would be needed. Do not silently
  pass high-tension combinations.
- **Ethics and data governance are design determinants.** Do not treat them
  as an appendix. Risk, identifiability, consent feasibility, and future
  harms from data circulation must inform method selection, not just
  accompany it.
- **Require validation for computational methods.** If computational text
  analysis, network analysis, or other automated methods are included,
  require a validation plan (close reading, triangulation, error analysis).
  Model outputs are not self-validating.
- **Require internet-specific ethics for digital methods.** If digital
  ethnography, trace methods, or platform-based research is included,
  require explicit treatment of public/private ambiguity, searchability
  of identifiers, platform terms, and consent expectations.

## Common Failure Modes

| Failure mode | Prevention |
|---|---|
| Methods as grocery list — no inferential role specified | Require a role statement per method: evidence -> claim -> limitation |
| Generic justification — "participant observation is a hallmark of anthropology" | Enforce stance-and-question anchoring: why this method is necessary here |
| Stance-method mismatch hidden by vague language | Add claim envelope step; check compatibility matrix; flag T-rated methods |
| Integration left implicit — "triangulation" as magic word | Specify type of triangulation and what convergence/divergence means |
| Sample size by round number or unexamined "saturation" | Use information power or empirically grounded saturation reasoning |
| Ethics treated as appendix | Require ethics and data governance as design determinants, not afterthoughts |

## Examples

**Example 1: Selecting methods for an interpretivist project**

Input: "I'm studying how gig workers make meaning out of algorithmic
management. I'm an interpretivist drawing on practice theory. What methods
should I use?"

Output approach:
- Load all three reference files
- Set epistemic stance to interpretivist + practice theory
- Claim envelope: meaning-making, practice-account relations, situated
  explanation — not prevalence or causal measurement
- Evidence needs: embodied practices (observation), interpretive frames
  (interviews), institutional categories (documents)
- Method system: participant observation (ride-alongs, waiting spaces) +
  semi-structured interviews + document analysis (platform communications,
  worker forums as texts) — all S or C rated for interpretive stance
- Integration: observation builds domain knowledge and refines interview
  guides; interviews test interpretive hypotheses; documents trace category
  circulation; iterative qualitative analysis across all streams
- Role statements for each method

**Example 2: Selecting methods for a computational/digital project**

Input: "I want to study how climate misinformation spreads in online
communities. I'm coming from a computational/digital ethnography perspective.
I'm thinking of scraping forum data and doing topic modeling."

Output approach:
- Load all three reference files
- Set epistemic stance to computational/digital
- Claim envelope: pattern identification at scale, platform-mediated practices,
  distributed coordination
- Check forum scraping + topic modeling: both S-rated for computational/digital
  stance, but require validation plan
- Recommend adding digital ethnography (community engagement, contextual
  interpretation) to ground computational findings — S-rated, standard
  integration pattern
- Require: validation through close reading, participant engagement for
  interpretation, internet-specific ethics (consent, searchability,
  platform terms)
- Flag: scraping without ethical governance plan is a guardrail violation

**Example 3: Checking stance-method coherence**

Input: "I'm doing a feminist study of reproductive healthcare access but my
advisor wants me to include a survey. Is that compatible with my framework?"

Output approach:
- Load compatibility reference
- Check surveys against feminist/queer stance: rated C (coherent, not
  standard) — epistemically compatible but requires explicit framing
- Explain: surveys are coherent within feminist frames when they
  operationalize structural exposure (access barriers, wait times,
  insurance status) and are integrated with ethnographic interpretation,
  not used as standalone "proof"
- Recommend framing: position survey as mapping the distribution of
  structural barriers that ethnography then explains in terms of lived
  experience and power; include critical analysis of what the survey
  categories make visible and invisible
- Flag: surveys become high-tension if treated as neutral measurement
  without feminist critique of the categories themselves

---
name: dissertation-prospectus
description: >
  Use this skill whenever a user needs help writing, drafting, revising, or
  structuring a dissertation prospectus, dissertation proposal, qualifying exam
  proposal, upgrade document, transfer document, or fieldwork clearance proposal
  for anthropological research. Triggers include: any mention of "prospectus,"
  "dissertation proposal," "qualifying exam," "QE," "upgrade proposal,"
  "transfer of status," "confirmation of status," "fieldwork proposal," or
  "fieldwork clearance" in the context of anthropology or ethnographic research;
  requests to structure, draft, or revise any section of a dissertation proposal
  (problem statement, research questions, theoretical positioning, literature
  review, methods, ethics, timeline, budget); questions about what a committee
  expects or how to prepare for a prospectus defense or upgrade viva. Also use
  when the user says "I need to write my prospectus," "I'm preparing for my
  qualifying exam," "how do I structure a dissertation proposal," or "what
  should my prospectus include." Covers US prospectuses (Berkeley, Harvard, and
  other programs), UK upgrade/transfer/fieldwork proposals (LSE, Cambridge,
  Oxford), and dual-purpose prospectuses that also serve as grant applications.
  Do NOT use for standalone grant proposals without a committee audience (use
  grant-proposal skill), general academic paper writing (use academic-paper
  skill), or research question development without a prospectus context (use
  research-question skill).
---

# Dissertation Prospectus Writing

Write dissertation prospectuses and proposals for anthropological research that
satisfy both committee expectations (intellectual coherence, feasibility,
scholarly preparation) and — when dual-purpose — funder requirements
(compliance, risk mitigation, credible execution). The strongest prospectuses
are modular: adaptable into a committee document, a fundable grant narrative,
and an ethics dossier without full rewrites.

## Quick Reference

| Task | Reference |
|------|-----------|
| Full prospectus guidance (sections, length norms, evaluation criteria, examples) | Read [references/prospectus-guide.md](references/prospectus-guide.md) |
| NSF DDRIG-specific requirements (if dual-purpose) | Load from grant-proposal skill: `references/nsf-cultural-anthro.md` |
| Wenner-Gren-specific requirements (if dual-purpose) | Load from grant-proposal skill: `references/wenner-gren.md` |
| Fulbright-specific requirements (if dual-purpose) | Load from grant-proposal skill: `references/fulbright.md` |

## Workflow

### Step 1: Identify What the User Needs

Determine the entry point:

- **Writing from scratch.** The user has a topic and needs to build a full
  prospectus. Load the full reference file and work through sections in order.
- **Revising an existing draft.** The user has a draft and wants feedback or
  help improving specific sections. Identify which sections need work and load
  the relevant guidance from the reference file.
- **Adapting format.** The user has a prospectus for one context and needs to
  adapt it for another (e.g., committee prospectus → NSF DDRIG application).
  Load both the prospectus reference and the relevant funder reference.

### Step 2: Gather Context

Before generating any content, ask for these required inputs:

1. **Program and milestone.** Which institution? Which milestone (US qualifying
   exam, UK upgrade/transfer, UK fieldwork clearance, other)? This determines
   length norms, required components, and evaluation criteria.
2. **Research topic and site(s).** What is the project about and where will
   fieldwork occur?
3. **Epistemic stance.** Which theoretical orientation(s) does the researcher
   work within? Ask which is primary and which are secondary.
4. **Target funder (if dual-purpose).** Is this prospectus also serving as the
   basis for an NSF DDRIG, Wenner-Gren, Fulbright, or other application?
5. **Stage of development.** Starting from scratch, refining a draft, or
   adapting to a different format?

Helpful but not required: theoretical framework, preliminary fieldwork or
pilot data, language competencies, committee composition, timeline constraints.

### Step 3: Load Appropriate Reference

Always load `references/prospectus-guide.md` for the full section-by-section
guidance, length norms, evaluation criteria, and examples.

If the user is writing a dual-purpose document, also load the relevant funder
reference from the grant-proposal skill to ensure the prospectus satisfies
both audiences simultaneously.

### Step 4: Generate Output

Follow the section structure and proportional allocations in the reference
file. Key principles:

- **Modular design.** Each section should work both for the committee and for
  potential funder adaptation.
- **Theory as leverage.** Theoretical positioning shows what conceptual work
  becomes possible, not just allegiance to a framework.
- **Methods as inferential design.** Specify evidence, justify the site-method
  pairing, and show how analysis proceeds.
- **Ethics as first-class content.** Address consent modality, community
  obligations, and data protection substantively — not as boilerplate.
- **Contingency planning.** Include a Plan B methodology.
- **Match length and format norms.** US prospectuses range from 8-10 pages
  (Berkeley) to 25-30 pages (Harvard). UK proposals range from 7,000 to
  20,000 words depending on milestone.

### Step 5: Quality Check

Before presenting output, verify:

- Research questions are fieldwork-operational AND theoretically motivated
- Theoretical positioning shows leverage, not just allegiance
- Literature review is selective, problem-centered, and multi-tradition
- Methods section specifies evidence, justifies site-method pairing, and
  includes analysis plan
- Ethics section addresses consent modality, community obligations, and
  data protection substantively
- Timeline includes pre-fieldwork workstreams
- Budget is itemized and connected to the evidence plan
- Contingency plan is present
- Tone is confident without overclaiming
- Output matches the user's program length and format requirements
- Epistemic stance is reflected consistently throughout
- If dual-purpose: all funder-specific requirements are met

## Parameters

- **Epistemic stance:** All 42 stances are relevant. Most dissertations combine
  a primary and one or more secondary stances.
- **Genre/audience:** Committee prospectus, dual-purpose prospectus + grant,
  UK upgrade/transfer, UK fieldwork clearance.
- **Compression:** 8-10 pages (short US), 20-30 pages (long US), 7,000-20,000
  words (UK, varies by milestone).
- **Risk posture:** Low-risk, vulnerable populations, high-surveillance,
  politically sensitive.
- **Formality register:** Disciplinary (default for committee audiences).
- **Field configuration:** Single site, multi-sited, digital, archival, hybrid.

## Guardrails

- **Do not generate content without knowing the program and milestone.** Length
  norms, required components, and evaluation criteria differ significantly
  between US and UK programs and between institutions. Ask first.
- **Do not produce ethics sections that are boilerplate.** Ethics must address
  the specific consent modality, community obligations, and data protection
  concerns relevant to the project. If the risk posture is elevated, ethics
  protections must match.
- **Do not omit contingency planning.** All prospectuses should include a
  Plan B methodology, even when not formally required.
- **Flag dual-purpose tension.** When a prospectus serves both committee and
  funder audiences, flag any points where their expectations diverge (e.g.,
  NSF requires falsifiable questions; committees may accept more interpretive
  framing).
- **Do not overclaim.** Epistemic humility about what the research will and
  will not be able to show is a mark of sophistication.

## Common Failure Modes

| Failure mode | Prevention |
|---|---|
| Overbreadth — too many questions, none convincing | Limit to 2-4 tightly articulated questions |
| Ethics as afterthought — perfunctory section | Make ethics a workflow step throughout |
| Vague analysis plan — "I will use thematic analysis" | Specify coding approach, triangulation, what constitutes a claim |
| Methods as menu — lists techniques without logic | Frame as inferential design generating specific evidence |
| No contingency — assumes everything goes to plan | Include Plan B with alternative methods and claim limitations |
| Answers already known — telegraphs conclusions | Frame genuinely open questions; acknowledge uncertainty |
| Generic literature review — lists without argument | Make the review an argument about where this project intervenes |
| Mission mismatch — description without theory contribution | Connect every methods choice to a theoretical claim |

## Examples

**Example 1: US sociocultural prospectus (Berkeley-style)**

Input: "I'm writing my prospectus for my QE at Berkeley. My project is about
how Senegalese migrants in Paris use WhatsApp groups to maintain translocal
kinship networks. I work within an interpretivist framework drawing on practice
theory and digital anthropology."

Output approach:
- Load `references/prospectus-guide.md`
- Set length to 8-10 pages (Berkeley tight format)
- Set epistemic stance to interpretivist + practice theory
- Set field configuration to multi-sited (Paris + digital + Senegal)
- Methods: participant observation in WhatsApp groups, life history interviews,
  multi-sited fieldwork logic
- Analysis: iterative coding with practice-theoretical categories

**Example 2: UK fieldwork proposal (Cambridge-style)**

Input: "I need to write my fieldwork proposal for Cambridge clearance. My
research examines Indigenous water governance in Bolivia's Altiplano. I work
within decolonial and political ecology traditions."

Output approach:
- Load `references/prospectus-guide.md`
- Set length to 7,000 words
- Set epistemic stance to decolonial + political ecology
- Set risk posture to politically sensitive + Indigenous communities
- Methods: foreground community authority, reciprocity, Indigenous knowledge
  sovereignty; include CARE Principles for data management
- Flag: separate risk assessment form also needed

**Example 3: Dual-purpose prospectus + NSF DDRIG**

Input: "I'm writing my dissertation prospectus and I also want to adapt it for
my NSF DDRIG application. My project studies algorithmic hiring systems in tech
companies from an STS perspective."

Output approach:
- Load `references/prospectus-guide.md` AND `nsf-cultural-anthro.md`
- Generate committee prospectus first, then flag NSF-specific adaptations
- NSF requires labeled intellectual merit and broader impacts sections,
  falsifiable questions, explicit analysis plan, data management plan
- Frame STS questions with falsifiable stakes for NSF audience

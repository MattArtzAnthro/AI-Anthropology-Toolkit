---
name: informed-consent
description: >
  Use this skill whenever a user needs help designing informed consent
  processes or documents for qualitative or anthropological research. Triggers
  include: any mention of "informed consent," "consent form," "consent
  process," "information sheet," "study information sheet," "participant
  consent," "verbal consent," "oral consent," "community consent," "consent
  for recording," "consent for photos," "consent for video," "media consent,"
  "ongoing consent," "process consent," "iterative consent," "re-consent,"
  "consent waiver," "waiver of documentation," "consent template," "consent
  language," "consent for minors," "assent form," "guardian consent,"
  "culturally appropriate consent," "consent in low-literacy settings,"
  "consent for longitudinal research," "consent for multi-site research," or
  "consent checklist." Covers designing consent processes (written, verbal,
  community-based, tiered), writing consent forms and information sheets,
  cultural adaptation, media and recording consent, and consent for special
  populations and contexts. Do NOT use for full IRB protocol narratives (use
  irb-protocol skill), methodology selection (use methodology-selection
  skill), or data management plans (use irb-protocol skill for DMP guidance
  within a protocol context).
---

# Informed Consent Design

Design informed consent processes and documents for qualitative
anthropological research that respect both regulatory requirements and the
relational, iterative reality of ethnographic fieldwork. Consent in
anthropology is an ongoing negotiated conversation, not a one-time signature
event. The skill treats consent design as a translation problem: making
ethical commitments legible to participants, reviewers, and institutions
simultaneously.

Contemporary best practice recognizes that the quality of consent — whether
participants genuinely understand what they are agreeing to and feel free to
say no — matters more than the format. A signed form that participants do not
understand is worse than an oral conversation that they do. This skill helps
researchers design consent processes that are ethically robust, culturally
appropriate, and institutionally defensible.

**Cross-references:** For full IRB protocol narratives that include consent
as one section among many, use the [irb-protocol](../irb-protocol/) skill.
The irb-protocol skill covers consent within the broader protocol context;
this skill focuses specifically on designing the consent process and its
documents in depth.

## Quick Reference

| Task | Reference |
|------|-----------|
| Regulatory foundations, consent modes, essential elements, cultural adaptation, power dynamics, documentation | Read [references/consent-design-guide.md](references/consent-design-guide.md) |
| Consent form templates, sample wording, checklists, flowcharts, media consent, special contexts | Read [references/consent-templates-and-examples.md](references/consent-templates-and-examples.md) |

## Workflow

### Step 1: Identify What the User Needs

Determine the entry point:

- **Designing a consent process from scratch.** The user has a research
  design and needs to determine the appropriate consent approach (written,
  verbal, layered, community-based) and produce the associated documents.
  Load both reference files.
- **Writing a consent form or information sheet.** The user knows what consent
  approach they need and wants help drafting the actual document. Load the
  templates reference for modular text blocks and sample wording.
- **Adapting consent for a specific context.** The user has a standard consent
  form but needs to adapt it for low-literacy populations, a specific cultural
  context, minors, or another special circumstance. Load the design guide for
  cultural adaptation and power dynamics.
- **Adding media/recording consent.** The user needs consent language for
  audio recording, video recording, photography, or participant-generated
  media. Load the templates reference for tiered media consent options.
- **Designing consent for longitudinal or multi-site research.** The user
  needs re-consent strategies, multi-site adaptations, or international
  compliance. Load both references.
- **Responding to IRB feedback on consent.** The user's consent documents were
  flagged by reviewers. Identify the specific concern and load relevant
  guidance to address it.

### Step 2: Gather Context

Before generating any content, collect these inputs:

**Required:**
1. **Research methods.** What methods will be used? Interviews, participant
   observation, focus groups, oral history, visual methods, digital
   ethnography? Different methods trigger different consent requirements
   (e.g., recording consent, group confidentiality limits, ongoing consent
   for observation).
2. **Participant population.** Who are the participants? Are there vulnerable
   populations (minors, prisoners, patients, employees)? What is the literacy
   level? What languages are spoken? Are there cultural norms around
   agreements and documentation?
3. **Risk level.** Minimal risk or elevated? Sensitive topics (health, legal
   status, political activity)? This determines how detailed the consent
   process needs to be and whether additional safeguards are required.

**Important but can be inferred:**
4. **Consent modality preference.** Written, verbal with waiver of
   documentation, layered/tiered, community-level? If unspecified, recommend
   based on methods, population, and context.
5. **Recording plans.** Audio, video, photo, screenshots? Separate consent
   for recordings is usually required and should be tiered (participate
   without recording as an option).
6. **Institutional context.** U.S. Common Rule, Canadian TCPS 2, EU/GDPR, or
   other? This determines regulatory requirements and available consent
   waivers.
7. **Data sharing or archiving plans.** Will data be archived, shared, or
   deposited? Consent language must match downstream data use.

**Helpful but not required:**
- Field site characteristics (public vs private spaces, organizational vs
  community settings)
- Whether community-level authorization is culturally expected or required
- Prior consent documents that need revision
- Specific IRB feedback to address
- Whether the project involves Indigenous communities (triggers CARE, OCAP,
  FPIC frameworks)

### Step 3: Load Appropriate References

- **Always load** `references/consent-design-guide.md` for regulatory
  foundations, consent mode selection, essential elements, cultural
  adaptation, and documentation requirements.
- **Always load** `references/consent-templates-and-examples.md` when the
  user needs to produce actual consent documents — forms, information sheets,
  oral consent scripts, media consent, or checklists.
- **Load both** for most tasks. The design guide provides the framework; the
  templates provide the implementation.

### Step 4: Generate Content

Follow the consent design framework from the guide reference:

1. **Select consent mode.** Based on methods, population, risk, and cultural
   context, determine the appropriate consent approach: written consent form,
   verbal consent with information sheet, layered/tiered consent, community
   consent plus individual consent, or a combination.
2. **Draft key information section.** The opening of any consent document
   should present the essential information concisely: what the study is
   about, what participation involves, main risks, main safeguards,
   voluntariness.
3. **Build the full document.** Using the template structure from the
   templates reference, draft each section: purpose, procedures,
   voluntariness, risks/benefits, confidentiality, recordings, data use,
   withdrawal, contacts.
4. **Add method-specific elements.** Recording consent (tiered), focus group
   confidentiality limits, observation consent (primary vs incidental),
   visual methods rights and ownership, digital ethnography quoting policies.
5. **Adapt for context.** Plain language, translation, cultural norms,
   literacy level, power dynamics, community authorization processes.
6. **Design the consent process.** The document is one part; also design when
   and how consent will be obtained, how it will be revisited, and what
   triggers re-consent.

### Step 5: Generate Output

Produce one or more deliverables depending on user needs:

- **Written consent form.** Full consent document for participant signature,
  with all required elements and method-specific additions.
- **Information sheet.** Standalone document for use with verbal consent
  (waiver of documentation). Provides all information without requiring a
  signature.
- **Oral consent script.** Structured script for obtaining and documenting
  verbal consent, including a witness protocol.
- **Tiered media consent.** Separate consent for audio, video, and/or
  photography with graduated options (participate without recording, record
  for analysis only, record for publication).
- **Community consent protocol.** Process for obtaining community-level
  authorization alongside individual consent.
- **Re-consent protocol.** Strategy for longitudinal or evolving studies,
  specifying when and how consent will be revisited.
- **Consent process design.** Complete consent strategy document describing
  the approach, rationale, timing, and documentation plan — suitable for
  inclusion in an IRB protocol or methods section.
- **Adapted consent materials.** Consent documents tailored for specific
  populations (minors with assent + guardian consent, low-literacy with
  visual aids, translated materials).

### Step 6: Quality Check

Before presenting output, verify:

- [ ] The consent document covers all essential elements: purpose, procedures,
      voluntariness, risks/benefits, confidentiality, data use, withdrawal,
      contacts
- [ ] Language is plain and jargon-free — a participant with no research
      background should understand every sentence
- [ ] The consent mode matches the context: written consent is not imposed
      where verbal would be more appropriate (and vice versa)
- [ ] Recording consent is separate and tiered: participants can say yes to
      the study but no to recording
- [ ] Focus group consent acknowledges that confidentiality cannot be
      guaranteed among participants
- [ ] Confidentiality promises are accurate — not overpromised (e.g., "we
      cannot guarantee absolute anonymity" where relevant)
- [ ] Consent is framed as a process, not a one-time event — ongoing consent
      checkpoints are specified
- [ ] Power dynamics are addressed: participants have genuine agency to
      refuse without consequences
- [ ] Cultural adaptation is appropriate: format, language, and process
      reflect participants' norms and expectations
- [ ] Data sharing/archiving consent matches the actual plan — consent
      language does not promise more restriction or more openness than
      what will happen
- [ ] The document meets institutional requirements (Common Rule, TCPS 2,
      EU guidelines, or other applicable framework)
- [ ] Documentation plan is specified: how consent will be recorded, stored,
      and archived

## Parameters

- **Consent mode:** Written (signed form), verbal with waiver of
  documentation (information sheet + oral agreement), layered/tiered
  (graduated options for different aspects), community-level (collective
  authorization + individual consent), recorded oral consent (audio-documented
  verbal agreement). Choice depends on risk level, cultural context, literacy,
  and institutional requirements.
- **Methods requiring consent:** Interviews (standard), focus groups
  (confidentiality limit), participant observation (primary vs incidental),
  oral history (attribution vs anonymity), visual methods (media rights),
  digital ethnography (platform-specific). Each method adds specific consent
  elements.
- **Population characteristics:** General adult population, minors (assent +
  guardian consent), low-literacy (oral/visual adaptations), non-English
  speaking (translation), vulnerable populations (additional protections),
  Indigenous communities (collective governance frameworks).
- **Risk posture:** Minimal risk (streamlined consent, waiver options),
  elevated risk (detailed consent, additional safeguards), sensitive topics
  (enhanced confidentiality language, distress protocols).
- **Output type:** Written consent form, information sheet, oral consent
  script, media consent form, community consent protocol, re-consent
  protocol, consent process design, adapted consent materials.
- **Regulatory framework:** U.S. Common Rule (default), Canadian TCPS 2,
  EU/Horizon Europe, UK ESRC, Australian NHMRC. Determines required elements,
  available waivers, and documentation expectations.

## Guardrails

- **Consent is a process, not a document.** Every output should frame consent
  as ongoing and negotiated. A signed form is documentation of one moment in
  a continuing conversation. Help users design the process, not just the
  paperwork.
- **Quality of understanding matters more than format.** A participant who
  genuinely understands what they are agreeing to through a verbal
  conversation has given better consent than one who signs a form they did
  not read. Help users justify the consent mode that produces genuine
  comprehension.
- **Do not overpromise confidentiality.** Absolute anonymity cannot always be
  guaranteed in qualitative research. Consent language should be honest:
  "we will take these specific steps to protect your identity, but we cannot
  promise that no one will ever be able to identify you."
- **Recording consent must be separate and tiered.** Participants must be able
  to participate without being recorded. Consent for audio, video, and
  photography should be distinct choices, not bundled with study consent.
- **Adapt to cultural context without abandoning ethical standards.** Cultural
  adaptation means changing the form and process of consent, not lowering the
  standard. Community consent supplements but does not replace individual
  consent. Oral consent in low-literacy settings still requires genuine
  understanding and voluntary agreement.
- **Flag when consent documents cannot solve the problem.** Some ethical
  challenges (extreme power imbalances, coercive institutional settings,
  participants who cannot meaningfully refuse) require methodological
  redesign, not better consent forms. Flag these situations.
- **Do not produce generic boilerplate.** Every consent document must reflect
  the specific study's methods, population, risks, and context. Language
  that could apply to any study is a failure mode.

## Common Failure Modes

| Failure mode | Prevention |
|---|---|
| Consent form that participants cannot understand (jargon, complex sentences, legal language) | Write at a 6th-8th grade reading level; use plain language, short sentences, bullet points; test with a non-researcher |
| One-time signature treated as permanent consent | Frame consent as ongoing; specify check-in points; include re-consent triggers in the process design |
| Recording consent bundled with study consent (all or nothing) | Separate recording consent with tiered options: participate without recording, record for analysis only, record for publication |
| Confidentiality overpromised ("your identity will be completely protected") | Use honest language: "we will take these steps... but cannot guarantee absolute anonymity in all circumstances" |
| Written consent imposed in contexts where it increases risk | Justify verbal consent with waiver of documentation; provide information sheet without requiring signature |
| Focus group consent that promises confidentiality | State explicitly that confidentiality cannot be guaranteed in group settings; describe mitigation steps |
| Generic consent form with no study-specific content | Every section must reflect the actual study: specific methods, specific risks, specific data handling plans |
| Missing media consent for visual methods | Require separate, tiered consent for any audio, video, or photographic recording; specify use and retention |

## Examples

**Example 1: Written consent form for semi-structured interviews**

Input: "I need a consent form for my interview study about health workers'
experiences with burnout in rural Kenya. I'll be doing 30 interviews in
English and Swahili, audio-recorded. Participants work at government health
facilities."

Output approach:
- Load both reference files
- Set consent mode to written (standard risk, literate population)
- Set methods to semi-structured interviews with audio recording
- Key design decisions: (a) bilingual form (English + Swahili), (b) tiered
  recording consent (participate without recording as an option), (c) address
  power dynamics (health workers may feel pressure from facility management —
  clarify that participation is separate from employment and supervisors will
  not know who participated), (d) confidentiality with honest limits
  (pseudonyms, encrypted storage, but acknowledge small professional
  community), (e) distress protocol for burnout discussions
- Generate: full consent form with all required sections, plus separate
  recording consent checkbox, plus Swahili translation guidance notes

**Example 2: Verbal consent with information sheet for participant observation**

Input: "I'm doing participant observation in a homeless shelter in Portland.
Many residents have literacy challenges and are wary of signing documents.
My IRB is asking how I'll get consent without written forms."

Output approach:
- Load both reference files
- Set consent mode to verbal with waiver of documentation
- Set population to low-literacy, potentially vulnerable (housing insecurity)
- Key design decisions: (a) justify waiver — signed forms create a record
  linking participants to a study about a stigmatized population, and many
  participants cannot read the form; (b) design a plain-language information
  sheet (large font, bullet points, visual elements) that participants keep
  but do not sign; (c) oral consent script covering all required elements;
  (d) witness protocol for documenting verbal consent; (e) layered consent
  distinguishing primary participants (consented for observation + interview)
  from incidental contacts in the shelter; (f) ongoing consent check-ins
  given that shelter residents may come and go
- Generate: information sheet, oral consent script, witness documentation
  form, and a consent process narrative suitable for the IRB application

**Example 3: Community consent protocol for research with Indigenous community**

Input: "I'm planning research on traditional ecological knowledge with a
First Nations community in British Columbia. The band council wants to be
involved in the consent process. I need to design something that respects
both TCPS 2 Chapter 9 and the community's own governance."

Output approach:
- Load both reference files
- Set regulatory framework to Canadian TCPS 2 with Indigenous governance
  (OCAP principles, CARE principles)
- Key design decisions: (a) two-layer consent — community authorization
  through band council plus individual participant consent; (b) community
  research agreement addressing data ownership, access, and use (OCAP);
  (c) consent for traditional knowledge that addresses collective rights,
  not just individual privacy; (d) participant choice model for attribution
  vs anonymity (some knowledge holders may want to be credited); (e)
  community review of outputs before publication; (f) consent language
  addressing what happens to data if the community-researcher relationship
  ends
- Generate: community research agreement template, individual consent form
  with attribution/anonymity choice, and a consent process design document
  describing the two-layer approach for the ethics board

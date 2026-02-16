---
name: irb-protocol
description: >
  Use this skill whenever a user needs help writing, revising, or evaluating
  an IRB or ethics protocol for qualitative or anthropological research.
  Triggers include: any mention of "IRB," "ethics protocol," "IRB application,"
  "ethics review," "human subjects," "Common Rule," "informed consent form,"
  "consent process," "how to write an IRB protocol," "ethics board," "IRB
  submission," "protocol narrative," "exempt vs expedited vs full board,"
  "consent waiver," "verbal consent," "data security plan," "confidentiality,"
  "de-identification," "deductive disclosure," "vulnerable populations,"
  "fieldwork ethics," or "recruitment script." Also trigger when users ask
  about writing consent forms, recruitment materials, data management plans
  for IRB, risk assessment for qualitative research, digital ethnography
  ethics, or oral history IRB issues. Covers all qualitative and ethnographic
  methods. Do NOT use for upstream method selection (use methodology-selection
  skill), full research plan writing (use research-plan skill), or grant
  proposals (use grant-proposal skill). This skill handles writing IRB-ready
  protocol narratives and associated documents.
---

# IRB & Ethics Protocol Writing

Write IRB and ethics protocols for qualitative anthropological research that
satisfy regulatory review criteria while making legible the distinctive
epistemics and practical uncertainties of ethnographic work — emergent
sampling, relational consent, and shifting field conditions. The skill treats
protocol writing as a translation problem: making ethnographic practice
reviewable without distorting it.

Contemporary best-practice protocols do two things at once: they (a) satisfy
the Common Rule's review criteria (risk minimization, risk-benefit
proportionality, equitable selection, consent, privacy and confidentiality
safeguards, and added protections when appropriate); and (b) anticipate
reviewer questions about ambiguity, and answer them with bounded flexibility
(estimated sample sizes plus an amendment plan; tiered consent strategies;
contingency plans for fieldwork changes).

## Quick Reference

| Task | Reference |
|------|-----------|
| Protocol template, checklist, regulatory foundations, comparative guidance | Read [references/irb-protocol-guide.md](references/irb-protocol-guide.md) |
| Method-specific guidance, consent templates, sample language, annotated excerpts | Read [references/irb-templates-and-examples.md](references/irb-templates-and-examples.md) |

## Workflow

### Step 1: Identify What the User Needs

Determine the entry point:

- **Writing a protocol from scratch.** The user has a research design and
  needs to produce a full protocol narrative. Load both reference files and
  work through the template section by section.
- **Revising for resubmission.** The user has reviewer feedback and needs to
  address specific concerns. Identify which protocol sections need revision
  and load relevant guidance.
- **Writing specific components.** The user needs a consent form, recruitment
  script, data management plan, or risk assessment — not a full protocol.
  Load the templates reference for modular text blocks.
- **Adapting for a specific method.** The user's methods trigger special
  protocol requirements (digital ethnography, oral history, visual methods,
  focus groups). Load the templates reference for method-specific guidance.

### Step 2: Gather Context

Before generating any content, collect these inputs:

**Required:**
1. **Research methods.** What methods will be used? Participant observation,
   interviews, focus groups, oral history, visual methods, digital
   ethnography, archival, or mixed? Different methods trigger different
   protocol requirements.
2. **Study population.** Who are the participants? How many (estimated range)?
   Are there primary vs incidental participants? Are there vulnerable
   populations, minors, dependency relationships?
3. **Risk level.** Minimal risk? Sensitive topics (health, legal status,
   political activity)? Vulnerable populations? Cross-border data?

**Important but can be inferred:**
4. **Institutional context.** U.S. Common Rule (default assumption), Canadian
   TCPS 2, or other? Does the institution use a SmartForm platform or
   narrative-style application?
5. **Review pathway.** Does the user expect exempt, expedited, or full board
   review? If unsure, help determine the likely pathway based on methods and
   risk profile.
6. **Consent approach.** Written, verbal with waiver, layered/tiered, ongoing,
   community-level? If unspecified, recommend based on methods and context.
7. **Recording plans.** Audio, video, photo, screenshots? Separate consent
   for recordings is usually required.
8. **Data sharing/archiving plans.** Will data be archived or shared?
   Consent language must match sharing plans.

**Helpful but not required:**
- Field site(s) and whether they are public or private spaces
- Language of consent (may need translated materials)
- Whether the project involves Indigenous communities (triggers additional
  governance requirements: CARE, OCAP, FPIC)
- Whether the project is funded (some funders require Certificates of
  Confidentiality or specific data management plans)
- Prior IRB experience and career stage

### Step 3: Load Appropriate References

- **Always load** `references/irb-protocol-guide.md` for the protocol
  template, regulatory foundations, checklist, and comparative guidance.
- **Load** `references/irb-templates-and-examples.md` when the user needs
  method-specific guidance, consent form language, recruitment scripts, data
  management plan templates, risk mitigation strategies, or annotated
  protocol excerpts.

### Step 4: Generate Protocol Content

Follow the protocol template architecture from the guide reference. The
standard protocol narrative contains these sections (adapt to institutional
format):

1. **Project overview and key information** — rapid orientation for reviewer
2. **Research questions and analytic goals** — establishes systematic
   investigation and social value
3. **Setting and sites** — privacy expectations and permissions
4. **Study population** — equitable selection, vulnerability flags
5. **Recruitment and access** — coercion risk, gatekeeper roles
6. **Methods and procedures** — core risk assessment anchor
7. **Consent processes** — meets regulatory requirements while addressing
   ethnographic consent realities
8. **Confidentiality and anonymization** — deductive disclosure, group limits
9. **Data management and security** — auditable controls
10. **Risks and mitigation** — social, legal, reputational, emotional,
    community harms
11. **Benefits, reciprocity, dissemination** — beyond clinical framing
12. **Vulnerable populations and power dynamics** — added safeguards
13. **Fieldwork contingencies and amendment plan** — makes uncertainty
    governable

### Step 5: Generate Output

Produce one or more deliverables depending on user needs:

- **Full protocol narrative.** Complete document following the 13-section
  template, with suggested word counts per section.
- **Consent form or information sheet.** Modular text blocks including key
  information summary, ongoing consent language, recording permissions,
  and focus group confidentiality limits.
- **Oral consent script.** For use with waiver of documentation.
- **Recruitment script.** IRB-compliant recruitment language.
- **Data management plan.** Storage, encryption, access control, key-file
  separation, retention, destruction, sharing/archiving.
- **Risk mitigation plan.** Deductive disclosure, emotional distress, legal
  risk, community harm, cross-border data.
- **Individual sections.** Any of the 13 protocol sections as standalone
  drafts.

### Step 6: Quality Check

Before presenting output, verify using the dual applicant-reviewer checklist
(full version in guide reference):

- [ ] Research determination and level of review are identified
- [ ] Research questions show social value and interpretive coherence
- [ ] Sites and permissions clarify public vs private, gatekeepers
- [ ] Population defines primary vs incidental participants with estimated
      sample size range
- [ ] Recruitment minimizes coercion and avoids role confusion
- [ ] Consent approach specifies written vs verbal, includes key information,
      addresses documentation waiver if used
- [ ] Ongoing consent is operational, not aspirational
- [ ] Recording plans specify separate consent and address identifiability
- [ ] Focus group limits state confidentiality cannot be guaranteed
- [ ] Anonymization addresses deductive disclosure for small-N data
- [ ] Data security describes specific controls (encryption, access, key-file
      separation)
- [ ] Data sharing/archiving claims do not exceed consent language
- [ ] Legal risk is framed appropriately; protections are not overstated
- [ ] Risks to participants are identified with mitigation and referrals
- [ ] Community impacts are considered where salient
- [ ] Vulnerable populations have additional protections
- [ ] Reciprocity and compensation avoid undue influence
- [ ] Fieldwork contingencies list amendment triggers and safety pivots

## Parameters

- **Review pathway:** Exempt, expedited, full board. Determines scope and
  detail of protocol narrative.
- **Methods in protocol:** Participant observation, interviews, focus groups,
  oral history, visual methods, digital ethnography, archival, mixed.
  Different methods trigger different protocol requirements.
- **Risk posture:** Minimal risk, sensitive topics, vulnerable populations,
  high-surveillance, cross-border. Higher risk postures require more detailed
  safeguards.
- **Consent modality:** Written, verbal with waiver, layered/tiered, ongoing,
  community-level. Choice depends on methods, context, and risk.
- **Output type:** Full protocol narrative, consent form, information sheet,
  recruitment script, data management plan, risk assessment, individual
  sections.
- **Institutional context:** U.S. Common Rule (default), Canadian TCPS 2,
  other. Determines regulatory framework and required elements.

## Guardrails

- **Do not produce boilerplate.** Every protocol section must reflect the
  specific project's methods, population, and risks. Generic language that
  could apply to any study is a failure mode.
- **Do not conflate consent process with consent documentation.** The Common
  Rule distinguishes these. A project can have a robust consent process
  (verbal, ongoing, relational) while requesting a waiver of written
  documentation. Help users frame this correctly.
- **Require explicit treatment of deductive disclosure.** For small-N,
  high-context qualitative data, "de-identification" alone is insufficient.
  Protocols must address how contextual details, distinctive roles, and
  narrative specificity can re-identify participants even without direct
  identifiers.
- **Flag method-specific protocol requirements.** When methods require
  special protocol attention, flag it explicitly:
  - Digital ethnography: public/private ambiguity, searchability of quotes,
    platform terms of service
  - Oral history: attribution vs anonymity choice, archiving options,
    narrator review
  - Visual methods: faces and locations as identifiers, rights and ownership
  - Focus groups: confidentiality cannot be guaranteed among participants
  - Participant observation: primary vs incidental participants
- **Ethics goes beyond IRB compliance.** Address AAA principles (do no harm,
  ongoing consent, record stewardship), community obligations, and data
  sovereignty (CARE, OCAP) where relevant. Do not treat the IRB as the
  ceiling of ethical practice.
- **Do not overpromise protections.** Certificates of Confidentiality have
  exceptions. "Confidentiality" in focus groups cannot be guaranteed.
  De-identification of qualitative data is always limited. Help users frame
  protections accurately.
- **Require amendment planning.** Ethnographic designs are emergent. Protocols
  must specify what changes require amendment (new populations, new recording
  types, materially increased risk) and what falls within approved
  flexibility (follow-up questions, emergent themes within approved domains).

## Common Failure Modes

| Failure mode | Prevention |
|---|---|
| Boilerplate consent that doesn't match ethnographic practice | Write consent language specific to the project's methods, population, and risk profile |
| Treating "confidentiality" as absolute promise | Frame as managed limitation; specify what controls exist and what limits remain |
| Missing deductive disclosure plan for small communities | Require aggregation, temporal fuzzing, role-based descriptors, controlled access |
| No amendment strategy for emergent sampling | Specify what changes require amendment vs what is approved flexibility |
| Consent form that doesn't distinguish primary from incidental participants | Use layered consent: site permission, introduction script, individualized consent |
| Data security described generically ("data will be kept secure") | Name specific controls: encryption, storage locations, access roles, key-file separation |
| Digital ethnography without internet-specific ethics | Require public/private analysis, quoting policy, screenshot handling, platform terms |
| Oral history without addressing attribution/anonymity choice | Offer participant choice model with dissemination options and time-limited restrictions |

## Examples

**Example 1: Full protocol for participant observation + interviews**

Input: "I need to write an IRB protocol for my study of street vendors
negotiating municipal regulation in Lima. I'll be doing participant
observation and semi-structured interviews with about 30 vendors."

Output approach:
- Load both reference files
- Set risk posture to standard (public spaces, non-sensitive population)
- Set consent modality to layered (site permission + verbal introduction +
  written consent for interviews + separate recording consent)
- Protocol: distinguish primary participants (30 consented interviewees) from
  incidental contacts during observation in public spaces
- Consent: written consent for interviews; justify observation in public
  spaces as not requiring individual consent; ongoing consent checkpoints
- Data security: encrypted storage, pseudonyms, deductive disclosure plan
  for small vendor community
- Fieldwork contingencies: amendment plan for expanded sites or populations
- Generate full 13-section protocol narrative

**Example 2: Digital ethnography protocol**

Input: "I'm studying how online health communities discuss alternative
treatments on Reddit. I want to analyze posts and do some interviews with
active members. My IRB is asking about consent for the Reddit data."

Output approach:
- Load both reference files
- Set methods to digital ethnography + interviews
- Set risk posture to elevated (health information, searchable content)
- Key protocol issues: (a) treating publicly accessible posts as human
  subjects data when collected and curated systematically; (b) quoting
  policy to prevent searchable re-identification; (c) separate consent
  pathway for interview participants vs observed forum content
- Consent: interviews get standard consent; forum observation uses
  paraphrase-only policy with no verbatim quotes, no screenshots with
  usernames; justify approach using context-sensitive internet research
  ethics
- Data security: encrypted storage, separate key-file for pseudonym-handle
  links, no raw data in cloud services

**Example 3: Oral history with archiving**

Input: "I'm collecting oral histories from civil rights activists. Some want
to be named. My IRB is confused about whether this is 'research' and how to
handle the naming issue."

Output approach:
- Load both reference files
- Address research determination: state whether this meets the regulatory
  definition of research (systematic investigation designed to contribute
  to generalizable knowledge) and what the institution's expected pathway is
- Set consent modality to participant choice (pseudonym vs attribution)
- Protocol: narrators choose whether to be credited or anonymized; narrators
  review transcripts; narrators select access conditions for archived
  materials (open, restricted, embargoed)
- Archiving: specify repository, access conditions, and how consent language
  supports the planned deposit
- Risk: attribution may create long-term risk; anonymization may be
  experienced as erasure; frame as informed choice with clear explanation
  of implications

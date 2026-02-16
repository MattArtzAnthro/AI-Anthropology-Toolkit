---
name: job-materials
description: >
  Use this skill whenever a user needs help preparing academic job application
  materials for anthropology positions. Triggers include: any mention of
  "academic CV," "curriculum vitae," "cover letter," "job application," "job
  talk," "academic job market," "tenure-track application," "postdoc
  application," "VAP application," "lecturer position," "how to write a cover
  letter," "CV formatting," "job talk preparation," "campus visit," "search
  committee," "application package," "tailoring applications," or "academic
  hiring." Covers academic CV design and formatting, cover letters tailored by
  position type, job talk design and delivery, and application strategy. Do NOT
  use for research/teaching/diversity statements (use career-statements skill),
  conference presentations (use conference-materials skill), or grant proposals
  (use grant-proposal skill).
---

# Job Application Materials for Anthropologists

## Overview

Produce market-ready application materials -- CVs, cover letters, job talks, and strategic application plans -- for academic anthropology positions. Each document type has field-specific norms and expectations that vary by position type, institution, and career stage. This skill treats job materials as strategic communication: every element should demonstrate fit between the candidate and the specific position.

The academic job market is a genre system. CVs have expected sections in expected order. Cover letters have a known architecture. Job talks have conventions that differ from conference talks. This skill provides the genre knowledge so the candidate can focus on content.

Materials are never produced in isolation. A cover letter references what the CV demonstrates. A job talk previews the research program the cover letter describes. An application package is a coordinated rhetorical performance where every piece reinforces the others.

Position type drives everything. The same candidate should present themselves differently for an R1 tenure-track position than for a liberal arts college, a postdoc, or a visiting position. The underlying qualifications are the same, but the emphasis, framing, and even the ordering of information must change to match what each institution values and evaluates. Materials that do not reflect this awareness signal that the candidate does not understand the field they are entering.

## Quick Reference

| Task | Reference |
|------|-----------|
| CV structure, sections, formatting, career-stage norms | Read `references/cv-design-guide.md` |
| Cover letter architecture, position analysis, tailoring | Read `references/cover-letter-guide.md` |
| Job talk design, delivery, Q&A preparation, campus visit | Read `references/job-talk-guide.md` |

## Workflow

### Step 1: Identify Needs

Determine which materials the user needs help with. Common requests fall into these categories:

- **Single document**: CV, cover letter, or job talk in isolation
- **Revision**: Improving existing materials with specific feedback
- **Full package**: Coordinated set of materials for a specific application
- **Application strategy**: Deciding which positions to apply for, timeline planning, managing multiple applications
- **Mock review**: Evaluating materials from the perspective of a search committee

### Step 2: Gather Context

**Required information:**
- Position type: tenure-track R1, tenure-track SLAC, tenure-track balanced institution, postdoc, VAP, lecturer, alt-ac
- Career stage: ABD, recent PhD (0-3 years), early career (3-7 years), mid-career (7-15 years)
- Subfield: cultural, biological/physical, archaeological, linguistic, applied, medical, environmental, or other specialization

**Important information:**
- Specific job ad text to tailor materials to
- Existing CV or other materials to revise
- Research area and key publications
- Teaching experience and interests

**Helpful information:**
- Department composition and recent hires at the target institution
- Candidate's particular strengths or concerns
- Timeline and deadlines
- Whether the candidate has received prior feedback on materials

If the user provides a job ad, analyze it before generating any materials. The ad reveals what the department prioritizes and how to frame the candidate's profile. Key elements to extract from an ad: required vs. preferred qualifications, named courses, subfield or area focus, emphasis on research vs. teaching vs. service, language about diversity and inclusion, and any unusual requirements (e.g., joint appointments, administrative roles, center affiliations).

If the user does not have a specific job ad, work with the position type and career stage to produce materials that follow best practices for that category. Note that generic materials should still be high quality -- they serve as a strong starting template that the candidate will tailor for each application.

### Step 3: Load References

Based on the identified needs, load the appropriate reference guides:

- **CV only**: Load `references/cv-design-guide.md`
- **Cover letter only**: Load `references/cover-letter-guide.md`
- **Job talk only**: Load `references/job-talk-guide.md`
- **Full package or application strategy**: Load all three guides
- **Revision of existing materials**: Load the relevant guide(s) for the document type being revised

Always confirm the reference content is loaded before generating materials. The reference guides contain the detailed genre knowledge, formatting conventions, and position-specific guidance that the generated output must follow.

### Step 4: Generate Content

All content must be tailored to the specific position type and institution. Key distinctions:

- **R1 tenure-track**: Lead with research. Emphasize publications, grants, graduate mentoring potential, and a clear research trajectory. Teaching matters but research is the primary evaluation criterion.
- **SLAC tenure-track**: Lead with teaching, but demonstrate active scholarship. Show curricular creativity, advising commitment, and enthusiasm for undergraduate mentoring. Research should be presentable to undergraduates.
- **Balanced institution**: Both research and teaching must be strong. Neither can carry the other. Show integration between research and teaching where possible.
- **Postdoc**: Research potential and productivity. Fit with the host lab or project. Mentoring capacity. Clear plan for the postdoc period.
- **VAP**: Teaching flexibility and breadth. Ability to step into existing courses. Collegiality and low-maintenance integration into a department.
- **Lecturer**: Teaching excellence and innovation. Course design experience. Assessment expertise. Student mentoring.
- **Alt-ac**: Transferable skills, project management, collaboration, impact outside the academy. Different document formats and conventions apply.

### Step 5: Generate Output

Produce the requested materials in clean, professional format. Output types include:

- **CV**: Full formatted CV or revision notes on existing CV
- **Cover letter**: Complete draft or structural outline with key content for each section
- **Job talk**: Detailed outline with slide suggestions, timing notes, and Q&A preparation
- **Application checklist**: Position-specific list of required and recommended materials with deadlines
- **Full package strategy**: Coordinated plan showing how all materials work together for a specific application
- **Revision feedback**: Detailed, actionable notes on existing materials with specific suggestions for improvement

When generating a full package, ensure consistency across documents. The research program described in the cover letter should match what the CV demonstrates. The job talk should present work that the cover letter has contextualized. The teaching philosophy implied in the cover letter should be consistent with the courses listed on the CV. Contradictions or misalignments between documents are red flags for search committees.

### Step 6: Quality Check

Before delivering any output, verify:

- [ ] Genre conventions are followed (correct sections, ordering, format)
- [ ] Content is tailored to the specific position type and institution
- [ ] No generic, interchangeable language remains
- [ ] Professional formatting is consistent throughout
- [ ] Claims are supportable and honest -- nothing fabricated or embellished
- [ ] Materials work together as a coordinated package (if multiple documents)
- [ ] Accessibility considerations are addressed (especially for job talk slides)
- [ ] Length is appropriate for the document type and career stage

## Parameters

| Parameter | Options | Default |
|-----------|---------|---------|
| Position type | tenure-track R1, tenure-track SLAC, tenure-track balanced, postdoc, VAP, lecturer, alt-ac | tenure-track R1 |
| Career stage | ABD, recent PhD, early career, mid-career | recent PhD |
| Subfield | cultural, biological, archaeological, linguistic, applied, medical, environmental, other | cultural |
| Material type | CV, cover letter, job talk, application checklist, full package | CV |
| Tailoring level | generic template, institution-specific, position-specific | position-specific |

### Parameter Interactions

Position type and career stage interact in important ways:

- **ABD + R1 tenure-track**: Uncommon but possible. The CV will be short. The cover letter must sell potential rather than track record. Publications and grants are the strongest signals.
- **ABD + SLAC**: More common. Teaching experience matters enormously. Demonstrate breadth and pedagogical thoughtfulness.
- **Recent PhD + postdoc**: Standard pathway. Focus on research productivity and what the postdoc period will enable.
- **Early career + R1 tenure-track**: The most competitive category. Strong publication record, external funding, and clear research trajectory are expected.
- **Mid-career + any position**: Lateral moves or first tenure-track after a series of contingent positions. Frame the trajectory honestly and emphasize accumulated strengths.

Subfield also affects conventions. Archaeological CVs feature fieldwork and technical skills more prominently. Biological anthropology may follow different publication norms. Linguistic anthropology emphasizes language proficiency. Applied anthropology values community partnerships and non-academic outputs. Always adapt the general guidance to the candidate's specific subfield.

## Application Timeline and Strategy

For users seeking application strategy guidance, use the following general timeline for the North American academic job market:

| Month | Activity |
|-------|----------|
| June-July | Begin updating CV; draft research and teaching statements; identify target positions from preliminary job listings |
| August-September | Main job ads posted (AAA AnthroGuide, HigherEdJobs, H-Net, disciplinary listservs). Begin tailoring cover letters for early deadlines. |
| September-November | Peak application submission period. Most tenure-track deadlines fall in this window. |
| October-December | Postdoc deadlines vary widely; check individual program timelines. |
| November-January | First-round interviews (video or conference). Prepare for 20-30 minute interviews with search committees. |
| January-March | Campus visits for shortlisted candidates. Job talks, teaching demos, faculty meetings. |
| February-April | Offers extended. Negotiation period. |
| March-May | Late-cycle positions posted (VAPs, lecturers, unexpected lines). Second-round hiring. |

Key strategic considerations:
- Apply broadly but strategically. Applying to positions where you have no realistic fit wastes time and energy.
- Prioritize quality over quantity in cover letters. A well-tailored letter for 15 positions outperforms a generic letter for 40.
- Keep a spreadsheet tracking: position, institution, deadline, materials submitted, status, follow-up dates.
- Have multiple versions of your cover letter template organized by position type (R1, SLAC, balanced, postdoc, VAP).
- Ask recommenders for letters early (at least 4-6 weeks before the first deadline) and keep them updated on your application list.

### First-Round Interview Preparation

If a user mentions preparing for a first-round interview (often conducted via video call), this falls within the scope of this skill. First-round interviews typically last 20-30 minutes and cover:

- Brief research overview (2-3 minutes, not a full talk)
- Teaching experience and approach (specific courses you could teach)
- Questions about fit with the department
- Your questions for the committee

Key preparation steps: prepare a concise research elevator pitch, review the job ad and department thoroughly, prepare 3-5 thoughtful questions to ask the committee, practice speaking about your work concisely and engagingly, test your video setup and internet connection.

## Guardrails

- CVs must follow disciplinary conventions for section ordering and content. Anthropology CVs have a standard architecture -- deviating from it without reason signals unfamiliarity with the field.
- Cover letters must be tailored to the specific position. Generic letters are immediately recognizable to search committees and communicate a lack of genuine interest.
- Job talks are not conference talks. They must demonstrate potential as a colleague, not just present research findings. Breadth, clarity, and intellectual range matter as much as depth.
- Do not fabricate or embellish qualifications. If a candidate has not published, do not suggest listing work "in preparation" unless manuscripts genuinely exist. If teaching experience is thin, frame it honestly.
- Materials should reflect what the candidate can genuinely claim, not aspirational self-presentation. Search committees verify claims and exaggeration damages credibility.
- Alt-ac materials follow different conventions. Do not apply academic norms to industry or nonprofit positions without explicit adaptation. A CV is not a resume.
- Always include accessibility considerations for job talk slides: sufficient contrast, readable fonts, alt text for images, and avoidance of color as the sole information carrier.
- Never recommend a one-size-fits-all approach. Every position type, institution type, and career stage calls for different emphases, framings, and strategic choices.
- Respect the candidate's voice. Materials should sound like the candidate at their most articulate and strategic, not like a template or a different person. Ask for samples of their writing when possible.
- Do not advise candidates to apply for positions where they have no realistic fit. Honest assessment of fit is a kindness, not a discouragement.
- Recognize the emotional dimension. The academic job market is stressful and often demoralizing. Be direct and practical in feedback but not callous. Distinguish between what the candidate can control (materials quality) and what they cannot (market conditions, committee preferences).

## Common Failure Modes

| Failure | Problem | Fix |
|---------|---------|-----|
| Generic cover letter | Search committee sees no evidence of fit; letter could be sent anywhere | Analyze the job ad and department; reference specific courses, colleagues, initiatives |
| CV padding | Listing trivial items or inflating roles signals insecurity, not accomplishment | Remove weak items; let strong items stand without padding |
| Dissertation summary as research statement | Cover letter research section reads like an abstract, not a research program | Frame research as an ongoing program with past results, current projects, and future directions |
| Conference talk as job talk | Too narrow, too fast, too specialized; audience loses interest | Broaden framing, slow down, explain methods and terms, add future directions |
| Defensive Q&A responses | Treating questions as attacks rather than intellectual engagement | Prepare for common question types; practice brief, generous answers |
| Wrong institution type framing | Leading with research for a SLAC, or leading with teaching for an R1 | Match emphasis to what the institution actually values and evaluates |
| Inconsistent package | CV claims one thing, cover letter emphasizes another, job talk ignores both | Coordinate all materials; they should tell a consistent story from different angles |
| Ignoring the ad | Applying to a job in medical anthropology with materials focused on political ecology | Read the ad carefully; if the fit is marginal, either reframe honestly or do not apply |

## Coordinating the Application Package

Most tenure-track applications require some combination of: CV, cover letter, research statement, teaching statement, diversity statement, writing sample, and letters of recommendation. This skill covers the CV, cover letter, and job talk. For research/teaching/diversity statements, use the career-statements skill.

The package must tell a coherent story. Here is how the pieces relate:

- **CV** provides the factual foundation. Everything claimed in other documents should be verifiable on the CV.
- **Cover letter** is the argument for fit. It selects from the CV and frames those selections for this specific position.
- **Research statement** (career-statements skill) elaborates the research program that the cover letter summarizes. It provides the detail and trajectory.
- **Teaching statement** (career-statements skill) elaborates the teaching approach that the cover letter previews.
- **Writing sample** demonstrates the quality of the scholarship that the CV lists and the cover letter describes.
- **Job talk** brings the research to life for a live audience and demonstrates the candidate as a colleague.

When helping with a cover letter, ask whether the user is also preparing other statements. Consistency across documents is critical. If the cover letter describes a research program focused on digital labor, the research statement should not pivot to a different framing without explanation.

### Writing Sample Selection

Although this skill does not produce writing samples, candidates often ask for advice on selection. The writing sample should:

- Be your best work, not necessarily your most recent
- Match the position's emphasis (a theory-heavy piece for a theory position, a methods-rich piece for a methods-oriented search)
- Be a reasonable length (25-35 pages is typical unless the ad specifies)
- Demonstrate the kind of scholarship you will produce as a faculty member
- Be a published or near-publication-quality piece, not a raw dissertation chapter

If the ad asks for a writing sample "related to your research," send work that connects to the research program described in your cover letter. If the ad does not specify, choose the piece that best demonstrates your analytical strengths.

## Examples

### Example 1: Cultural Anthropology CV for R1 Tenure-Track

**Context**: ABD candidate finishing a dissertation on digital labor practices in Southeast Asia. Two peer-reviewed articles, one book chapter. Three years of teaching as a TA plus one course designed and taught independently. NSF DDRIG and Wenner-Gren dissertation fellowship.

**Approach**:
- Load `references/cv-design-guide.md`
- Structure CV with Education first (degree expected date prominent), then Publications (peer-reviewed articles first), then Grants and Fellowships (NSF and Wenner-Gren are strong signals), then Conference Presentations, then Teaching Experience
- At ABD stage, keep to 3-4 pages. Do not pad with every guest lecture or departmental committee
- List publications with full citation format, clearly distinguishing peer-reviewed from other
- In Teaching section, separate "Courses Designed and Taught" from "Teaching Assistant" roles
- Include Languages and Fieldwork sections given the Southeast Asia focus
- Add a brief Professional Development or Methods Training section if the candidate has formal methods training relevant to the position

**Key decisions**:
- "Under review" items: include only if genuinely under review at a journal, not if merely planned
- Conference presentations: list selectively. AAA, SfAA, and subfield conferences; omit departmental brown bags
- References: list 3-4 names with full contact information at the end
- Fieldwork section placement: for Southeast Asia research, fieldwork and language competency are central qualifications. Place these sections where they will be noticed, not buried at the bottom.
- Digital presence: include ORCID and personal academic website if maintained. These are increasingly expected and allow the committee to learn more about the candidate.

### Example 2: Tailored Cover Letter for a SLAC Position

**Context**: Recent PhD (2 years out) applying for an assistant professor position at a liberal arts college. The ad emphasizes teaching excellence, undergraduate mentoring, and the ability to teach Introduction to Cultural Anthropology and a course on globalization. The department has 4 faculty members and values interdisciplinary collaboration.

**Approach**:
- Load `references/cover-letter-guide.md`
- Analyze the job ad: small department means they need teaching breadth and collegiality. Emphasis on intro course and globalization means these should be addressed directly. "Undergraduate mentoring" signals they want someone who will supervise senior theses and engage students in research.
- Opening paragraph: State who you are, what position you are applying for, and demonstrate that you know this specific department. Reference something concrete -- a faculty member's work, a program initiative, the college's liberal arts mission.
- Teaching paragraph comes second (before research) for a SLAC. Describe your approach to Introduction to Cultural Anthropology with specifics. Describe the globalization course you would design. Mention other courses you could offer that complement the existing curriculum.
- Research paragraph: Frame research as accessible and involving undergraduates. Describe your program but emphasize how it connects to teaching and how students participate.
- Service/collegiality: In a 4-person department, everyone does significant service. Show willingness and capacity. Mention interdisciplinary interests that connect to other departments.
- Keep to 1.5-2 pages. Every sentence should demonstrate fit with this specific position.

**Key decisions**:
- Do not lead with research prestige. This is not what a SLAC search committee prioritizes.
- Name specific courses from the ad and describe your approach to them.
- Show awareness of the liberal arts context -- not just teaching, but mentoring, advising, and intellectual community.
- Tone matters: the letter should convey warmth and genuine enthusiasm for undergraduate education, not a sense that you are settling for a SLAC because you could not get an R1 position. Search committees at liberal arts colleges are attuned to this and will reject candidates who seem to view their institution as a backup plan.

### Example 3: Job Talk Outline

**Context**: Early career candidate (3 years post-PhD) giving a job talk at a mid-sized research university. Research on water politics and infrastructure in South Asia. Book manuscript under contract. The department has strengths in environmental anthropology and political ecology.

**Approach**:
- Load `references/job-talk-guide.md`
- Design for 45 minutes of presentation plus 15-20 minutes of Q&A
- Structure the talk to be accessible to the entire department, not just environmental anthropologists

**Outline**:

1. **Opening (5 minutes)**: Start with a vivid fieldwork moment that captures the central tension -- a community meeting about water access that reveals how infrastructure projects reconfigure political relationships. Establish the broad question: How do large-scale infrastructure projects reshape local politics and everyday life?

2. **Framing and Literature (7 minutes)**: Position the work within political ecology, infrastructure studies, and the anthropology of the state. Define key terms clearly. Show how this work addresses a gap or advances a conversation that matters beyond the subfield.

3. **Methods and Site (5 minutes)**: Describe the field site with maps and images. Explain your ethnographic approach -- multi-sited, combining participant observation with archival research and interviews. Make methods visible so the audience can evaluate your evidence.

4. **Analytical Move 1 (8 minutes)**: First major argument with ethnographic evidence. Use a sustained example rather than multiple brief ones. Show your analytical process -- how you move from observation to interpretation.

5. **Analytical Move 2 (8 minutes)**: Second major argument that extends or complicates the first. Introduce different actors or scales. Demonstrate range and intellectual flexibility.

6. **Analytical Move 3 (5 minutes)**: Third point that ties the first two together or opens a new dimension. This is where you show the full scope of the project.

7. **Contribution and Future Directions (5 minutes)**: State clearly what this research contributes to anthropology and adjacent fields. Then describe the next project or the next phase -- show that you have a research program, not just a book. Connect future work to the department's strengths where possible.

8. **Closing (2 minutes)**: Return to the opening vignette or image. End with a clear, memorable statement of what is at stake.

**Q&A Preparation**:
- Anticipated questions about methods: Why this site? How long in the field? How do you handle positionality?
- Anticipated questions about scope: How does this apply beyond South Asia? What about climate change dimensions?
- Anticipated questions about theory: How does this relate to [specific faculty member's work]? Where do you part ways with [major theorist]?
- Practice concise, 1-2 minute answers. Thank the questioner. If you do not know, say so honestly and describe how you would investigate.

**Slide guidance**:
- 25-35 slides maximum for 45 minutes
- Use assertion-evidence format: slide title is a claim, body is the evidence
- Include fieldwork photographs (with appropriate consent and ethical consideration)
- Maps for spatial context
- Minimal text on slides -- speak the argument, show the evidence
- Ensure all images have sufficient contrast and are described verbally for accessibility

**Campus visit context**:
- The job talk sets the tone for all other interactions during the 1-2 day visit
- Faculty who attend the talk will reference it in one-on-one meetings
- Be prepared for informal follow-up questions about your research throughout the visit
- Student meetings assess your mentoring and teaching potential -- be warm, curious, and engaged
- Social meals are still part of the evaluation -- be professional, personable, and attentive

### Adapting Examples by Subfield

The three examples above use cultural anthropology scenarios. For other subfields, the same principles apply with adjustments:

**Archaeology**: CVs should prominently feature fieldwork experience (excavation, survey, lab work), technical skills (GIS, remote sensing, lithic analysis), and CRM experience if applicable. Cover letters for archaeology positions often emphasize methodological range and field direction experience. Job talks in archaeology typically include more data visualization -- maps, stratigraphic profiles, artifact typologies, spatial analyses -- and may need to explain technical methods to non-archaeologist anthropologists in the department.

**Biological/Physical Anthropology**: CVs may follow slightly different publication conventions (contribution-based author ordering). Lab skills, datasets, and technical methods deserve prominent placement. Cover letters should articulate how biological anthropology research connects to the department's four-field or multi-subfield identity. Job talks should explain statistical methods and laboratory procedures clearly for the non-specialist audience.

**Linguistic Anthropology**: Language documentation projects, transcription and corpus analysis skills, and community-based language work are distinctive qualifications. Cover letters should demonstrate how linguistic anthropology courses serve the broader curriculum. Job talks may need to play audio or present transcripts, requiring additional technology preparation.

**Applied Anthropology**: Community partnerships, reports, and policy impact are significant credentials that differ from traditional academic metrics. Cover letters should frame applied work as both practically impactful and intellectually rigorous. Job talks at applied programs should demonstrate methodology and real-world outcomes alongside theoretical contribution.

**Medical Anthropology**: Increasingly interdisciplinary, with positions sometimes housed in public health or global health programs rather than anthropology departments. CVs may need to include clinical or public health experience. Cover letters should demonstrate ability to speak across disciplinary boundaries. Job talks should be accessible to health professionals who may not have anthropological training.

**Environmental Anthropology**: Often intersects with environmental studies, geography, or sustainability programs. Candidates should be prepared to articulate how their work contributes to environmental and climate conversations beyond anthropology. Multispecies ethnography, political ecology, and science and technology studies are common theoretical frameworks that should be explained for non-specialist audiences.

# Manuscript Anonymization Guide

Reference file for the research-writing skill. Loaded when preparing an
anonymous version of a manuscript for blind or double-anonymous peer
review: finding everything that reveals the authors, deciding what to do
with each item, and producing a worklist the author can execute — plus
the restoration map for after acceptance.

The governing test throughout is the **insider test**: not "is the name
removed?" but "could a reviewer *in this subfield* identify the author
from what remains?" Anthropology fails this test in distinctive ways —
a unique field site plus a citation trail identifies an ethnographer as
surely as a byline.

---

## Step 0: Check the Journal's Actual Policy

Anonymization conventions differ by journal, and guessing wastes work:

- Some journals want self-citations kept but rewritten in third person;
  others want them masked as "(Author, Year)" with the reference entry
  reduced to "Author (Year). Details removed for peer review."
- Some require anonymized data-availability and ethics statements;
  others move those to unblinded metadata pages.
- Some check file metadata; all should be assumed to.

Read the submission guidelines first and record the journal's rules at
the top of the worklist. When the guidelines are silent, default to the
conservative options below.

## Step 1: Scan — The Identity Surface

Sweep the manuscript for every item in each category. For each hit,
record location, what it reveals, and risk (see the worklist format in
Step 3).

### 1. Self-citations and the citation trail

- Direct self-reference: "as I have argued (Surname 2024)," "building
  on my earlier study," "we previously showed."
- Indirect trail: three citations to the same author across the
  framework signal advisor, collaborator, or self.
- **Decision rule:** *rewrite-as-other* is preferred when the sentence
  survives it — "as Surname (2024) argues" reads anonymously if nothing
  else links you. *Mask* — "(Author, Year)" in text, stripped entry in
  the references — only when the citation context itself gives you away
  ("in the first study of this village..."). Masking removes
  information reviewers may need; use it sparingly and note each mask
  for the editor.

### 2. The field-site problem (anthropology's hardest case)

A described site — "eighteen months in a Pentecostal congregation in
Accra's Nima district" — cross-referenced with your prior publications
identifies you to any area specialist. Options, in order of preference:

1. Keep the site, and rewrite/mask the self-citations that link you to
   it (the site alone rarely identifies; site + trail does).
2. Generalize the smallest identifying detail ("a West African
   metropolis") only where it does not damage the ethnography — and
   flag every generalization for restoration.
3. Where the site *is* the identity (you are the only person who works
   there and reviewers know it), note this openly to the editor;
   double-anonymous review has known limits in small subfields, and
   editors handle this routinely.

### 3. Front and back matter

- **Acknowledgments**: remove entirely for review (restore later).
- **Funding**: grant numbers are lookup-able — replace with "[funding
  information removed for review]."
- **Ethics/IRB statements**: institution names and protocol numbers →
  "[institution] IRB protocol [number removed]."
- **Author bios, ORCID, correspondence details**: remove.

### 4. First-person research history

"My dissertation," "our lab," "in my earlier fieldwork," "the second
author's clinical experience" — rewrite to anonymous equivalents ("in
earlier fieldwork," "prior research") that preserve the epistemic claim
without the biography.

### 5. Positionality and reflexivity passages

The anthropological tension: reflexivity sections are identity-rich by
design, and gutting them damages the methodology. Options:

- Generalize to the categories doing analytical work: "as a researcher
  who shares the community's language but not its religion" usually
  survives anonymization; "as a Fulbright scholar from [university]"
  does not.
- Where the positionality is inseparable from identity, replace with
  "[positionality statement abbreviated for review]" and tell the
  editor — reviewers understand.

### 6. Coined terminology and signature moves

"What I have elsewhere called X" is a byline. So, more subtly, is
heavy use of a framework you are known for. Rewrite the phrase; where
the framework itself points at you, prefer rewrite-as-other citation
of the term's source.

### 7. Figures, maps, and images

- Map credits, base-map watermarks, institutional templates, photo
  credits ("photo by author" is fine; "photo: J. Smith" is not).
- Field photographs that show the researcher, their team, or
  identifiable named collaborators.
- Figure files carry their own metadata (see 9).

### 8. Links and repositories

- Data/code repository URLs containing usernames (OSF, GitHub) →
  anonymized view-only links (both platforms support them) or
  "[repository link removed for review]."
- Preprint of the same manuscript: flag as a policy question — a
  posted preprint breaks blindness by search, and journals differ on
  whether that matters.

### 9. File hygiene (the step everyone forgets)

- DOCX: author name in document properties, tracked-changes author
  tags, comment authors.
- PDF: producer metadata, embedded author fields.
- File name: `Artz_ms_v14.docx` defeats everything else. Name it
  `manuscript_anonymous.docx`.

## Step 2: The Insider Test (verification pass)

After the fixes: read the manuscript as the two or three people most
likely to review it — the area specialist, the subfield theorist, your
methodological neighbor. What combination of site, method, framework,
and citation pattern still triangulates to you? Anything that survives
goes back on the worklist or into the editor note.

## Step 3: The Deliverable — Anonymization Worklist

Produce the worklist as a table the author works through top-down:

| # | Location | Item | Reveals | Risk | Action | Replacement text | Restore note |
|---|----------|------|---------|------|--------|------------------|--------------|
| 1 | p.2 ¶1 | "as I argued (Surname 2024)" | self-citation | High | Rewrite-as-other | "as Surname (2024) argues" | revert phrasing |
| 2 | p.4 ¶3 | "my dissertation fieldwork" | research history | High | Rewrite | "dissertation fieldwork in the region" | restore "my" |
| 3 | Refs | Surname 2024 entry | trail | Med | Keep (reads as other after #1) | — | — |
| 4 | Acknowl. | full section | names, funders | High | Remove | "[removed for review]" | restore section |
| 5 | p.11 | OSF link with username | identity | High | Anonymized view link | anonymized URL | restore full link |

- **Risk**: High = identifies on its own or with one cross-reference;
  Med = contributes to triangulation; Low = cosmetic.
- Order the list: High first, then file hygiene (always), then Med.
- Keep the table itself OUT of the submission — it is the author's
  working document and the restoration map.

## Step 4: Restoration Map

Every action's "Restore note" column is the de-anonymization plan: on
acceptance, work the table bottom-up — restore acknowledgments,
funding, full citations, links, and positionality text, and verify no
"(Author, Year)" masks or "[removed for review]" placeholders survive
into proofs. The most common post-acceptance error is a surviving
mask; grep for "Author," "[removed," and "[details" before returning
the final files.

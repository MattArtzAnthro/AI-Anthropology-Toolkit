---
name: chicago-manual-of-style
description: >
  Use this skill whenever an anthropologist needs citations written, checked,
  or converted in Chicago style, or a Chicago editorial-style question
  settled. Triggers include: "Chicago style," "CMOS," "author-date,"
  "notes and bibliography," "footnotes," "endnotes," "shortened notes,"
  "ibid.," "References Cited," "AAA style," "format my reference list," "fix inconsistent
  citations," "convert my citations to Chicago," "how do I cite my field
  notes," "cite an interview I conducted," "cite an archival collection,"
  or a press or journal that requires
  Chicago. Covers both Chicago systems at the 18th edition, the edition
  differences that make old examples wrong, what AAA and other anthropology
  venues actually ask for, ethnographic sources Chicago has no template
  for, and the toolkit's citation formatter. Do NOT use for finding or
  screening sources (use literature-review), checking citations in a
  typeset proof (use proof-review), or masking self-citations for blind
  review (use review-anonymization).
---

# Chicago Style for Anthropologists

## Overview

Most anthropology is cited in Chicago author-date: the American
Anthropological Association's journals grew up on it, and the university
presses that publish ethnography mostly use one of the two Chicago systems.
This skill writes, checks, and converts citations in either system, and
answers the Chicago editorial questions that come up in anthropological
manuscripts.

Three things make this harder than looking up a template.

1. **Editions disagree.** The 18th edition (2024) changed rules that most
   examples online, and most anthropology style sheets, still show in their
   17th-edition form. An example copied from the wrong edition looks right
   and is wrong.
2. **"AAA style" is not one thing.** The legacy AAA style guide, Chicago
   author-date, and the house style of the journals' current publisher
   disagree on small points, and which one a venue wants is the venue's
   decision, stated in its author guidelines.
3. **Ethnographic sources have no Chicago template.** Field notes,
   interviews you conducted, oral histories, community knowledge, and
   participants' social media posts each raise a citation question that is
   also a confidentiality question.

This skill adopts no Friction by Design tier (Tier 3; see
`skills/DESIGN.md`): citation form is rule-checkable genre mechanics over a
factual record. The guardrails below do the boundary work. The one place a
judgment leaks is ethnographic sources, where how a participant is cited is
a consent decision, and the skill routes that decision rather than making
it.

## Quick Reference

| Task | Reference |
|------|-----------|
| Which system and edition, what a venue wants, AAA's position, the 17th/18th differences, the toolkit's CSL styles and their traps | Read `references/editions-and-venues.md` |
| Parenthetical (Author Year, page) citations and the reference list | Read `references/author-date.md` |
| Numbered notes, shortened notes, and the bibliography | Read `references/notes-bibliography.md` |
| Field notes, your own interviews, archives, oral histories, community knowledge, participants' posts, non-English and reprinted classics | Read `references/ethnographic-sources.md` |

Load one system file, not both. They cover the same source types, and a
manuscript is almost never in both systems.

## Workflow

### Step 1: Fix the target

Establish, in this order, what the citations must follow:

1. **The venue's author guidelines**, if there is a venue. A journal or press
   style sheet overrides Chicago wherever they differ.
2. **An existing manuscript's practice**, if the task is to extend or repair
   one. Consistency with the rest of the document matters more than the
   newest rule.
3. **Chicago 18th-edition author-date**, as the default for anthropology
   when nothing above settles it.

If the user says "AAA style" without a venue, read
`references/editions-and-venues.md` before producing anything: the phrase
names at least three different things.

### Step 2: Load one reference

`references/author-date.md` or `references/notes-bibliography.md`, plus
`references/ethnographic-sources.md` whenever the material includes field
notes, interviews, archives, or anything a participant produced.

### Step 3: Get the metadata right before the form

A perfectly formatted citation with the wrong year is worse than an ugly one
with the right year. For anything with a DOI, pull canonical metadata with
the toolkit's `search_crossref` tool, or render a draft with
`format_citation` / `format_citation_batch` (use `list_citation_styles` for
the exact style name). Those tools format what the registrar holds and do
not verify it: check the draft against the work itself, and expect the
registrar artifacts listed in `references/editions-and-venues.md`.

For books, chapters, archival items, and anything without a DOI, take the
metadata from the title page, the copyright page, or the finding aid, not
from memory.

### Step 4: Format, then reconcile

Format each entry, then reconcile the whole document: every in-text
citation or note must resolve to exactly one list entry, with matching
author spelling and year.

### Step 5: Quality check

- [ ] Every citation resolves to a list entry, and the years and name
      spellings match
- [ ] No place of publication for post-1900 books (18th-edition rule),
      unless the venue's style sheet asks for it
- [ ] Headline-style capitalization for English titles, sentence-style for
      titles in other languages
- [ ] Italics for whole works, quotation marks for parts
- [ ] DOIs as `https://doi.org/` links where they exist, in preference to
      database or publisher URLs
- [ ] Personal communications, your own field notes, and your own
      interviews stay in the text or a note, with no list entry
- [ ] Any *CMOS* paragraph number cited is labeled with its edition
- [ ] Nothing a participant said or posted is cited in a form that
      identifies them beyond what their consent covers

## Guardrails

- **Never fabricate a citation or fill a gap with a guess.** A missing page
  range, issue, or publisher is marked `[check: …]` and listed for the
  author. An invented detail in a reference list is a fabricated citation.
- **Never quote a *CMOS* paragraph number across editions.** The 18th
  edition renumbered the citation chapters. "*CMOS* 14.30" in an 18th-edition
  source is a different paragraph from 14.30 in the 17th.
- **The venue outranks Chicago.** Where a style sheet and the manual
  disagree, follow the style sheet and say so.
- **A participant's name in a citation is a disclosure.** Citing an
  interview, a post, or a recording by a real name, or in a form that a
  search engine can resolve to a person, is decided by the consent record,
  not by citation convention. Route it to the `informed-consent` skill when
  the consent scope is unclear.
- **Do not normalize away the author's choices.** Diacritics,
  transliteration systems, Indigenous-language spellings, and a community's
  preferred name for itself are kept as the author wrote them, even where a
  formatter or a database spells them differently.
- **Formatter output is a draft.** Say so when handing it over.

## Common Failure Modes

| Failure | Problem | Fix |
|---------|---------|-----|
| 17th-edition example copied into an 18th-edition list | Places of publication, chapter page ranges, or "et al." thresholds that the current edition changed | Check every pattern against `references/editions-and-venues.md` |
| "AAA style" from a 2009 guide | Colon page form `(Geertz 1973:12)`, unquoted article titles, year standing alone after the name | Ask which venue; default to Chicago author-date |
| The formatter's `american-anthropological-association` style used for a current submission | It renders the legacy AAA form, with the publisher inserted mid-entry and `dx.doi.org` links | Use `chicago-author-date` and adjust to the venue |
| Registrar metadata trusted | Annual volumes given an issue number, lowercase DOIs, titles in all caps, missing subtitles | Check against the work; fix in the entry |
| Interviews you conducted put in the reference list | Lists a participant (often by pseudonym) as an author and creates a findable entry | In-text or note only; describe the corpus in the methods section |
| Reprinted classic given only the reprint year | (Mauss 1990) reads as if the argument were from 1990 | Original year in brackets or parentheses as the system requires |
| Mixed systems | Some notes, some parenthetical citations | Pick one system for the document and convert the rest |
| Edition-blind "ibid." policy | House styles differ on it; Chicago discourages it in favor of shortened notes | Follow the venue; otherwise use shortened notes |

## Relation to Other Skills

- `research-writing` drafts the article; this skill handles its citation
  form.
- `literature-review` finds, screens, and synthesizes sources; this skill
  formats what it found.
- `proof-review` audits citations in a publisher's typeset proof against the
  submitted manuscript, which is a comparison task, not a formatting one.
- `review-anonymization` masks self-citations for double-anonymized review;
  format the master first, then anonymize the copy.
- `informed-consent` holds the decision about how a participant may be
  named, which this skill's ethnographic-sources guidance defers to.

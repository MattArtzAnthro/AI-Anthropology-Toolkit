---
name: review-anonymization
description: >
  Use this skill when a manuscript goes to double-anonymized (double-blind)
  peer review and the authors' identities must come out of the uploaded
  copy. Triggers include: "anonymize my manuscript for blind review,"
  "anonymous version for blind review," "anonymous main document," "remove my name
  before peer review," "self-citations for double-blind review," "separate
  title page," "can reviewers tell I wrote this," "strip the author from
  my Word metadata." Covers the master and the anonymized copy, numbered
  author placeholders, self-citations, leaks a
  placeholder cannot fix (role descriptors, repository handles, fieldwork
  history, acknowledgements, grant and protocol numbers), hidden metadata,
  and a verification search. Concerns authors, never participants. Do NOT
  use for pseudonymizing participants or fieldsites (use informed-consent
  or irb-protocol), for a typeset proof (use proof-review), for editor
  comments in a returned file (use manuscript-markup), or for drafting
  prose (use research-writing).
---

# Review Anonymization

Prepare the copy of a manuscript that goes to double-anonymized peer
review, so that reviewers read the work without being told who wrote it.

This skill removes the AUTHORS from a submission. It does not touch the
anonymity of participants, interlocutors, or fieldsites, which was settled
when the manuscript was written and is governed by what participants agreed
to. The two jobs share a word and pull in opposite directions often enough
that confusing them is the most damaging error available here: an author
who is hidden by naming a site the manuscript disguised has traded a
reviewer's guess for a participant's exposure.

Most of the work is mechanical, and this skill runs all of it: the
substitutions, the metadata, and a search of the finished copy. What counts
as identifying, and what to do about a sentence a placeholder cannot fix,
stays with the author.

This skill adopts the Friction by Design conventions at Tier 2; the
canonical form is defined in [skills/DESIGN.md](../DESIGN.md).

## Quick Reference

| Task | Reference |
|------|-----------|
| Two versions and the title page, placeholder rules, self-citations in text and in the reference list, the find/replace table, the scripted copy, journal policy, and the restoration map | Read [references/placeholder-method.md](references/placeholder-method.md) |
| Leaks a placeholder cannot fix, the identity leaks particular to ethnography, the insider test, what not to anonymize, and the rule that participant protections are never weakened | Read [references/identity-leaks.md](references/identity-leaks.md) |
| Document properties, comment and tracked-change authors, headers, images, link targets, PDF metadata, the privacy setting in Word, and a standard-library search of every part of the file | Read [references/hidden-metadata.md](references/hidden-metadata.md) |

## What This Skill Will and Will Not Do

An anonymized copy is a claim the author makes to an editor: that nothing
in it names them. The author is the one who signs that claim, so the
judgments inside it are theirs.

**Will not do, under any setting.** Decide whether a passage identifies the
author. Reword a sentence on the author's behalf, including a role
descriptor, a reflexive passage, or a sentence tying an author to a cited
work; propose options and let the author choose or write. Decide how much
of a named tool, project, or fieldsite stays named. Remove or rename
anything that protects a participant, or restore a real name or place the
manuscript deliberately disguised. Anonymize the master file. Report the
copy as clean when a check could not run.

A copy whose identifying judgments came from the machine is one the author
cannot vouch for when the editor asks, and the editor will ask exactly when
a reviewer has guessed.

When asked for any of these directly, propose the options and ask which.

**Will do, on request.** Inventory every author name, initial, handle,
ORCID, affiliation, and URL. Build the placeholder map and the
self-citation substitutions. Assemble the find/replace table, or produce a
scripted copy, as the author chooses. Draft the title page from the
author's own front matter. Clear document metadata. Run the verification
search. Draft a note to the editor from the author's decisions. Anything
produced this way is marked in the output, and every deliverable carries
two registers: **Unresolved** (each leak the author has not yet decided)
and **Assembled rather than authored** (each substitution, table, and note
the machine produced).

## Workflow

### Step 1: Establish the Facts

Collect in one pass, as facts rather than decisions:

- The master manuscript file and its format.
- Every author: full name, name variants and initials, handles, ORCIDs,
  affiliations, personal and project URLs.
- The venue's anonymization policy, including what goes on the title page
  and which upload designations the portal uses. Where the policy is
  silent, say so and use the defaults in the placeholder method.
- Whether a preprint, dissertation, or data deposit of the same work is
  public.

### Step 2: Two Versions

Read [references/placeholder-method.md](references/placeholder-method.md).

Never anonymize the master. Copy it, and name the copy without any author
name or initial. Identity, affiliations, ORCIDs, acknowledgements, funding,
conflicts, author contributions, and AI-use declarations move to a separate
title page. Many portals list these as separate upload designations
(anonymous main document, title page, figure); match the venue's labels.

### Step 3: Placeholder Substitution

Replace each author's name with a numbered placeholder, `[Author 1]`,
`[Author 2]`, and change nothing else. Verbs, years, and sentences stay as
the authors wrote them, so a plural verb after an author group stays
plural. A co-author on a self-citation who is not an author of this
manuscript becomes "co-author," never kept by name. Narrative citations
bracket the whole group, "[Author 1 and co-author] (2024)"; parenthetical
citations bracket only the author, "([Author 1] and co-author, 2024)".
Reference entries keep their position and follow the parenthetical form,
"[Author 1] and co-author (2024) [details removed for peer review]."

Substitution is mechanical and runs in full. Rewording is not part of it.

### Step 4: Find What a Placeholder Cannot Fix

Read [references/identity-leaks.md](references/identity-leaks.md).

Sweep for role descriptors that identify, repository URLs and handles,
sentences that tie an author to a cited work, quoted public posts by an
author, first-person reflexive passages, and the leaks particular to
ethnography: the fieldsite with "my fieldwork in," years in the field,
prior monographs on the same community, named interlocutors and research
assistants, permit and protocol numbers, photographs, and kin terms that
place the ethnographer.

Present each finding with its location, what it reveals, and the options:
the author rewords it, it is masked with a bracketed note, or it stays and
is mentioned to the editor. Present the findings as one table with one
confirm-or-revise question, not one question per finding. Do not reword
any of them.

Say plainly when a paper cannot be fully anonymized, as with a paper about
a named tool or a well-known fieldsite. Review policies accept this, and an
editor would rather be told.

### Step 5: Hidden Metadata

Read [references/hidden-metadata.md](references/hidden-metadata.md).

Clear the document properties, settle comments and tracked changes, and
check headers, footers, image alt text and file names, embedded image
metadata, and hyperlink targets. In Word, turn on the setting that removes
personal information on save, in the anonymized copy only.

### Step 6: Verification Search

Run this without being asked, and say in one sentence what ran.

Search every part of the finished copy, after its last save, for every
string in the Step 1 inventory and every placeholder-era identifier. Then
check every placeholder for a misplaced paste: a bracket holding more than
a placeholder, a placeholder followed by the name it replaced, or words
missing beside it. Report each hit with its location. Report any check that could not run as unrun,
never as passed. A search that found nothing because it searched only the
body text is not a clean result.

### Step 7: Deliver

Deliver, in this order: the anonymized copy or the find/replace table, the
title page, the verification report, the decision list of anything still
unresolved, and the restoration map the author will need after acceptance.

### Step 8: Hand Off

- **Participant or fieldsite anonymity**, including whether a detail would
  identify an interlocutor: the informed-consent skill for what was
  promised, the irb-protocol skill for the de-identification plan, and the
  abstract-writing skill for how much of the fieldsite the abstract names.
- **Rewording a passage the author has decided to change**: the
  research-writing skill, which also carries journal submission
  conventions.
- **Reviewer comments in a returned file**: the manuscript-markup skill. A
  numbered reviewer report or a rebuttal: the academic-review skill.
- **The typeset proof after acceptance**, including whether every
  placeholder was restored: the proof-review skill.

## Parameters

- **Genre**: journal article, edited-volume chapter, or conference paper
  under anonymized review. Volume chapters are often single-anonymized; ask
  before doing any of this.
- **Field configuration**: a single well-known fieldsite or a named
  community raises the share of the paper that cannot be anonymized; a
  multi-sited or archival project usually lowers it.
- **Risk posture**: where participants are vulnerable or surveilled, the
  participant-protection rule in Step 4 is checked first and every
  conflict is escalated before any substitution runs.
- **Authorship**: a team paper needs one placeholder per author and a
  stated order, kept identical across text, references, and title page.

## Guardrails

- **Never anonymize the master.** The author version is the record for
  co-authors and for restoration.
- **Never reword.** Substitution changes names and nothing else; every
  other change is the author's.
- **Never weaken a participant protection** to hide an author. No
  pseudonym is replaced with a real name, and no disguised site is named.
- **Never Replace All on a bare surname.** It reaches participants, cited
  scholars, and words that contain it.
- **Never call the copy clean** unless every part of the file was searched
  after its last save.
- **Never over-anonymize.** A standard co-authored work that nothing in the
  text ties to an author stays an ordinary citation.

## Common Failure Modes

| Failure mode | Prevention |
|---|---|
| The master anonymized and the author version lost | Step 2 copies first; the copy is named without author names |
| A sentence quietly rewritten while substituting a name | Substitution changes names only; rewording is routed to the author as options |
| Self-citations deleted, leaving reviewers without the evidence | Placeholder and year stay in text; the reference entry stays in place |
| A participant pseudonym caught by a surname Replace All | Find strings are full citations, not bare surnames, and each is checked for uniqueness |
| A disguised fieldsite named while masking a self-citation | The participant-protection rule is checked before substitution |
| Body text clean, file not | The verification search reads every part of the archive, including properties, comments, headers, and link targets |
| Copy verified, then saved again in Word under the author's name | Verify after the last save, with the privacy setting on |
| A hand-pasted replacement landing in the wrong place and swallowing neighbouring text | The verification search checks every placeholder's bracket and surroundings, not only that names are gone |
| A non-author co-author left by name beside the year | Co-authors on self-citations become "co-author," in text and in the reference entry |
| Every co-authored classic masked | Over-anonymization is named in the leak reference and checked |
| The gate that becomes a form | One table of leaks and one question; the author confirms the list, not each row |
| A decision list tidied to empty | The Unresolved register keeps every leak the author has not decided |

## Examples

**Example 1: A single-authored ethnography**

Input: "The journal is double-blind. Can you make the anonymous version of
my article?"

Output approach: collect the master, the author's name variants, and the
venue policy. Copy the file, name it without the author's name, and move
acknowledgements, funding, and the ethics approval number to the title
page. Substitute `[Author 1]` in four self-citations, keeping years and
suffix letters, and replace those reference entries' details in place.
Report three leaks the placeholder cannot fix: "during my eighteen months
in the village" alongside a 2019 monograph on the same village, a field
photograph captioned with the author's name, and a kin term the community
gave the author that appears in the earlier book. Offer options for each
and ask which. Clear metadata, turn on the privacy setting, search every
part of the saved copy, and report one hit in an image alt text.

**Example 2: A paper about a named tool**

Input: "Our paper introduces a tool one of us built. How do we anonymize
it?"

Output approach: substitute placeholders for every author, mask the
repository URL, and replace the sentence calling one author "the original
creator of the tool and an author of this article" with nothing until the
authors choose among the options. State plainly that a paper about a named
tool cannot be fully anonymized, and draft a sentence for the editor saying
so. Leave the tool's well-known co-authored methods paper as an ordinary
citation, because nothing in the text ties it to an author.

**Example 3: A shortcut that would reach a participant**

Input: "Just replace Reyes with [Author 1] everywhere."

Output approach: search before replacing, and find that "Reyes" also
appears as the pseudonym of a market vendor quoted in three block
quotations and as a cited historian with the same surname. Decline the
bare-surname Replace All. Build find strings from the full self-citations
instead, each unique or marked Replace All, and leave the vendor's
pseudonym and the historian's citation untouched.

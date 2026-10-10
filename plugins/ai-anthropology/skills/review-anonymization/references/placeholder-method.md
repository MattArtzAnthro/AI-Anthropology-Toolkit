# The Placeholder Method

Reference file for the review-anonymization skill. Loaded when setting up
the two versions, building the substitutions, and choosing how they are
applied.

The method has one rule that everything else serves: **substitute, do not
rewrite.** A name becomes a placeholder and nothing else changes. The
author's sentences, verbs, and years survive intact, so the anonymized copy
is the same paper with the names taken out, and restoring it later is the
same operation in reverse.

---

## 1. Check the Venue's Policy First

Read the submission guidelines and record the venue's rules at the top of
the worklist. Policies differ on:

- Whether self-citations are masked as placeholders or kept in the third
  person. This method masks; where a venue asks for third person instead,
  the author decides how each sentence reads, and the skill does not
  reword them.
- What the title page carries, and whether ethics, funding, and data
  statements stay in the main document in anonymized form or move to the
  title page.
- Whether the portal checks file metadata. Assume it does.
- Whether a posted preprint of the same manuscript is acceptable.

Where the guidelines are silent, use the defaults below and say that they
are defaults.

## 2. Two Versions

| | Master (author version) | Anonymized copy |
|---|---|---|
| Purpose | The record: for co-authors, for restoration, for later reuse | The upload |
| Names | Present | Placeholders |
| File name | Whatever the author uses | No author name or initial, e.g. `manuscript-anonymized.docx` |
| Metadata | Untouched | Cleared, privacy setting on |
| Edited by this method | Never | Yes |

Make the copy before changing anything. All later edits to the argument go
into the master and are carried to the copy, never the other way round; a
copy that has drifted from its master cannot be restored cleanly.

### The title page

A separate file holding everything that identifies the authors:

- Title, author names in order, affiliations, ORCIDs, corresponding author
  and contact details.
- Acknowledgements, including communities, research assistants,
  transcribers, and hosts.
- Funding, with funder names and grant numbers.
- Conflicts of interest, author contributions, and any AI-use declaration.
- Ethics approval with the institution and protocol number, and research
  permit numbers, unless the venue asks for an anonymized statement in the
  main document instead.

Portals often list these as separate upload designations, for example
"Anonymous Main Document," "Title Page," "Figure." Use the venue's own
labels.

## 3. The Placeholder Map

One numbered placeholder per author, in authorship order:

| Author (master) | Variants found | Placeholder |
|---|---|---|
| Dana Reyes | Reyes, D. Reyes, D.R., @dreyes | `[Author 1]` |
| Tomas Lindqvist | Lindqvist, T. Lindqvist, T.L. | `[Author 2]` |

The placeholder replaces the name and only the name. A sentence such as
"Reyes (2021) argues that ..." becomes "[Author 1] (2021) argues that
...", with the verb, tense, and year unchanged. If the result reads oddly,
that is a decision for the author, not a reason to rewrite.

Keep the map out of the submission. It is the author's working document
and half of the restoration map.

## 4. Self-Citations

**In text.** Swap the author's name for the placeholder and keep the
years, suffix letters, and page numbers. A co-author on a self-citation
who is not an author of this manuscript is anonymized too, as
"co-author," never kept by name: their name next to the year points back
at the paper as surely as the author's would.

The bracket follows the citation form:

- **Narrative citations** put the whole author group in one bracket:
  "[Author 1 and co-author] (2024) draw on ..."
- **Parenthetical citations** bracket only the author: "([Author 1] and
  co-author, 2024)."

| Master | Anonymized |
|---|---|
| (Reyes 2021) | ([Author 1] 2021) |
| (Lindqvist and Okafor, 2024) | ([Author 2] and co-author, 2024) |
| Lindqvist and Okafor (2024) draw on | [Author 2 and co-author] (2024) draw on |
| (Reyes 2019a, 2019b) | ([Author 1] 2019a, 2019b) |
| Reyes et al. (2022, 14) | [Author 1 et al.] (2022, 14) |
| (Reyes and Lindqvist 2023) | ([Author 1] and [Author 2] 2023) |

Verbs stay as written. "Lindqvist and Okafor (2024) draw on" keeps the
plural "draw," because the group is still plural; the placeholder changes
the names, not the grammar.

**In the reference list.** Keep the entry in its place. Do not reorder the
list, and do not delete the entry. Entries follow the parenthetical form:
the placeholder, "co-author" for any non-author co-author, the year, and
the remaining details replaced:

```
[Author 1] (2021) [details removed for peer review].
[Author 2] and co-author (2024) [details removed for peer review].
```

Leaving the entry in place keeps the copy aligned with the master, so
restoration is a line-for-line swap.

**Repeated identical citations.** A citation that appears several times
with identical text needs Replace All on that exact string. Mark it so in
the table, and give the count found.

**Co-authored works that stay ordinary citations.** A well-known
multi-author work that an author contributed to stays as it is when
nothing in the text ties it to an author. See the over-anonymization
section of [identity-leaks.md](identity-leaks.md).

## 5. Applying the Substitutions

The author chooses one of two forms.

### Form A: Find/replace pairs the author pastes

```markdown
| # | Location | Find (verbatim) | Replace with | Scope | Count found |
|---|----------|-----------------|--------------|-------|-------------|
| 1 | Refs | Reyes, Dana. 2021. Market Days ... | [Author 1] (2021) [details removed for peer review]. | Once | 1 |
| 2 | Body | (Reyes 2021) | ([Author 1] 2021) | Replace All | 4 |
```

Rules for building the table:

- **Copy every find string verbatim from a plain-text export** of the
  master, not from memory and not from a rendered view. Curly quotes,
  non-breaking spaces, en dashes in page ranges, and soft hyphens all have
  to match, or Word reports zero matches and the author assumes the string
  is absent.
- **Each find string is unique in the document** unless marked Replace
  All, and the count found is stated so the author can confirm Word's
  count against it.
- **Order longest first.** Replace a full reference entry before a short
  citation that it contains, so a short replacement does not break a long
  find string.
- **Never use a bare surname as a find string.** It reaches participant
  pseudonyms, cited scholars who share the name, and words that contain
  it. Use the whole citation or the whole phrase.
- **Use Match Case** and, for short strings, Find Whole Words Only.
- **Expect a paste to land in the wrong place.** Applied by hand, a
  replacement pasted with the cursor in the wrong spot swallows the
  neighbouring text or lands beside the string it was meant to replace.
  The verification search looks for exactly this: a bracket holding more
  than a placeholder, a placeholder followed by the name it replaced, and
  a sentence that lost words next to a placeholder.

### Form B: A scripted copy

A script makes the copy, applies the same table, and reports. It must:

- Read the master and write a new file; it never writes to the master.
- Apply exactly the substitutions in the table, and nothing else.
- Report every find string it could not locate, rather than skipping it.
  Word splits text into runs at formatting and editing boundaries, so a
  string visible on the page may be split in the XML; a miss is reported
  for the author to apply by hand.
- Clear the document properties explicitly. Editing an existing file keeps
  its fields; see [hidden-metadata.md](hidden-metadata.md).
- End by running the verification search.

Either way, the result is assembled rather than authored, and the
deliverable says so.

## 6. The Decision List

Every leak the placeholder could not fix, with its location, what it
reveals, the options offered, and the author's choice:

```markdown
| # | Location | Passage | Reveals | Options | Author's decision |
|---|----------|---------|---------|---------|-------------------|
```

Options are of three kinds: the author rewords it, it is masked with a
bracketed note such as `[sentence removed for peer review]`, or it stays
and is mentioned to the editor. Rows without a decision stay in the
Unresolved register.

## 7. The Note to the Editor

Where something cannot be anonymized, a short note in the cover letter
says so: a paper about a named tool, a fieldsite few people work in, a
preprint already posted. Draft it from the author's decisions and mark it
assembled. Editors handle these routinely; an unexplained leak a reviewer
finds is worse than a disclosed one.

## 8. The Restoration Map

After acceptance, the placeholder map, the find/replace table, and the
decision list run in reverse: restore names, reference details,
acknowledgements, funding, ethics statements, links, and every masked or
removed passage. Restore into the master's text, not into a reconstruction
of it.

Before returning final files, search for `[Author`, `[details removed`,
`[sentence removed`, and `removed for peer review`. A surviving placeholder
in the published article is the most common error at this stage. Search
again when the proof arrives, alongside the proof-review skill's audit.

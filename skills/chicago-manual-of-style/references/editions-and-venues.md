# Editions and Venues

Read this before producing citations for a venue you have not confirmed, and
whenever someone says "AAA style."

## Choosing a system

Chicago has two systems that style every source component identically and
differ only in how the text points to the source.

- **Author-date.** A parenthetical `(Geertz 1973, 12)` in the text and an
  alphabetical reference list. The default for anthropology: American
  Anthropologist, American Ethnologist, Cultural Anthropology, and most
  social-science venues use a variant of it.
- **Notes and bibliography.** Numbered footnotes or endnotes and, usually, an
  alphabetical bibliography. Common in historical anthropology, in edited
  volumes from humanities-leaning presses, and wherever sources are archival,
  unpublished, or need a sentence of commentary that a parenthesis cannot
  carry.

A manuscript can use author-date and still carry discursive footnotes. What
it cannot do is cite sources in both systems.

Because the components are the same, converting between systems is
mechanical: move the year to follow the author's name (author-date) or to
the end of the publication facts (notes and bibliography), change the
punctuation between elements, and change the indentation. Names, titles,
and publication facts do not change.

## The 18th edition and the 17th

The 18th edition (2024) is current. The 17th (2017) is still what most
departmental handouts, library guides, and older style sheets show. Where
they conflict, follow the 18th unless the venue specifies the 17th.

**Paragraph numbers.** The 18th edition reorganized the citation chapters,
so a paragraph number does not carry between editions. Always label a
*CMOS* paragraph reference with its edition, and never look up a number
from one edition in the other.

**Changes that make old examples wrong:**

| Point | 17th edition | 18th edition |
|---|---|---|
| Place of publication for books | Given before the publisher | Omitted; publisher and year only. Books published before 1900 still give the place, which stands in for the publisher |
| Page range of a chapter in an edited book | Given in the list entry | No longer required in the list entry; cite the specific pages in the note or the parenthetical |
| "Et al." in author-date text citations | Used from four authors | Used from three authors |
| Many-author list entries | All authors listed up to ten | All authors listed up to six; for seven or more, the first three and "et al." |

Confirm the two "et al." rows against the 18th edition itself before
enforcing them on someone else's reference list: they are the kind of
detail a venue's own style sheet often overrides.

**Unchanged:** name order, headline-style capitalization of English titles,
italics for whole works and quotation marks for parts, shortened notes, the
preference for DOIs over database URLs, and the treatment of personal
communications.

## What "AAA style" means

There is no single current answer, and the skill should not pretend there is.

- **The legacy AAA style guide** (editions through the 2000s and 2010s, still
  circulating as PDFs and in syllabi) used a colon between year and page,
  `(Geertz 1973:12)`, headed the list "References Cited," and differed from
  Chicago in punctuation within entries.
- **Chicago author-date** is what library guides and AAA's own guidance now
  point students to when they are told to use "AAA style." As reported by
  library guides in 2026, the association's publishing style page says it
  does not require a specific citation style for its journals and points to
  Chicago author-date as the nearest match to the traditional conventions.
  The page could not be read directly when this file was written, so confirm
  against it.
- **The publisher's house style.** Journals published by Wiley apply their
  own in-text conventions on top of Chicago; one library guide reports a
  comma after the author name, `(Herzfeld, 2005, 146–47)`, and no original
  date for reprinted books.

The rule that follows: for a submission, use the journal's current author
guidelines. For coursework, ask the instructor; if no one specifies, use
Chicago 18th-edition author-date, comma before the page, list headed
"References Cited" (the anthropological convention) or "References."

## Other anthropology venues

Many venues have their own author-date house style rather than Chicago:
the Journal of the Royal Anthropological Institute, Social Anthropology,
Focaal, and others. The formatter ships CSL styles for several of these
(`list_citation_styles` with `contains="anthropolog"`). Treat them as drafts
and check against the journal's current guidelines; a CSL style can lag a
journal's changes by years.

## The toolkit's formatter

`format_citation` and `format_citation_batch` render a DOI in any CSL style
through the DOI Foundation's formatter. `list_citation_styles` finds the
exact name; near-misses are rejected.

Useful names, as shipped in 2026:

| Style name | What it produces |
|---|---|
| `chicago-author-date` | Current Chicago author-date |
| `chicago-author-date-17th-edition` | The previous edition, for a venue that still requires it |
| `chicago-notes-bibliography` | Current notes and bibliography (bibliography form) |
| `chicago-shortened-notes-bibliography` | Notes and bibliography with shortened notes |
| `american-anthropological-association` | **The legacy AAA form**, not a current venue's |

**The `american-anthropological-association` trap.** Tested on George
Marcus's 1995 Annual Review article, it produced: no period after the year,
no quotation marks around the article title, the publisher name inserted
between the issue and the pages ("Annual Reviews: 95–117"), and a
`dx.doi.org` link. That matches no current anthropology journal. Use
`chicago-author-date` and adjust to the venue.

**Registrar artifacts to check in every rendered entry:**

- **Issue numbers on annual volumes.** Annual Review of Anthropology came
  back as "24 (1)". An issue number on an annual volume is usually a
  registrar artifact; check the journal.
- **DOI case.** `chicago-author-date` lowercased the Ortner DOI
  (`10.1017/s0010417500010811`). DOIs are case-insensitive, so the link
  works, but keep the registered form.
- **Titles.** Registrars hold titles in whatever case the publisher sent,
  sometimes all capitals, sometimes without the subtitle. Restore the title
  from the work.
- **Names.** Diacritics, particles (de, van, al-), and compound surnames are
  often mangled. Restore them from the work.
- **Books and chapters.** Book DOIs are sparse and chapter metadata is often
  missing editors. Take book metadata from the copyright page.

The batch tool renders entries but does not build a bibliography: it does
not sort, and it does not add the "a" and "b" suffixes that distinguish two
works by one author in one year. Say so when handing over its output.

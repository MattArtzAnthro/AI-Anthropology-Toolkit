# Comparison Method

How to compare a typeset proof against a submitted manuscript: the
governing rule, the two channels, what falls in scope, the literal
checklists, the normalization rules that keep typesetting out of the
report, and the visual inspection of rendered pages.

## Governing Comparison Rule

Treat the Word manuscript as the source text, with all tracked changes
treated as accepted unless the author instructs otherwise.

Compare the final intended wording of the manuscript against the wording
and presentation in the proof. Do not compare tracked-change markup,
deleted text, comments, or hidden revision metadata unless they remain
unresolved or affect the intended manuscript.

Where a copyedited version exists between the two, the manuscript remains
the source text and the copyedit becomes evidence of when a change entered.
A change the author accepted at copyedit is not a proof error, and saying
so keeps the correction list credible.

## The Three Reads

Use all three:

- **Text extraction** for exact textual comparison.
- **Rendered PDF pages** for visual and typesetting inspection.
- **The PDF annotation layer**, read separately from the page content.

The third is easy to forget and changes what the other two mean. A proof
can carry annotations from two directions: the publisher's author queries,
which some presses deliver as sticky notes rather than as printed marginal
text, and the author's own in-progress corrections from an earlier sitting.
Read the annotation layer before the pages, list what is there with its
author, and keep the author's own marks out of the findings — a mark the
author already made is not a discrepancy the audit discovered, and
reporting it back to them as one wastes the review.

Annotations that strike through or replace text also change what the
rendered page appears to say, so an audit that reads the pages without
reading the annotation layer will misread struck text as printed text.

Do not rely solely on PDF text extraction. Line breaks, ligatures,
discretionary hyphens, and embedded figures produce misleading results:
extraction invents spaces, drops soft hyphens inconsistently, decomposes
or recomposes accented characters, reorders text in multi-column and
floated layouts, and returns nothing at all for text baked into a figure.

The rule that follows: **a finding produced by extraction alone is
confirmed on the rendered page before it enters the report.** Most false
positives in a proof audit are extraction artifacts, and a correction list
containing them costs the author credibility with the press.

Three extraction hazards recur and are worth handling before any diff
rather than debugging afterwards:

- **Running heads and folios.** There are usually two running heads, one
  on the verso and one on the recto, and they carry different text: the
  book or part title on one side, the chapter or author on the other.
  Identify both and remove them along with the page numbers before
  comparing, or every page boundary produces a phantom insertion.
- **Marginal queries.** A query set in the margin extracts as text
  interleaved into the body stream at whatever vertical position it sits,
  which splits the sentence or reference it lands beside. Pull marginal
  material out and audit it separately rather than letting it corrupt the
  diff.
- **Italics and bold do not survive plain-text extraction at all.** A
  formatting comparison has to read the source document's run properties,
  not its extracted text. Without that, a journal title the publisher
  failed to italicize and one the author never italicized look identical,
  and they are different findings with different corrections.

The converse also holds. Extraction catches what the eye does not: a
changed digit, a dropped article, a duplicated word across a page break.
Neither channel is sufficient.

## Scope Inventory

Check every part of both documents:

- Chapter number
- Title and subtitle
- Author name
- Author affiliation
- ORCID
- Abstract
- Keywords
- Contributor biography
- Acknowledgments
- Headings and subheadings
- Main body text
- Block quotations
- Lists
- Tables
- Table headings and notes
- Figures
- Figure captions
- Figure callouts
- Figure numbering
- Alt text
- Footnotes and endnotes
- Cross-references
- In-text citations
- Reference list
- URLs and DOIs
- Author queries
- Editorial notes
- Compositor instructions
- Running heads
- Page headers and footers
- Chapter pagination
- Copyright and licensing statements

Front matter, the contributor biography, the acknowledgments, and the
running heads are checked first rather than last. They carry the errors
that survive longest, because they are the parts nobody reads at proof
stage and nobody can correct after.

## Literal Textual Comparison

Compare the documents word for word and character for character.

Check:

- Words and phrases
- Word order
- Missing or duplicated words
- Added or deleted sentences
- Spelling
- Capitalization
- Singular and plural forms
- Verb tense
- Articles and prepositions
- Numbers
- Dates
- Percentages
- Units
- Initials
- Names
- Titles
- Citation years
- Page numbers
- Figure and table numbers
- URLs
- DOIs

Also compare every punctuation mark and typographic feature:

- Periods
- Commas
- Semicolons
- Colons
- Question marks
- Exclamation marks
- Apostrophes
- Quotation marks
- Parentheses
- Brackets
- Ellipses
- Hyphens
- En dashes
- Em dashes
- Slashes
- Italics
- Boldface
- Superscripts
- Subscripts
- Special symbols
- Accented characters
- Nonbreaking spaces

## Normalization Rules

Do not report differences caused solely by:

- PDF line wrapping
- Page breaks
- Justification
- Word spacing introduced by typesetting
- Automatic end-of-line hyphenation
- Font substitution
- Ligature encoding
- Soft hyphens
- Differences between ordinary and nonbreaking spaces
- Changes from straight to typographic quotation marks
- Changes from hyphens to en dashes in numerical ranges
- Other purely mechanical typesetting conversions that do not affect the
  displayed wording or meaning

**The exception.** Report a hyphenation or dash change when it alters a
compound term, proper noun, citation, number, meaning, or established
spelling. This exception is where real errors hide inside a rule written
to suppress noise. A double-barrelled surname collapsed to a single
hyphenated form, a page range that became a date range, a compound whose
meaning turns on the hyphen: each of these arrives looking exactly like
the mechanical conversions above.

**URLs and DOIs are exempt from the de-hyphenation rule.** Never resolve a
line-break hyphen inside a URL or DOI from extraction. Suppressing it
silently deletes a hyphen that may belong to the address, and reporting it
invents a broken link that is not broken. Both errors are common and both
are expensive: one lets a dead link reach print, the other puts a false
finding in front of the press. Every URL or DOI that breaks across a line
is resolved by reading the rendered page, character by character, and if it
cannot be read reliably it goes in the **Not examined** register rather
than being guessed either way. The same applies to the space that
extraction inserts at a URL's wrap point.

**Font substitution has a matching exception.** Suppress it as a
difference in typeface. Report it when a glyph changed identity: a
character that fell back to a different codepoint, dropped entirely, or
rendered as a box, a question mark, or a substitute letter. See
[ethnographic-integrity.md](ethnographic-integrity.md), where this is the
common failure for orthographies outside the compositor's default font.

**House style is not automatically correct.** Determine whether each
change is harmless, inconsistent, grammatically questionable, or
substantively incorrect. Consistency establishes that a change was
intentional; it does not establish that it was right.

## Alt-Text Rule

Check that figure alt text is complete, accurate, and associated with the
correct figure.

Do **not** automatically classify alt text printed visibly on the page as
a production error. Report it only as an item for confirmation when:

- It appears accidentally placed
- It interrupts the argument
- It duplicates a caption unnecessarily
- It conflicts with the publisher's stated production conventions
- It contains errors
- Its visible placement appears inconsistent with the rest of the volume

Otherwise, note it without recommending removal.

## Visual Proof Inspection

Inspect every rendered page for production problems:

- Missing text
- Duplicated text
- Clipped text
- Overlapping elements
- Broken characters
- Incorrect glyphs
- Excessive or missing spaces
- Awkward word breaks
- Widows and orphans
- Stranded headings
- Incorrect indentation
- Inconsistent heading levels
- Unbalanced page layout
- Missing figures
- Low-resolution figures
- Illegible labels
- Distorted figures
- Incorrect figure placement
- Incorrect captions
- Captions separated from their figures
- Incorrect table layout
- Broken URLs
- Margin notes accidentally left in place
- Author queries that remain unresolved
- Compositor instructions printed as publication text

Do not confuse crop marks, printer marks, proofing marks, or normal
publication furniture with errors.

Two of these recur and warrant naming. **Unresolved author queries** and
**compositor instructions printed as publication text** are the production
faults most likely to reach print, because each looks like it belongs to
someone else's stage of the process. Both are checked for by name rather
than noticed in passing.

Any page, figure, or table that cannot be examined reliably goes in the
report's **Not examined** register. It is not silently skipped, and its
presence means the audit is not described as complete.

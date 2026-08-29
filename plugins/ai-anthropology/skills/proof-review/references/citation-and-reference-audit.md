# Citation and Reference Audit

Proof stage is the last chance to catch a citation error and the stage at
which citation errors are most likely to have been introduced, because a
citation-style conversion touches every citation in the chapter at once.

The audit runs in two directions and against two sources: each citation
against the manuscript, and each citation against the reference list.

## Citation Audit

Check every in-text citation against both the manuscript and the reference
list.

Verify:

- Author names
- Author order
- Spelling
- Year
- Letter suffixes such as 2024a and 2024b
- Use of "and" versus "et al."
- Page references
- Multiple citations within one parenthesis
- Citation order
- Correspondence between citations and references

Identify:

- Citations present in the text but absent from the reference list
- References present in the reference list but never cited
- Citations whose author names or years do not match their reference
  entries
- Incorrect shortening of two-author citations to "et al."
- Inconsistent treatment of three-author or multi-author citations

**Do not flag a consistent conversion to publisher citation style unless
it introduces an error or inconsistency.** A press converting author-date
to a numbered system, or applying its own et al. threshold uniformly, is
doing its job. Report it once as a category 5 change so the author can see
it, not once per citation.

The conversions that do introduce errors are specific and worth checking
for by name:

- **An et al. threshold applied to a two-author citation**, which
  misattributes the work to the first author alone.
- **Letter suffixes lost or reassigned** when a style conversion re-sorted
  the reference list. Two 2024 entries by one author whose a and b were
  swapped will still look internally consistent and will point every
  in-text citation at the wrong work.
- **Compound and non-Western surnames split or reordered.** A conversion
  that treats a patronymic, a double-barrelled surname, a particle such as
  van or de, or a name whose family element comes first as though it were
  a Western given-name-then-surname pair will produce a wrong citation and
  a wrong alphabetical position, and it will do so consistently enough to
  look intentional.

  The two failures compound, and the mechanism is worth checking for
  directly: a hyphenated surname read as two authors adds a phantom author
  to the citation, which can push a two-author citation over the press's
  et al. threshold. The result is a citation that has both lost half a
  surname and gained an et al. it was never entitled to, from one parsing
  error. **Check every et al. in the proof against the author count in the
  reference entry**, not against the author count in the manuscript's
  citation, because that is where the phantom author becomes visible.

- **Names that are correctly lowercase, spaced, or otherwise
  unconventional.** Some scholars style their names in ways a
  capitalization pass will treat as an error and correct. These survive or
  fail silently, so verify each against the manuscript in both the
  citation and the reference entry rather than assuming a consistent-
  looking list is a correct one.
- **Page references dropped** from citations of quoted material, which
  turns a locatable quotation into an unlocatable one.

## Reference-List Audit

Compare every reference entry in full.

For each entry, check:

- Author names
- Initials
- Author order
- Year
- Letter suffix
- Article or chapter title
- Book or journal title
- Editors
- Edition
- Volume
- Issue
- Page range
- Publisher
- Place of publication
- DOI
- URL
- Terminal punctuation
- Capitalization
- Italics
- Quotation marks

Verify that editorial corrections have not introduced shortened names,
incorrect author groupings, incomplete publication information, duplicate
URLs, malformed DOIs, or inconsistent punctuation.

Two field-specific checks belong here:

- **Archival, oral-historical, and personal-communication entries**, which
  do not fit a standard bibliographic template and are therefore the
  entries a style conversion most often mangles. Check that a collection,
  box, folder, and repository survived, and that a personal communication
  attributed to a pseudonymous interlocutor was not converted into a
  named citation.
- **Non-English titles and their translations**, for diacritics per
  [ethnographic-integrity.md](ethnographic-integrity.md), for capitalization
  applied under English rules to a language with different conventions, and
  for a bracketed translation that was dropped as redundant.

## Reporting Rule

**Do not silently repair either document. Report what each file actually
contains.**

Keep the four states distinct for every finding:

- Introduced at proof
- Inherited from the manuscript
- An intentional publisher change
- Uncertain

The distinction is not bookkeeping. A reference error inherited from the
manuscript is still worth correcting, but it is corrected with different
language to the publisher, it may fall outside a correction allowance that
covers only production errors, and describing it as a proof error is a
claim about the press that the files do not support.

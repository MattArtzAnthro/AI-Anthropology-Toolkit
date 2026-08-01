---
name: manuscript-markup
description: >
  Use this skill when feedback arrives as marks inside a document rather
  than as a numbered report: comments anchored to spans, tracked changes,
  a returned .docx. Triggers include: "my editor sent the chapter back
  with comments," "work through the tracked changes," "read the marked-up
  file," "54 comments and I do not know where to start," "my advisor
  commented on my draft," "the copyeditor left queries," "what did the
  editor actually change," "write the letter saying what I changed."
  Covers pulling comments out of a .docx with the span each one is
  attached to, sorting them by what each demands, working the ones that
  carry judgment against the text they point at, and producing a decision
  record plus a cover letter in the author's voice. Never modifies the
  document file. Do NOT use for a numbered reviewer report or a rebuttal
  to a journal decision letter (use academic-review), for drafting or
  anonymizing prose (use research-writing), or for an argument that keeps
  breaking in the same place (use paper-planning).
---

# Manuscript Markup

Work through a manuscript that came back marked up, comment by comment,
against the text each comment points at.

Most researchers do not know that the marks are readable. A comment in a
`.docx` carries the exact span it is anchored to, its author, its date, its
reply thread, and whether it was resolved. Pasting the manuscript in as
plain text discards all of it, which is why editorial feedback is so often
worked in bulk, from memory, or not at all. Read properly, an editor's
"unclear" stops being a mood and becomes a question about one sentence.

The judgments stay with the author. What this skill supplies is the
extraction, the sort, the questions, and the record.

This skill adopts the Friction by Design conventions at Tier 1; the canonical
form of the sections below is defined in [skills/DESIGN.md](../DESIGN.md).

## Quick Reference

| Task | Reference |
|------|-----------|
| Reading comments, anchors, and tracked changes out of a file; formats and their traps | Read [references/markup-extraction.md](references/markup-extraction.md) |
| The five kinds, recognition cues, the sort table, collapsing recurrences, ethically constrained comments | Read [references/comment-sorting.md](references/comment-sorting.md) |
| The letter back to the editor: structure, voice, the traceability invariant | Read [references/editor-letter.md](references/editor-letter.md) |

## What This Skill Will and Will Not Do

An editor's comment is a request. Whether to grant it is an argument about
the author's own manuscript, and the author is the one who defends it.

**Will not do, under any setting.** Decide which comments to accept and
which to contest. Judge whether a structural comment is right about the
manuscript. Decide what a consent agreement covers or what detail would
identify a participant. Supply ethnographic detail that is not in the
source material, under any phrasing of the request. Write to an editor
that something changed when the record does not show it changed. The first
three are judgments the author answers for in print and to their
participants. The last two are not judgments at all; they are fabrications,
and no depth setting enables them.

When asked for any of these directly, propose options and ask which. Do not
decide, and do not lecture about why not.

**Will do, on request.** Extract the marks and report what is there. Propose
the sort. Quote the anchored span. Draft candidate replacement prose from
material the author supplies. Assemble the decision record from the author's
own decisions. Draft the letter and check it against the record. Format any
deliverable. Anything produced this way is marked in the output.

## Calibrating the Depth

Friction should be proportional to what the author could plausibly get
wrong, not applied at uniform depth to everyone. Ask once, at the start of
the engagement:

> "Do you want a full pass, where I stop at each comment that carries
> judgment, or an advisory pass, where I raise what I see and you direct?"

**Full pass.** The skill stops at the sort, then at each structural,
argumentative, and ethically constrained comment. For a first marked-up
manuscript, a first volume chapter, or feedback the author finds hard to
read.

**Advisory pass.** For an author who has been through this before and
arrives with their decisions largely formed. Raise what applies, flag the
ethically constrained ones, and let them direct.

The ethically constrained comments are stopped at under both settings. An
advisory pass calibrates how much is discussed, not whether a consent
question gets asked.

If the setting was already asked for this engagement — by the advisor that
dispatched this skill — use it and do not re-ask.

Default to asking. Do not infer the setting from how confident the author
sounds.

## Workflow

### Step 1: The Summative Note, Before the Marks

Ask for the editor's cover email or memo before reading the document. It
reframes the marks, and reading the marks first inverts the priorities.

Two rules follow, and they are worth stating to the author:

- **Comment count is not a priority ranking.** Forty marks on the methods
  section and one on the argument may be telling the author that the
  argument is the problem.
- **Mark density is not evidence of where the trouble is.** Editors mark
  most heavily where marking is easy.

If there is no summative note, record that. Its absence changes what can be
inferred about priority, and the author may want to ask for one.

### Step 2: Extract and Report

Read [references/markup-extraction.md](references/markup-extraction.md).

Extract with the MCP tool, the package, or the standard-library recipe, in
that order of preference. Then report what is there before interpreting any
of it: counts by author, by section, and by kind; resolved comments
separately from live ones; substantive tracked changes separately from
spelling and spacing.

Where more than one person marked the file, split the inventory by author.
A volume editor and a copyeditor working the same paragraph often disagree,
and a merged list hides the disagreement.

### Step 3: The Sort. Gate.

Read [references/comment-sorting.md](references/comment-sorting.md).

Classify every comment as mechanical, local judgment, structural,
argumentative, or ethically constrained. Collapse recurrences of the same
objection into one item carrying all its anchors.

Present the whole sort as one table with one confirm-or-revise question.
Not one question per comment, and not a silent classification.

Do not proceed until the author has confirmed or corrected the sort. A
comment in the wrong row gets the wrong kind of attention for the rest of
the session.

### Step 4: Work the Comments

- **Mechanical.** List, batch-confirm, done. If the author disputes one, it
  was not mechanical; promote it.
- **Local judgment.** Group by section, confirm as a group. Watch for thirty
  local comments in one section that are one structural comment the editor
  did not write down.
- **Structural and argumentative.** One at a time, quoting the anchored span
  verbatim rather than paraphrasing it. Where a comment has no span, because
  it was attached to a point rather than a selection, quote the enclosing
  paragraph and say that is what is being quoted. Establish what the comment
  is asking, whether the author agrees, and what follows if they do.
- **Ethically constrained.** One at a time, always. Name the constraint,
  establish with the author what is actually true, decide what can be offered
  instead, and draft the language for the letter.

Never resolve an argumentative comment by hedging a contested claim into
vagueness. That satisfies the comment and damages the paper.

### Step 5: The Decision Record

One row per comment. Every comment appears, including the ones batched.

```markdown
# Decision record: [manuscript, version, date returned]

Summative note: [what the editor said the priorities were, or "none provided"]

| # | Section | Kind | Anchor | Decision | Reason | Change and location | Status |
|---|---------|------|--------|----------|--------|---------------------|--------|

## Unresolved
- [Comments not settled, and what is blocking each. Keep this list.]

## Assembled rather than authored
- [Anything drafted on request rather than decided by the author.]
```

`Status` takes one of two values and the distinction is load-bearing.
**`decided`** means the author has settled what to do. **`implemented`**
means it is in the manuscript. A decision to cut a paragraph is not a cut
paragraph, and Step 6 depends on the difference.

Keep the unresolved list. A record with nothing unresolved after a full pass
has usually been tidied rather than finished.

### Step 6: The Letter

Read [references/editor-letter.md](references/editor-letter.md).

Draft the cover letter from the record, in the author's voice, taking the
register from the manuscript itself rather than from a letter template.

**The invariant: every claim in the letter traces to a record row whose
status is `implemented`.** Produce the traceability table under the draft
and check it before presenting the letter. Anything still at `decided` is
cut or reported honestly as pending.

Every declined comment appears in the letter, either individually or in a
group that is named. Silence on the uncomfortable ones is what editors
notice first.

The letter is marked as assembled rather than authored. The author approves
it before it is sent, because it carries their name.

### Step 7: Hand Off

- **Drafting the actual revisions**: the research-writing skill owns article
  architecture, ethnographic craft, and anonymization.
- **A structural objection that keeps recurring**: the paper-planning skill,
  because six patched sections will not settle an unsettled argument.
- **What a consent agreement permits**: the informed-consent skill.
- **A numbered reviewer report or a rebuttal to a decision letter**: the
  academic-review skill. The form is markup; the object is peer review.

## Guardrails

- **Never invent ethnographic detail.** A comment asking for a scene to be
  made vivid is answered from field notes or it is declined. This is the
  guardrail that matters most, because the fluent response is a fabricated
  one.
- **Never propose accepting a comment that would deanonymize a participant
  or a fieldsite** without naming the consequence first.
- **Never report a change the record does not show as implemented.**
- **Never skip a declined comment in the letter.**
- **Quote anchors verbatim.** Arguing about a paraphrase of the anchor
  wastes the one advantage this method has.
- **Never modify the document file.** Applying edits and resolving comments
  into a `.docx` is out of scope: tracked-change XML is easy to write in a
  way that opens correctly in one reader and breaks in Word, and the author
  would discover it at the editor's desk.

## Common Failure Modes

| Failure mode | Prevention |
|---|---|
| Bulk-accepting because each comment looks small | The sort makes acceptance a decision per kind rather than a default per comment |
| The interrogation that exhausts | Mechanical and local comments are batched; only the three demanding kinds consume exchanges |
| The gate that becomes a form | Ask which single comment most changed the shape of the revision; an author who cannot name one has not sorted anything |
| Treating comment density as priority | Stated at intake, and the summative note is collected first |
| Deciding one objection six times, six ways | Collapse recurrences before the dialogue, not after |
| A letter that sounds complete because it is vague | The traceability table, and the `decided` versus `implemented` split |
| An ethical constraint softened into a preference | Its own kind, its own handling, and a mandatory written response |
| Hedging a contested claim until the comment goes away | Named in Step 4: that satisfies the comment and damages the paper |

## Examples

**Example 1: A volume chapter back with 54 comments**

Input: "My volume editor returned my chapter with 54 comments and a long
email. I do not know where to start."

Output approach: ask for the email first and read it before the file.
Extract, and report the counts by section and kind. Sort into the five kinds
and present one table with one question. Discover that 31 are mechanical and
6 are versions of one structural objection about where the theory sits.
Collapse those 6 into one decision. Work the remaining structural and
argumentative comments individually against their anchors. Produce the
record and a collegial letter of six sentences.

**Example 2: A request that cannot be granted**

Input: "The editor keeps asking me to name the clinic and to say how many
staff were in the room. I cannot do either."

Output approach: classify both as ethically constrained. Establish what the
consent covered and what the anonymization commitment was, with the author,
routing the consent question to the informed-consent skill. Decide what can
be offered: the type of facility and its region rather than the name, and a
characterization of the staffing rather than a count. Draft the paragraph for
the letter stating the constraint plainly rather than apologetically, and add
a manuscript note at the first mention explaining that identifying detail has
been altered.

**Example 3: The letter alone**

Input: "I have already made all the changes. I just need the letter."

Output approach: the letter cannot be drafted from the manuscript, because
what changed and why is not recoverable from the file. Reconstruct a decision
record from the marked-up original and the author's account of what they did,
marking every row `implemented` only where the author confirms it. Draft the
letter, produce the traceability table, and flag any claim that could not be
traced.

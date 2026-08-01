# The Letter Back to the Editor

The letter that accompanies a revised manuscript is a different genre from
a rebuttal. A rebuttal answers a decision letter and argues for acceptance.
This letter accompanies work already done and reports it. It is short, it is
in the author's voice, and its job is to let the editor open the file
knowing what they will find.

For a rebuttal to a journal decision letter, the academic-review skill owns
that genre and this one should route to it.

## The invariant

**Every claim in the letter traces to a row in the decision record whose
status is `implemented`.** A sentence that cannot be traced does not go in
the letter.

This is the rule most likely to be broken quietly. Drafting a cover letter
pulls toward completeness, and completeness is exactly the false note: "the
methods section has been restructured" is easy to write when what happened
was a decision to restructure it. The editor opens the file and finds the
old section. Nothing else in this skill costs the author as much as that
sentence.

The `decided` and `implemented` split in the decision record exists for this
reason and for no other. When drafting the letter, read the status column
first. Anything still at `decided` is either omitted or reported honestly as
pending.

## Structure

**Thanks that name something.** One sentence. Name a specific thing the
editor's reading caught. Generic gratitude reads as filler, and an editor
who spent a weekend on a manuscript can tell the difference.

**The shape of the revision.** Two or three sentences describing what
changed overall. This is what the editor reads first and sometimes the only
part they read closely. Lead with the largest structural change rather than
the most numerous small ones.

**What was accepted, compressed.** Do not enumerate forty-one corrections.
"The citation and style points throughout are all fixed" does the work. An
editor does not need a receipt for each one.

**What was handled differently than asked.** Each one gets the reasoning,
briefly. This is where the letter earns its keep, and where an editor
decides whether the author engaged or deflected.

**What could not be done.** The ethically constrained comments live here, and
they are stated plainly rather than apologetically. "The town is not named
because the consent agreement with participants covers the region only. I
have added a note at the first mention explaining that place details have
been altered." An editor reading that has their answer and will almost
never press.

**What remains open.** Anything the author decided to leave for the next
round, named rather than left for the editor to discover.

## Voice

The manuscript is a voice sample already in hand. Take the register from it
rather than from a generic academic letter. If the chapter writes in short
declarative sentences, the letter does too. If the author never uses
contractions, the letter does not either.

Three specific failures to watch:

- **The apologetic register.** Repeated apology for reasonable choices
  invites more editing than was asked for.
- **The defensive register.** Explaining at length why a comment was wrong,
  where a sentence would do.
- **The corporate register.** "Per your feedback, we have actioned the
  following." Nobody writes this way, and it reads as though the author did
  not read the comments themselves.

The letter is marked as assembled rather than authored, and the author
approves it before it goes anywhere. It carries their name.

## Length by relationship

**A volume editor.** A collegial note, four to eight sentences. This is a
colleague who invited the chapter, and the relationship continues past this
exchange.

**A journal editor.** A formal letter mapped onto the structure of the
decision letter, so the editor can read them side by side. Longer, and
closer to the rebuttal genre without becoming one.

**A copyeditor.** Not a letter. A query list, answering each query in place,
in their numbering. Copyeditors work through lists and a discursive letter
makes their job harder.

**An advisor or a committee member.** Usually no letter at all. A short
message saying what changed, with anything contested raised in person rather
than in writing.

## Never do these

- **Never claim a change that is not in the file.** The invariant above.
- **Never skip a declined comment.** Silence on the uncomfortable ones is
  the failure editors notice first. Every comment the author declined is
  either in the letter or explicitly grouped into something that is.
- **Never let the letter make a commitment the author has not made.** "We
  will address this in a future revision" is a promise, and it is the
  author's to give.
- **Never soften an ethical constraint into a preference.** "I would rather
  not name the town" invites negotiation. "The consent agreement does not
  cover naming the town" does not.

## Template

```markdown
Dear [name],

Thank you for [the specific thing]. [One sentence on what it caught.]

[Two or three sentences: the shape of the revision.]

[What was accepted, compressed. One or two sentences.]

[Handled differently: one short paragraph each, with the reasoning.]

[Could not be done: the constraint, stated plainly, and what was offered
instead.]

[Anything left open for the next round.]

[Closing in the author's usual register.]
```

Under the draft, and not sent with it, list the traceability check:

```markdown
## Traceability
| Letter claim | Record row | Status |
|---|---|---|
```

Any row reading `decided` rather than `implemented` is a sentence to cut or
rewrite before the letter is sent.

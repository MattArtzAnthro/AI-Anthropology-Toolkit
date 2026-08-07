# What these evals support, and what they do not

These are maintainer tools. No researcher using the toolkit ever runs them,
and nothing here appears in a skill.

```bash
AAT_RUN_GATE_EVALS=1 python3 -m unittest discover -s tests/evals -v
```

They cost tokens and model behaviour varies between runs, so they stay out of
CI. The deterministic half — everything in `test_judge_contract.py`,
`test_isolation.py`, `test_floor.py`, `test_stance.py` — runs in CI for free.

## What they can support

**They find problems.** Run against nine gate scenarios in 2026-08 they
found a gate that did not hold once the subject was isolated, two skills that
re-interrogated judgments the researcher had already supplied, and four
scenarios whose green results were never evidence about the skills at all.

## What they cannot support

**They do not certify anything.** No number from this suite belongs in a
paper, a release gate, or a claim about a skill without a second instrument
agreeing.

The reason is measured rather than cautious. Building this suite produced
five defects in its own reading layer in a single session, every one of which
changed results:

- a mutation that did not mutate, so three checks guarded nothing;
- a breakage script that rebound a module attribute the tests did not use,
  reporting false holes twice;
- a floor reading that scored four scenarios as measuring the model's
  defaults when the result was structural;
- a stance reading that accused a working skill of ignoring stance, when the
  evidence showed it correctly asking the researcher;
- an evidence check that rejected legitimate quoting as fabrication, in three
  separate forms, deflating every verdict it touched.

## Three things that follow

**Defects live in the reading layer, not the running layer.** The subject
runs fine. The judge mostly runs fine. What breaks is the code that turns
observations into verdicts. That layer is pure functions, so it is the
cheapest thing here to test and the most valuable.

**A verdict that disagrees with its own evidence is an instrument problem.**
So is a whole class of scenarios reading identically. Both were how real
defects surfaced, and neither is visible from a summary count. When either
happens, look at the reading before believing the finding.

**Contact catches what care does not.** Every defect above was found by
running the instrument against a case whose answer was already known, and
none by inspecting it. That is what the anchors in `test_judge_anchors.py`
are: transcripts whose correct verdict the author decides. They are not a
gate that gets passed once and retired. They are the load-bearing part, and
they should be re-run whenever any reading changes.

## What the numbers currently are, and how much to trust them

| Result | Reading | Confidence |
|---|---|---|
| 6 of 13 verdicts change when the subject is isolated from this repo | The repo's CLAUDE.md, on-disk skills, MCP server, and installed plugin all carried gates the system prompt did not | Highest. Two arms measured identically, so a reading defect distorts both equally and the difference survives |
| 3 of 9 pressure scenarios measure the skill rather than the model | The other four return the same verdict with no skill loaded | Moderate. The classification was corrected once mid-run, and it is one sample per scenario |
| Both stance pairs route the judgment back under either stance | The skills do not impose one tradition's commitment on another | Lowest. Rebuilt twice, two pairs, and the first two runs were discarded |

Raising confidence from here means repeated runs, which have not been done,
and anchors for each reading rather than only for the judge. It does not mean
more scenarios.

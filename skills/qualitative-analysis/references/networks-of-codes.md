# Networks of Codes

A coded dataset is already a network: codes that appear in the same chunk are
tied, speakers are tied to the codes they voice, and lenses are tied by the
chunks on which they agree. Drawing that network is a way of reading the
analysis, not a result in itself. This reference covers when to build one,
how to read it, and what it does not license.

## When a network helps

- **After coding, before themes.** A co-occurrence map shows which codes
  travel together across the corpus; clusters are candidate themes, and a
  code that bridges two clusters is a candidate for splitting or for a theme
  of its own.
- **Comparing speakers or sources.** The two-mode speaker-to-code network
  shows who voices what; a speaker at the margin of the map is coded
  differently from the rest, which is either a finding or a coding problem.
- **Comparing lenses.** Lens-agreement ties count the chunks on which two
  lenses applied a common code. Weak ties between lenses are the
  lens-specific findings; strong ties are the convergent ones.

A network does not help when there are fewer than a dozen codes (a table is
clearer) or when the coding was single-code per chunk (no co-occurrence to
draw).

## The tools

`build_network(records, kind)` takes the coding job's records
(`get_job_result`) and builds `code_cooccurrence`, `speaker_code`, or
`lens_agreement` (the last needs `results_by_lens`). `analyze_network(graph)`
lays it out, colors it by modularity community, sizes by degree, and returns
a summary and a visual-QA reading. `view_network(graph)` shows it in chat
where the host renders MCP Apps; otherwise draw `structuredContent` yourself.
`export_network(graph, path)` writes GEXF, which opens in Gephi laid out and
colored, and from there Gephi AI's full instrument applies.

## Reading the map

- **Compute before you claim.** Communities and centralities come from the
  analysis; the picture confirms them, it does not replace them.
- **Name the ties.** A tie in a co-occurrence map means "applied to the same
  chunk," nothing more. Say that in the caption.
- **Hub dominance is a property of this corpus.** A code with many ties is
  broad, or frequent, or both; never call the distribution "scale-free" or a
  "power law." Those fits are indistinguishable from log-normal at these
  sizes and smuggle in a universal-law claim.
- **Check the partition.** `analyze_network` reports whether the community
  partition is topologically real (within-community tie share against a
  random baseline). If the verdict is "none," coloring by it misleads.
- **Isolates and components are findings.** A code with no ties was never
  applied with another; a separate component is a part of the corpus that
  never meets the rest. Ask why before removing them.
- **Weight matters.** `min_weight` drops rare co-occurrences; say what
  threshold the map uses, because the picture changes with it.

## Captions

Every exported map ships with its story: the corpus and coding pass it came
from, what a node and a tie mean, the co-occurrence threshold, what size and
color encode, and what the map does and does not license. A map circulated
without that is a picture, not evidence.

## Further reading

The Gephi AI skill (`gephi-ai/claude-plugin/skills/gephi/references/`)
carries the fuller craft: layout choice, statistics, claim verification, and
reading network maps. For the network science itself: Jacomy, M. (2020),
"Epistemic clashes in network science: mapping the argumentative structure
of..." is the source of the scale-free caution; Blondel et al. (2008) for
modularity.

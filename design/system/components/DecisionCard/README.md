# DecisionCard

One decision the researcher has to make: a code to ratify, a disagreement to rule on, a theme to confirm.

**Use**
- Show one open card at a time where the work is a queue: Progress above it, the card raised on the page, and decided items as one-line rows below.
- `state="needs"` until the researcher acts: the yellow Needs-you status in the card's corner.
- `started` once something is chosen but not recorded.
- `done` with a `result` collapses the card to one line with a Change button, so only open work stays expanded.
- Inside: the data (Passage), the evidence (who coded what), numbered Steps, and the model's view in a Provenance box.

**Props** `title` · `eyebrow` (an ID) · `state`: `"needs" | "started" | "done"` · `statusLabel` · `result` · `doneLabel` · `onChange` · `children`.

**Plain HTML**
```html
<article class="aat-card aat-card--needs">
  <header class="aat-card__head">
    <div class="aat-card__titles"><span class="aat-id">P07-c15</span><h3 class="aat-card__title">Disagreement 1 of 4</h3></div>
    <span class="aat-status aat-status--needs">Needs your ruling</span>
  </header>
  …
</article>
```

# Tally

How many decisions are left, with the way to the next one and the action that finishes the stage.

**Use** once per stage. `sticky` keeps it in view while the list scrolls, and a sticky tally is always one row: the count and Go to next, nothing else (it ignores `children`). Put the button that finishes the stage below the last card, disabled with a reason until everything is decided. A tally that is not sticky may carry that button in `children`.

**Props** `left` · `total` · `noun` ("codes", "disagreements") · `onNext` · `sticky` · `doneText` · `children`: actions, only when not sticky.

**Plain HTML**
```html
<div class="aat-tally" role="status">
  <span class="aat-tally__count"><span class="aat-status aat-status--needs">3</span><span class="aat-tally__text">3 of 7 codes need you</span></span>
  <div class="aat-tally__actions">…buttons…</div>
</div>
```

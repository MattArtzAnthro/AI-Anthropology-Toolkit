# Progress

Where the researcher is in a queue of decisions: one segment per item.

**Use** above the open decision when items are shown one at a time. Decided items are `action`, the item that needs you now is `attention`, and the rest are `line`. Always pair it with a sentence that gives the numbers ("Disagreement 3 of 4", or a Tally); the strip alone is not the count.

**Props** `total` · `done`: how many are decided · `current`: index of the open item · `label`: replaces the spoken summary ("2 of 4 decided").

**Plain HTML**
```html
<ol class="aat-progress" role="img" aria-label="2 of 4 decided">
  <li class="aat-progress__seg aat-progress__seg--done"></li>
  <li class="aat-progress__seg aat-progress__seg--done"></li>
  <li class="aat-progress__seg aat-progress__seg--current"></li>
  <li class="aat-progress__seg"></li>
</ol>
```

**Don't** use it for more than about 20 items; past that, show the count in words only.

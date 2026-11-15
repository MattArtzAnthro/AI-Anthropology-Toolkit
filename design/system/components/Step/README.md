# Step

A numbered instruction that makes the order of clicks visible: 1 choose, 2 record.

**Use** inside a decision card whenever a decision takes more than one click. Number from 1 inside each card. Mark a finished step with `done`.

**Props** `n` · `label` · `done` · `children` (the controls for that step).

**Plain HTML**
```html
<div class="aat-step">
  <span class="aat-step__n" aria-hidden="true">2</span>
  <div class="aat-step__label">Record your ruling</div>
  <div class="aat-step__body">…controls…</div>
</div>
```

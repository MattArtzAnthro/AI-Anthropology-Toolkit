# Stages

The stages of a longer task, in order, with where you are and how much is left in each.

**Use** at the top of a multi-stage view (Codebook, Rulings, Record). The `note` says what is left ("3 left", "Done"). The current stage is outlined in the action colour.

**Props** `stages`: `[{ id, label, note? }]` · `current` · `onSelect(id)` · `label`.

**Plain HTML**
```html
<nav aria-label="Stages"><ol class="aat-stages">
  <li><button class="aat-stage" aria-current="step"><span class="aat-stage__n" aria-hidden="true">1</span>Codebook<span class="aat-stage__note">3 left</span></button></li>
</ol></nav>
```

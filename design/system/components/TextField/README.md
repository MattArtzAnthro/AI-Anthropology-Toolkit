# TextField

A labelled text input or text area, with an optional hint and an error that says how to fix it.

**Use** for reasons, rules, rewordings and notes. Say in the hint what a good answer looks like. Errors say what is wrong and what to do: "Write the rule in one sentence."

**Props** `label` · `hint` · `error` · `multiline` · any input attribute (`value`, `onChange`, `placeholder`, `required`).

**Plain HTML**
```html
<div class="aat-field">
  <label class="aat-field__label" for="rule">The rule</label>
  <span class="aat-field__hint" id="rule-hint">One sentence the codebook can carry.</span>
  <textarea class="aat-input" id="rule" aria-describedby="rule-hint"></textarea>
</div>
```
Add `aat-field--error` and an `aat-field__error` span for an error.

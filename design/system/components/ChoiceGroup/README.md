# ChoiceGroup

A question with its answers as pills you tap (rounded tiles when an answer has a description); checkboxes when several can apply, radios when one can.

**Use**
- The legend is the question, ending in a question mark: "Which codes apply to this passage?"
- Nothing is pre-selected. The researcher picks; the model's suggestion never fills these in.
- Give codes their `tone` (1–6) so the colour matches the code everywhere else.
- `wide` puts one answer per row.
- Inside a `Step` whose label already asks the question, pass `hideLegend`: the question stays for screen readers without showing twice.

**Props** `legend` · `hint` · `options`: `[{ value, label, description?, tone? }]` · `multiple` · `value` / `defaultValue` · `onChange(value)` · `name` · `wide` · `hideLegend` · `disabled`.

**Plain HTML**
```html
<fieldset class="aat-choices">
  <legend>Which codes apply to this passage?</legend>
  <div class="aat-choices__list">
    <label class="aat-choice"><input type="checkbox" name="codes" value="MUTUAL_AID">
      <span class="aat-choice__text">Mutual aid</span></label>
  </div>
</fieldset>
```

**Don't** use a select menu for fewer than eight answers. Don't add a "select all".

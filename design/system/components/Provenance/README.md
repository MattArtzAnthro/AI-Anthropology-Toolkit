# Provenance

Shows who wrote something: a dashed box for the model's draft that nobody has decided, a solid box for the researcher's decision.

**Use**
- Anything the model produced and the researcher has not decided goes in `by="model"`: a proposed code, a draft definition, a suggested resolution.
- Once the researcher decides, show it in `by="researcher"`. Never restyle a model draft as solid because it was accepted; show the decision as its own block.
- When the proposal is hidden (blind first), show the model box with "Hidden until you record your ruling."

**Props** `by`: `"model" | "researcher"` · `label` (default "Model draft · not decided" / "Your decision") · `children`.

**Plain HTML**
```html
<section class="aat-prov aat-prov--model" aria-label="Model draft">
  <p class="aat-prov__who">Model draft · not decided</p>
  <div class="aat-prov__body">Charity framing. Gives surplus, has not taken.</div>
</section>
```

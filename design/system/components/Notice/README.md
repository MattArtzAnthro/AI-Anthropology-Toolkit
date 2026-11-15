# Notice

What the server said, in a sentence: a refusal that names what to fix, a confirmation, or information.

**Use**
- `refusal` whenever the gate says no. The title says what was refused; the body lists exactly what is missing. "Can't ratify yet" / "2 codes have no decision: Being watched, Permits and city rules."
- `done` to confirm a recorded result with its ID.
- `info` for anything the researcher should know before acting (for example, chunks not yet rechecked).

**Props** `tone`: `"info" | "refusal" | "done"` · `title` · `children`.

**Plain HTML**
```html
<div class="aat-notice aat-notice--refusal" role="alert">
  <p class="aat-notice__title">Can't ratify yet</p>
  <div class="aat-notice__body">2 codes have no decision.</div>
</div>
```

**Don't** apologise or say "something went wrong". Say what happened and what to do.

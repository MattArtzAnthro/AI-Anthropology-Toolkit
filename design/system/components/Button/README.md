# Button

Three kinds: primary for the one thing the view is for, secondary for everything else, quiet for small moves like Change or Go to next.

**Use**
- One primary button per view. On a decision card it is the commit ("Record ruling", "Ratify codebook").
- Label with a verb and the object: "Record ruling", not "Submit" or "OK".
- A disabled button always says why. Pass `reason`; it shows beside the button and is linked for screen readers.

**Props** `variant`: `"primary" | "secondary" | "quiet"` (default secondary) · `disabled` · `reason`: text shown when disabled · any button attribute.

**Plain HTML**
```html
<button class="aat-btn aat-btn--primary">Record ruling</button>
<span class="aat-action">
  <button class="aat-btn aat-btn--primary" disabled aria-describedby="r1">Ratify codebook</button>
  <span class="aat-action__reason" id="r1">Decide 2 more codes first.</span>
</span>
<button class="aat-btn">Review the record</button>
<button class="aat-btn aat-btn--quiet">Change</button>
```

**Don't** disable a button without a reason. Don't use primary for navigation.

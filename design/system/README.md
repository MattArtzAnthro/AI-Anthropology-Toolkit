The AI Anthropology Toolkit's interface system: one small set of tokens and components for every screen the toolkit shows, from a ratification desk inside a chat to an exported decision record.

## Three rules every screen keeps

1. **Show who decided.** Anything the model wrote that nobody has decided sits in a dashed `model` box (`Provenance by="model"`, `Status tone="model"`). Anything the researcher decided is solid (`Provenance by="researcher"`). Never restyle a model draft as solid because it was accepted; show the decision as its own block.
2. **What needs you is the loudest thing on screen.** Show one open decision at a time where the work is a queue: `Progress` above it, the `DecisionCard` raised on the page with the yellow Needs-you status, and decided items as one-line rows below. Nothing else uses `attention`.
3. **One next step, numbered.** Inside a decision, number the clicks with `Step` (1 choose, 2 record). One primary button per view. A disabled button always says why (`Button reason`).

## Voice

- Plain words, sentence case, no exclamation marks. Labels are verbs plus objects: "Record ruling", "Ratify codebook", "Review the record".
- Questions end in a question mark: "Which codes apply to this passage?"
- Refusals say what was refused and exactly what is missing: "Can't ratify yet. 2 codes have no decision: Being watched, Permits and city rules." No apologies, no "something went wrong".
- Say "the model" for machine output and "you" for the researcher. Don't call the model "AI", "assistant" or "Claude" in the interface.
- Numbers are exact and counted from the record: "208 of 212 chunks", never "most".
- Quote participants exactly. Never tidy, trim or paraphrase a passage.

## Type

Who is speaking decides the typeface.

- **Interface** in Figtree: `display` once per view for the project title; `title` for a stage; `heading` for a card; `body` for everything else; `label` for field labels and status words; `small` for hints; `id` for chunk IDs and positions ("Disagreement 3 of 4 · P08-c06"); `model-label` for the label on model drafts.
- **People's words** in Source Serif 4 (`passage`), set larger than anything else in a decision: every quoted chunk, field note or document excerpt, with its source.
- **Raw machine text** in Source Code Pro (`raw`): exported JSON and IDs meant to be copied. Nowhere else.

Never set labels in all caps. Keep running text and passages within `measure` (68ch).

## Colour

The palette is Harbor: navy for what you can do, on a cool grey page, with yellow kept for what needs you.

- `paper` is the page; `surface` is every card, input and table on it. Text is `ink`; secondary text is `ink-muted`.
- `action` means "you can do this": primary buttons, selected choices, links, the current stage. Text on it is `on-action`.
- `attention` is only the Needs-you status. `done` is only recorded results. `refusal` is only errors and server refusals, always with a sentence.
- `model`, `model-line` and `model-soft` are only for what the model wrote and nobody has decided.
- `code-1` to `code-6` colour codes, lenses and chart series. They are marks (dots, lines, nodes), never text. A code keeps the same tone everywhere.
- Every text pair meets 4.5:1 in both themes; control borders (`line-strong`) and the focus ring meet 3:1. `line` is decorative only.

## Layout and states

- Spacing comes from the scale: `space-2` between choices, `space-4` inside small cards, `space-6` inside decision cards, `space-8` between cards.
- Shapes: buttons, choices, status and code tags are pills (`radius-full`). The decision card is `radius-lg`; boxes inside it (model drafts, your decision, notices) and collapsed done rows are `radius-md`; inputs and tables are `radius-sm`.
- The open decision card is the only element with a shadow.
- Everything clickable is at least `target` (44px) tall. Choices are whole rows you can click anywhere on.
- Keyboard focus is a 2px solid `focus` ring with a 2px gap, on every control.
- Hover changes colour only, in 150ms. No motion beyond that.
- Status is always a word plus a mark (filled, hollow, check, cross, dashed). Never colour alone.
- Full pages are at most `page` (880px) wide.

## Where it runs

- **Inside a chat (MCP App).** Set `data-theme="light"` or `"dark"` on the root from the host's theme and follow it. End the view with the one-line `Byline`.
- **Standalone pages and exported records** (decision record, methods appendix). Use the same tokens and components and end with `Byline full`.
- **Text-only hosts.** The same rules carry over in words: name who decided, list what needs the researcher first, and ask one numbered question at a time.

## Identity

The `Byline` is the toolkit's only branding: "AI Anthropology Toolkit by Matt Artz", the version, Cite (DOI), GitHub and mattartz.me. Every view ends with it. Don't add other marks or logos, and don't reword it. There is no logo; the name is set in type.

## Icons

There is no icon set. Status marks, the check, the cross and the notice glyph are drawn in `components/bundle.css` and take their colour from the text. Prefer a word to an icon. When an icon is unavoidable, use a single-colour 24px stroke icon tinted with `currentColor`, and always next to a word.

## Using it

- **Plain HTML.** Load `tokens.css` and `components/bundle.css`, then write the `aat-` classes. Each component's guidelines show the markup.
- **React.** Load React 18, then `components/bundle.js`; the components are on `window.AAT` and render the same markup.
- Fonts load from Google Fonts through `bundle.css`: Figtree, Source Serif 4 and Source Code Pro. Fallbacks are the system sans, Georgia and the system mono.

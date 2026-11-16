# Vendored files

Copied unchanged from the pinned npm packages in `app/package-lock.json`.

| File | Package | Version | License | Source |
|------|---------|---------|---------|--------|
| a2ui_schema/ (agent_to_renderer.json, common_types.json, catalog_definition.json, catalogs/basic/catalog.json) | @a2ui/web_core | 0.14.0 | Apache-2.0 | `src/v1_0/schemas/` in the package; licence in `a2ui_schema/LICENSE` |

To upgrade: change the pinned version in `app/package.json`, run `npm install` in `app/`, copy the
files from `node_modules/@a2ui/web_core/src/v1_0/schemas/` and its `LICENSE`, and update this table.

## The bundle

`app/dist/desk-app.js` bundles these packages, at the versions `app/package-lock.json` pins, into
the desk view. The bundle ends with the licence notices its sources carry; the table names every package's licence.

| Package | Version | License |
|---------|---------|---------|
| `@a2ui/lit` | 0.14.0 | Apache-2.0 |
| `@a2ui/web_core` | 0.14.0 | Apache-2.0 |
| `@lit/context` | 1.1.6 | BSD-3-Clause |
| `@lit/reactive-element` | 2.1.2 | BSD-3-Clause |
| `@preact/signals-core` | 1.14.5 | MIT |
| `lit` | 3.3.3 | BSD-3-Clause |
| `lit-element` | 4.2.2 | BSD-3-Clause |
| `lit-html` | 3.3.3 | BSD-3-Clause |
| `redos-detector` | 6.1.4 | MIT |
| `signal-polyfill` | 0.2.2 | Apache-2.0 |
| `signal-utils` | 0.21.1 | MIT |
| `validate-color` | 2.2.4 | MIT |
| `zod` | 3.25.76 | MIT |
| `zod-to-json-schema` | 3.25.2 | ISC |

To rebuild: `npm ci && npm run build` in `app/`. CI rebuilds the bundle and fails if it differs
from the committed one; `tests/package/test_desk_bundle.py` holds this table to the lockfile and
to what esbuild bundles, and the bundle to 500,000 bytes.

### Accepted advisory

`zod` 3.25.76 is inside the range of GHSA-mrhx-c7xc-m3w5 (memory exhaustion while validating
oversized constrained collections; fixed in zod 4.6.6). `@a2ui/web_core` 0.14.0 is written against
zod 3, so the desk stays on it until A2UI moves. The renderer validates only messages from the
toolkit's own server or from the page's own data block, whose collections are a desk's cards and
codes, so the advisory's input does not reach it.

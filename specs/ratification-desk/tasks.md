# Implementation Plan

## Progress Summary
- **Total Tasks**: 25
- **Completed**: 5
- **Remaining**: 20
- **Progress**: 20%

---

## Completed Tasks ✔

_No tasks completed yet. Tasks will be moved here as they are implemented._

---

## Pending Tasks

### Phase 1: Foundation

- [x] 1. Spike: one card with one toolkit component through the A2UI Lit renderer, inside an MCP App shell
  - Test first: tests/package/test_desk_browser.py::test_r7_11_custom_component_renders_in_app_shell (fails: no bundle yet)
  - Pin `@a2ui/lit`, `@a2ui/web_core` (A2UI v1.0, a release at least two weeks old) and `lit` exactly in `desk/app/package.json` and `package-lock.json`; add an esbuild `build` script
  - Write one catalog component (Passage) as a Lit element and register it under the toolkit catalog ID
  - Build `desk/app/dist/desk-app.js`; render a `createSurface` + `updateComponents` pair holding a basic `Text` and a toolkit `Passage` in a page with a stubbed MCP Apps host
  - If the renderer cannot take a custom catalog, stop and bring the finding back before Phase 2
  - Files: src/ai_anthro_toolkit/desk/__init__.py, src/ai_anthro_toolkit/desk/app/{package.json,package-lock.json,src/passage.js,src/main.js,build.mjs,dist/desk-app.js}, tests/package/test_desk_browser.py
  - Requirements: [R7.11]

- [x] 2. Design module code: tokens, theme CSS, A2UI token mapping
  - Test first: tests/package/test_design.py::test_r8_6_a2ui_tokens_come_from_toolkit_tokens (fails: no `a2ui_css` yet)
  - Add `tokens()`, `tokens_css()` (light on `:root`; dark under the guarded media query and `[data-theme="dark"]`), `stylesheet(fonts)`, `FONTS_URL`, `FONT_DOMAINS` and `a2ui_css()` (the `--a2ui-*` values set from toolkit tokens)
  - Files: src/ai_anthro_toolkit/design/__init__.py, tests/package/test_design.py
  - Requirements: [R8.6]

- [x] 3. Identity module; the network viewer takes its credit from it
  - Test first: tests/package/test_brand.py::test_r8_2_identity_matches_citation_cff (fails: no `brand` module yet)
  - Create `brand.py` with CREDIT, AUTHOR, AUTHOR_DESCRIPTION, WEBSITE, REPOSITORY, DOI_URL, ORCID_URL
  - Replace `BRAND_URL` and `BRAND_CREDIT` in `network/viewer/__init__.py` with imports from `brand`
  - Also: test_r8_1_viewer_credit_comes_from_brand, test_r8_5_viewer_credit_text_and_link_unchanged
  - Files: src/ai_anthro_toolkit/brand.py, src/ai_anthro_toolkit/network/viewer/__init__.py, tests/package/test_brand.py
  - Requirements: [R8.1], [R8.2], [R8.5]

- [x] 4. Colophon: `byline_html` and the design system's Byline
  - Test first: tests/package/test_brand.py::test_r8_3_colophon_links_in_order (fails: no `byline_html` yet)
  - Add `byline_html(version, full)`: credit linked to the website with the version, the author description (`text-wrap: balance`), then Website, Toolkit on GitHub, Cite (DOI), ORCID
  - Update the design system's Byline (bundle.js, index.d.ts, README, preview) to the same content and order
  - Also: test_r8_4_colophon_names_package_version, test_r8_3_colophon_carries_no_other_text, test_r8_4_no_version_no_version_mark, test_r8_3_design_system_byline_matches (runs bundle.js under node and compares its Byline with byline_html), and test_desk_browser.py::test_r8_3_description_sits_on_its_own_row (the description owns its row at every width)
  - Files: src/ai_anthro_toolkit/brand.py, src/ai_anthro_toolkit/design/bundle.css, design/system/components/{bundle.js,index.d.ts,Byline/README.md,Byline/preview.html}, tests/package/test_brand.py, tests/package/test_desk_browser.py
  - Requirements: [R8.3], [R8.4]

- [x] 5. Toolkit A2UI catalog definition and schema validation
  - Test first: tests/package/test_desk_a2ui.py::test_r1_8_unknown_component_fails_validation (fails: no validator yet)
  - Vendor the pinned A2UI v1.0 JSON schemas (with their licence) as package data; write `desk/catalog.json` naming DecisionCard, Passage, Provenance, ChoiceGroup, Step, Status, CodeTag, Progress, Notice, Tally, TextField, Byline and their properties
  - Add `a2ui.validate(messages)`: every message against the schema, every component in the basic or toolkit catalog; add `jsonschema` to the package dependencies
  - `validate(messages)` takes the whole sequence from `createSurface` and checks each message's envelope, then each component against the catalog it names (its own `catalogId`, else its surface's), then what the renderer checks in strict mode: identifier IDs, one ID per update, a root, references that resolve, no cycles, no orphans, and surfaces created once and gone once deleted. It refuses message kinds a desk does not send. `catalog_problems` checks a catalog against A2UI's catalog definition schema. `referencing` is declared too (imported directly)
  - The renderer runs with `STRICT_VALIDATION`. `desk/app/src/apis.js` holds the toolkit components' zod APIs without Lit, and `desk/app/scripts/check-messages.mjs` runs the renderer's strict check under node; test_r1_8_validator_and_renderer_agree requires the two checks to agree on a corpus, and test_r1_8_catalog_matches_the_renderer_schemas that each zod API takes exactly catalog.json's properties. CI runs `npm ci` in `desk/app`
  - Files: src/ai_anthro_toolkit/desk/{catalog.json,a2ui.py,a2ui_schema/,VENDORED.md}, pyproject.toml, tests/package/test_desk_a2ui.py
  - Requirements: [R1.8]

### Phase 2: Core logic

- [ ] 6. Cards and their checksum
  - Test first: tests/package/test_desk_cards.py::test_r1_3_cards_only_for_chunks_whose_code_sets_differ (fails: no `cards` module yet)
  - `codebook_cards(codebook, cases)` (raises naming every code without a case), `rulings_cards(job_a, job_b, codebook, proposals)`, `checksum(cards)`
  - Synthetic fixture: six codes, eight cases, two coding passes over twelve chunks with four disagreements, in tests/package/fixtures/desk/
  - Files: src/ai_anthro_toolkit/desk/cards.py, tests/package/fixtures/desk/, tests/package/test_desk_cards.py
  - Requirements: [R1.3]

- [ ] 7. A2UI description of a codebook desk
  - Test first: tests/package/test_desk_a2ui.py::test_r2_3_initial_data_model_has_no_choice_set (fails: no `surface` yet)
  - `a2ui.surface(desk)` for the codebook stage: Progress, one open DecisionCard per code with its cases (typical and borderline marked), the five actions, one exclusivity question
  - Also: test_r1_8_codebook_surface_validates, test_r2_1_code_card_carries_definition_criteria_and_cases, test_r2_2_code_card_offers_exactly_five_actions, test_r2_4_one_exclusivity_question
  - Files: src/ai_anthro_toolkit/desk/a2ui.py, tests/package/test_desk_a2ui.py
  - Requirements: [R1.8], [R2.1], [R2.2], [R2.3], [R2.4]

- [ ] 8. A2UI description of a rulings desk, and the updates after a decision
  - Test first: tests/package/test_desk_a2ui.py::test_r3_2_no_initial_message_carries_a_proposal (fails: no rulings surface yet)
  - Rulings cards: chunk text, both coders' codes, codebook entries; ChoiceGroup single-select when exclusive, else multi-select with "No code applies"; exclude with a required reason
  - `after_decision(desk, saved, card_id)`: mark decided, open the next card, release the proposal under blind-first, add the rule question when the ruling differs
  - Also: test_r3_1_rulings_card_carries_text_codes_and_entries, test_r3_3_exclusive_desk_is_single_select, test_r3_4_exclude_requires_reason, test_r3_5_no_action_carries_two_card_ids
  - Files: src/ai_anthro_toolkit/desk/a2ui.py, tests/package/test_desk_a2ui.py
  - Requirements: [R3.1], [R3.2], [R3.3], [R3.4], [R3.5]

- [ ] 9. Parse and validate a decisions document
  - Test first: tests/package/test_desk_decisions.py::test_r2_8_merge_into_unknown_code_refused (fails: no `decisions` module yet)
  - `parse(doc)` for `aat/desk-decisions@1`; `validate(desk, decisions, complete)` returning every problem with its card
  - Also: test_r2_8_split_needs_two_parts, test_r2_8_empty_reword_refused, test_r3_7_ruling_with_unknown_code_refused, test_r4_2_rule_without_text_refused
  - Files: src/ai_anthro_toolkit/desk/decisions.py, tests/package/test_desk_decisions.py
  - Requirements: [R2.8], [R3.7], [R4.2]

- [ ] 10. Apply actions, resolve rulings, create amendments
  - Test first: tests/package/test_desk_apply.py::test_r4_1_rule_creates_amendment_citing_card (fails: no `apply` module yet)
  - `apply_actions(codebook, decisions)` for adopt, reword, merge, split, delete; `resolve(cards, decisions)` returning resolved records and amendments; amended codes gain `rules`
  - `crosslens.codebook_checksum` includes `rules` only when a record has them; every existing checksum stays the same
  - Also: test_r4_4_rules_change_checksum_only_when_present
  - Files: src/ai_anthro_toolkit/desk/apply.py, src/ai_anthro_toolkit/crosslens.py, tests/package/test_desk_apply.py
  - Requirements: [R4.1], [R4.4]

- [ ] 11. Decision record and methods paragraph
  - Test first: tests/package/test_desk_record.py::test_r6_3_paragraph_counts_match_fixture_record (fails: no `methods` module yet)
  - `record.append`, `record.read_lineage` with an injectable `now()`; `methods.paragraph(lineage)`
  - Also: test_r6_4_paragraph_labelled_assembled, test_r6_5_paragraph_states_blind_first_per_desk, test_r6_6_paragraph_states_unrechecked_chunks
  - Files: src/ai_anthro_toolkit/desk/{record.py,methods.py}, tests/package/test_desk_record.py
  - Requirements: [R6.3], [R6.4], [R6.5], [R6.6]

- [ ] 12. Page shell
  - Test first: tests/package/test_desk_page.py::test_r1_5_page_has_no_external_script (fails: no `page` module yet)
  - `render_page(desk)`: tokens CSS, `a2ui_css`, stylesheet, the inlined bundle, the A2UI messages in an escaped JSON block, the title header and the colophon; `app_shell()`: the same without data
  - Also: test_r1_6_page_has_no_build_machine_path, test_r8_6_every_colour_comes_from_tokens, test_r8_7_title_in_header_author_only_in_colophon
  - Files: src/ai_anthro_toolkit/desk/{page.py,template.html}, pyproject.toml (package data), tests/package/test_desk_page.py
  - Requirements: [R1.5], [R1.6], [R8.6], [R8.7]

### Phase 3: Integration

- [ ] 13. The import gate
  - Test first: tests/package/test_desk_gate.py::test_r5_2_changed_card_checksum_refused (fails: no `gate` module yet)
  - `gate.apply(store, desk_id, doc, surface)`: validate the whole document first, then write; idempotent on the decisions digest
  - Also: test_r5_1_unknown_desk_refused, test_r5_3_decision_for_card_not_on_desk_refused, test_r5_4_incomplete_rulings_write_nothing, test_r5_6_same_decisions_twice_same_ratification, test_r2_6_missing_action_mints_nothing, test_r6_1_accepted_decisions_recorded
  - Files: src/ai_anthro_toolkit/desk/gate.py, tests/package/test_desk_gate.py
  - Requirements: [R2.6], [R5.1], [R5.2], [R5.3], [R5.4], [R5.6], [R6.1]

- [ ] 14. `build_ratification_desk` tool and the desk resource
  - Test first: tests/package/test_server_desk.py::test_r1_1_codebook_desk_writes_page_and_returns_desk_id (fails: no tool yet)
  - Register with `@_tool` and `_meta.ui.resourceUri = ui://ai-anthropology/ratification-desk`; register the resource with `_meta.ui.csp.resourceDomains` for the two font domains
  - Store the desk job (cards, checksum, blind_first, ratification in force); record drafted codes and proposals as decided_by "machine"
  - Also: test_r1_2_code_without_case_refused_and_named, test_r1_4_jobs_under_different_ratifications_refused, test_r1_7_desk_stores_card_checksum, test_r3_8_rulings_desk_blind_first_by_default, test_r6_2_build_records_machine_entries, test_r7_6_tool_carries_desk_resource_uri
  - Files: src/ai_anthro_toolkit/mcp/server.py, tests/package/test_server_desk.py
  - Requirements: [R1.1], [R1.2], [R1.4], [R1.7], [R3.8], [R6.2], [R7.6]

- [ ] 15. `record_desk_decisions` tool (chat and file surfaces)
  - Test first: tests/package/test_server_desk.py::test_r2_5_desk_ratification_accepted_by_start_coding_job (fails: no tool yet)
  - Model-visible import through `gate.apply` with surface "chat" or "page"; mints ratifications (method "desk", version "1.0") and amended ones (method "amendment", next minor version, parent)
  - Also: test_r2_7_actions_reach_ratified_codebook, test_r3_6_differing_ruling_without_rule_answer_refused, test_r4_3_amendment_issues_next_minor_version, test_r4_4_amended_ratification_names_parent_and_amendments, test_r4_5_reports_unrechecked_agreed_chunks, test_r7_4_chat_decisions_recorded_with_surface_chat
  - Files: src/ai_anthro_toolkit/mcp/server.py, tests/package/test_server_desk.py
  - Requirements: [R2.5], [R2.7], [R3.6], [R4.3], [R4.4], [R4.5], [R7.4]

- [ ] 16. App-only tools `desk_sync` and `desk_finish`
  - Test first: tests/package/test_server_desk.py::test_r7_7_desk_sync_is_app_only (fails: no tool yet)
  - `desk_sync` saves one decision and returns A2UI messages from `after_decision`; with no decision, returns the saved state; `desk_finish` runs the gate with surface "app"
  - Also: test_r3_9_proposal_only_in_response_saving_its_ruling, test_r5_5_app_route_and_json_route_give_identical_results, test_r7_8_only_app_only_tool_mints_for_app_desk
  - Files: src/ai_anthro_toolkit/mcp/server.py, tests/package/test_server_desk.py
  - Requirements: [R3.9], [R5.5], [R7.7], [R7.8]

- [ ] 17. `get_decision_record` tool
  - Test first: tests/package/test_server_desk.py::test_r6_3_record_tool_returns_counted_paragraph (fails: no tool yet)
  - Walk the ratification lineage and the desks built under it; return the record and the paragraph
  - Files: src/ai_anthro_toolkit/mcp/server.py, tests/package/test_server_desk.py
  - Requirements: [R6.3]

- [ ] 18. `ratify_codebook` records method and version
  - Test first: tests/package/test_server_desk.py::test_r7_5_table_ratification_records_method_table (fails: no method field yet)
  - Add `method: "table"` and `version: "1.0"` to the ratification record; behaviour otherwise unchanged
  - Files: src/ai_anthro_toolkit/mcp/server.py, tests/package/test_server_desk.py
  - Requirements: [R7.5]

- [ ] 19. Server instructions and the network fallback text name the design system
  - Test first: tests/package/test_server_desk.py::test_r8_8_instructions_name_credit_and_design_system (fails: instructions say monochrome)
  - Update the server instructions and the `view_network` fallback text; keep the credit text and link
  - Files: src/ai_anthro_toolkit/mcp/server.py, tests/package/test_server_desk.py
  - Requirements: [R8.8]

### Phase 4: The view

- [ ] 20. Catalog components and the controller
  - Test first: tests/package/test_desk_browser.py::test_r7_11_actions_become_app_only_tool_calls (fails: controller not written)
  - Write the remaining catalog components (DecisionCard, Provenance, ChoiceGroup, Step, Status, CodeTag, Progress, Notice, Tally, TextField, Byline) as Lit elements styled from bundle.css and the tokens, each API in `apis.js` and `TOOLKIT_APIS`; add a test that `TOOLKIT_APIS` names every catalog.json component, and add each component to the renderer-agreement corpus in test_desk_a2ui.py
  - Controller: read initial messages, apply host theme, map `save_decision` and `finish` to `desk_sync` and `desk_finish`, apply returned messages, show a Notice when the renderer rejects a message
  - Also: test_r3_2_proposal_appears_after_ruling, test_r3_3_exclusive_desk_allows_one_code, test_r3_6_differing_ruling_shows_rule_question, test_r7_9_reopen_restores_saved_decisions
  - Files: src/ai_anthro_toolkit/desk/app/src/*.js, src/ai_anthro_toolkit/desk/app/dist/desk-app.js, tests/package/test_desk_browser.py
  - Requirements: [R3.2], [R3.3], [R3.6], [R7.9], [R7.11]

- [ ] 21. Standalone page: browser storage and Copy decisions as JSON
  - Test first: tests/package/test_desk_browser.py::test_r7_2_decision_survives_reload_outside_app (fails: no storage path yet)
  - Detect no host, save to `localStorage` under `aat-desk:<desk_id>:<checksum>`, fall back to memory with a Notice; "Copy decisions as JSON" on every surface
  - Also: test_r7_3_copied_json_accepted_by_record_desk_decisions
  - Files: src/ai_anthro_toolkit/desk/app/src/*.js, src/ai_anthro_toolkit/desk/app/dist/desk-app.js, tests/package/test_desk_browser.py
  - Requirements: [R7.2], [R7.3]

- [ ] 22. Bundle checks and CI
  - Test first: tests/package/test_desk_bundle.py::test_r7_11_bundle_versions_match_vendored_md (fails: no VENDORED.md yet)
  - Write `desk/app/VENDORED.md` (versions, licences, the accepted zod advisory); test the 500 KB budget; CI: a job that runs `npm ci && npm run build` and fails if the bundle differs from the committed one
  - Already done with task 2: Playwright in the test extra; Chromium and `AAT_REQUIRE_BROWSER=1` in the package job
  - Files: src/ai_anthro_toolkit/desk/app/VENDORED.md, tests/package/test_desk_bundle.py, .github/workflows/validate.yml
  - Requirements: [R7.11]

### Phase 5: Skill and documentation

- [ ] 23. The qualitative-analysis skill offers the desk
  - Test first: tests/test_repo.py::test_r7_10_skill_offers_desk_with_chat_fallback (fails: skill text has no desk)
  - Update the ratification and disagreement steps; regenerate the Codex mirror with `scripts/sync_codex_mirror.py`
  - Files: skills/qualitative-analysis/SKILL.md, plugins/ai-anthropology/skills/qualitative-analysis/SKILL.md, tests/test_repo.py
  - Requirements: [R7.10]

- [ ] 24. Tool counts and docs
  - Test first: tests/test_repo.py tool-count test updated to 37 model-visible tools plus 2 app-only (fails: docs still say 34)
  - Update CLAUDE.md, README.md, AGENTS.md, GEMINI.md, RELEASING.md and the tool reference; add the desk tools to the CHANGELOG's Unreleased sections; raise `MIN_TESTS`
  - Files: CLAUDE.md, README.md, AGENTS.md, GEMINI.md, RELEASING.md, CHANGELOG.md, scripts/check.sh, tests/test_repo.py
  - Requirements: [R7.6], [R7.7], [R7.8]

- [ ] 25. Withdrawn criterion stays withdrawn
  - Test first: tests/package/test_server_desk.py::test_r7_1_no_artifact_database_path (fails: none; it guards against reintroducing the withdrawn path)
  - Assert no desk module or page reads or writes an artifact database
  - Files: tests/package/test_server_desk.py
  - Requirements: [R7.1]

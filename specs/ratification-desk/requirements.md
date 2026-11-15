# Requirements Document

## Introduction

The ratification desk is an interactive page where a researcher reviews a machine-drafted codebook
and the coding decisions that follow from it, one card per decision. It replaces approving a table
in chat at the points where approval changes the analysis. The toolkit builds the page from data it
already holds. The researcher's decisions come back through one import gate, and the server applies
only what was recorded there.

Ratifying a whole codebook as one table creates little friction, so it is easy to pass a codebook
unchanged. The decisions that expose gaps in a codebook come later, at the disagreements between two
coding passes. A ruling that departs from the proposed resolution often means the codebook lacks a
rule. The desk puts friction in two places. Codebook ratification is done code by code, each code
shown with its cases. Each disagreement ruling that departs from the proposal is asked whether it
states a rule, and a rule becomes a versioned amendment. Every action lands in a decision record,
and that record supports a draft methods paragraph.

The users are researchers who run the toolkit's coding pipeline. The pipeline's existing gate still
applies: `start_coding_job` refuses a codebook without a ratification. The desk is a richer way to
produce that ratification and a new way to settle disagreements. The chat-table path stays available
on every surface.

Scope of this version: ratification by cases, disagreement rulings with amendments, and the decision
record. The consistency sweep and review-by-code are deferred (see Out of scope). The record states
openly what goes unchecked while they are missing.

## Requirements

### Requirement 1: Building a desk [R1]
**User Story:** As a researcher with a drafted codebook or two finished coding passes, I want the
toolkit to build a desk page from data it already holds, so that I decide from the real cases
instead of from a summary.

#### Acceptance Criteria
1. WHEN the caller requests a codebook desk with codebook records and cases for each code THEN the server SHALL write a self-contained HTML page with one card per code and return a desk_id.
2. IF any code in a codebook desk request has no case THEN the server SHALL refuse to build and name every code without a case.
3. WHEN the caller requests a rulings desk with two coding job IDs THEN the server SHALL create one card for each chunk whose two code sets differ.
4. IF the two coding jobs of a rulings desk request were run under different ratification_ids THEN the server SHALL refuse to build the desk.
5. The built page SHALL embed all of its data and script inline, with no external script source.
6. The built page SHALL contain no filesystem path of the machine that built it.
7. WHEN a desk is built THEN the server SHALL store a checksum of the desk's cards with the desk.
8. The server SHALL describe each desk as A2UI v1.0 messages that validate against the pinned A2UI schema, using the basic catalog and the toolkit's own catalog of design-system components.

### Requirement 2: Ratifying a codebook by cases [R2]
**User Story:** As a researcher, I want to ratify each code against the cases it would take,
including the borderline ones, so that ratification tests the codebook instead of approving it
unread.

#### Acceptance Criteria
1. Each code card SHALL show the code's label, definition, inclusion and exclusion criteria, and its cases, with typical and borderline cases marked apart.
2. Each code card SHALL offer exactly the actions adopt, reword, merge, split, and delete.
3. The page SHALL show no action as chosen until the researcher chooses one.
4. The codebook desk SHALL ask once whether the codes are mutually exclusive.
5. WHEN imported decisions give every code an action and answer the exclusivity question THEN the server SHALL mint a ratification_id that `start_coding_job` accepts.
6. IF any code has no action or the exclusivity question is unanswered THEN the server SHALL refuse the import, name what is missing, and mint no ratification_id.
7. WHEN the imported actions include reword, merge, split, or delete THEN the ratified codebook SHALL be the result of applying those actions, and `start_coding_job` SHALL code with that result.
8. IF a merge names a target that is not in the codebook, a split has fewer than two parts, or a reword has an empty definition THEN the server SHALL refuse the import and name the card.

### Requirement 3: Ruling on disagreements [R3]
**User Story:** As a researcher settling disagreements between two coding passes, I want each
disagreement presented so that I decide it before seeing what the machine suggests, so that my
rulings are mine and not ratified proposals.

#### Acceptance Criteria
1. Each rulings card SHALL show the chunk text, each coder's codes, and the codebook entries for those codes.
2. WHILE blind-first is on THEN a rulings card SHALL keep the proposed resolution hidden until the researcher records a ruling for that card.
3. WHERE the codebook was ratified as mutually exclusive THEN a ruling SHALL accept exactly one code; otherwise a ruling SHALL accept one or more codes or "no code applies".
4. Each rulings card SHALL offer an exclude action that requires a reason.
5. The page SHALL offer no control that records rulings for more than one card at once.
6. WHEN a ruling differs from the proposal THEN the page SHALL ask whether the ruling states a rule.
7. IF a ruling names a code that is not in the codebook in force THEN the server SHALL refuse the import and name the card.
8. WHEN a rulings desk is built THEN blind-first SHALL be on unless the caller turns it off for that desk.
9. WHILE blind-first is on and the desk runs as an MCP App THEN the server SHALL send a card's proposal to the view only after the ruling for that card is saved.

### Requirement 4: Rules become codebook amendments [R4]
**User Story:** As a researcher whose ruling exposes a gap in the codebook, I want that ruling to
become a versioned amendment, so that the codebook records the rule and later coding follows it.

#### Acceptance Criteria
1. WHEN an imported ruling is marked as a rule with rule text THEN the server SHALL create an amendment that cites the ruling's card.
2. IF an imported ruling is marked as a rule with empty rule text THEN the server SHALL refuse the import and name the card.
3. WHEN an import creates one or more amendments THEN the server SHALL issue the codebook under the next minor version and keep the prior version unchanged.
4. WHEN an import creates one or more amendments THEN the server SHALL issue a ratification for the amended version whose record names the parent ratification and each amendment.
5. WHEN an import creates one or more amendments THEN the server SHALL report the number of chunks both coders agreed on under the prior version, and mark them as not yet checked against the amendments.

### Requirement 5: The import gate [R5]
**User Story:** As a researcher, I want the toolkit to apply only decisions recorded against the desk
I saw, so that nothing enters my analysis that I did not decide.

#### Acceptance Criteria
1. IF an import names a desk_id the server did not issue THEN the server SHALL refuse it.
2. IF an import's card checksum differs from the desk's stored checksum THEN the server SHALL refuse it.
3. IF an import contains a decision for a card that is not on the desk THEN the server SHALL refuse it and name the card.
4. IF a rulings import does not cover every card THEN the server SHALL write no resolutions and report how many cards are still open.
5. The server SHALL produce identical results from the page's JSON export and from the same decisions saved on the server through the MCP App.
6. WHEN the same complete decisions are imported twice THEN the server SHALL return the same ratification_id and append nothing new to the record.

### Requirement 6: The decision record [R6]
**User Story:** As a researcher writing up the analysis, I want every decision and its source kept
in one record, so that I can report what I decided, what the machine proposed, and how the codebook
changed.

#### Acceptance Criteria
1. WHEN an import is accepted THEN the server SHALL append each decision to the record with its desk_id, card, action, note, time, surface, and decided_by "researcher".
2. WHEN a desk is built with proposals or drafted codes THEN the server SHALL record each one with decided_by "machine".
3. WHEN the record is requested THEN the server SHALL return a draft methods paragraph whose counts are computed from the record: codes ratified and their actions, disagreements, rulings that departed from the proposal, rules adopted, exclusions, and the codebook version in force.
4. The methods paragraph SHALL be labelled as assembled rather than authored.
5. The methods paragraph SHALL state whether blind-first was on for each rulings desk.
6. WHERE amendments exist and no consistency sweep has run THEN the methods paragraph SHALL state how many agreed chunks were not rechecked against the amendments.

### Requirement 7: Surfaces and fallbacks [R7]
**User Story:** As a researcher on any surface the toolkit supports, I want to be able to finish a
desk and have the gate hold, so that the method does not depend on one product.

#### Acceptance Criteria
1. (withdrawn: replaced by R7.6–R7.9, which save decisions on the server through the MCP App instead of in an artifact's database) WHERE the page runs as a hosted artifact with a database THEN the page SHALL save each decision when it is made and restore saved decisions when the page reopens.
2. WHERE no hosted database is available THEN the page SHALL save decisions in browser storage.
3. The page SHALL offer a "Copy decisions as JSON" control on every surface.
4. WHERE the researcher decides in chat instead of on the page THEN the decisions SHALL pass the same import gate and be recorded with surface "chat".
5. The existing `ratify_codebook` path SHALL keep its current behaviour, and its ratifications SHALL be recorded with method "table".
6. WHERE the host supports MCP Apps THEN the desk SHALL open as an MCP App view in the conversation.
7. WHERE the desk runs as an MCP App THEN each decision SHALL be saved on the server by a tool whose `_meta.ui.visibility` is `["app"]`, so that the model cannot call it.
8. WHERE the desk runs as an MCP App THEN the ratification_id SHALL be minted only by an app-only tool that the researcher's Ratify control calls.
9. WHEN a researcher reopens a desk in an MCP App THEN the view SHALL restore every decision already saved on the server for that desk.
10. WHEN the qualitative-analysis skill reaches codebook ratification or disagreement rulings on a host that can show a page THEN the skill SHALL offer the desk, with the chat table as the fallback.
11. WHERE the desk runs as an MCP App THEN the view SHALL render the desk's A2UI description with the A2UI renderer bundled in the toolkit, and every action the researcher takes SHALL reach the server through an app-only tool.

### Requirement 8: The toolkit's identity on every page it renders [R8]
**User Story:** As the toolkit's author, I want every page the toolkit renders to share one house
style and carry a byline that credits me and links to my work, so that the toolkit is attributed
wherever its pages appear. As a researcher using the toolkit, I want that byline to credit the tool
and not my analysis, so that my decisions stay visibly mine.

#### Acceptance Criteria
1. The toolkit SHALL keep its identity in one module: the credit line, the author's name, a one-sentence description of the author, and the links to the website, repository, citation DOI, and ORCID. Every page renderer SHALL take the identity from that module.
2. The DOI, ORCID, and repository URL in the identity module SHALL match `CITATION.cff`.
3. WHEN the toolkit renders a desk page THEN the page SHALL end with a colophon containing the credit linked to the website, the author description, and links to the repository, the citation DOI, and ORCID.
4. The colophon SHALL name the toolkit version that built the page.
5. WHEN the network viewer renders THEN its credit SHALL come from the identity module, with its current text and link unchanged.
6. A desk page SHALL take every colour, typeface, spacing and radius value from the toolkit design system's tokens (`ai_anthro_toolkit/design/tokens.json`) and its stylesheet, in both the light and the dark theme, including the values the bundled A2UI renderer draws with.
7. WHEN a desk is built with a project title THEN the page header SHALL show that title, and the author's name SHALL appear only in the colophon.
8. The MCP server's instructions SHALL tell hosts that any page they build from toolkit output keeps the credit and uses the toolkit design system.

## Out of scope for this version

- **Consistency sweep.** After an amendment, sending agreed chunks that the new rule would recode
  back as keep, recode, or exclude cards. Until it ships, R4.5 and R6.6 make the gap visible.
- **Review by code.** Listing every chunk in one code and deciding keep, recode, or exclude for each.
- **Serving A2UI to hosts that render it themselves.** Such hosts may route actions through the
  model, so their decisions would need chat-level trust (R7.4). Revisit when a target host exists.
- **Any use of the `ratify` plugin.** Toolkit users will not have it, so the desk is built into
  the toolkit: its own page, its own decision format, and its own skill text, all in this repo. The
  desk follows the same principles independently: one decision per item, nothing preselected, and
  an export that keeps every per-item decision. It shares no code and no instructions with the
  plugin.

## Settled (Matt, 2026-11-15)

- **Scope.** This version builds ratification by cases, disagreement rulings with amendments, and
  the decision record. The consistency sweep and review-by-code are deferred, with the gap stated
  in the record (R4.5, R6.6).
- **Blind-first** is on by default for rulings desks, can be turned off per desk, and is reported
  in the methods paragraph (R3.2, R3.8, R6.5).
- **No bulk accept.** No control records more than one card at once (R3.5).
- **Amendments take effect from the recorded rule**, with no second confirm step (R4.4).
- **The skill offers the desk wherever a page can be shown**, with the chat table as the fallback
  (R7.10).
- **MCP Apps are the primary surface** (R7.6–R7.9). The artifact-database path is withdrawn (R7.1).
  An artifact or a local file still works through browser storage and the JSON export (R7.2, R7.3),
  and chat through R7.4.
- **The interface is the toolkit design system** (Harbor palette; Figtree, Source Serif 4 and
  Source Code Pro; one open decision at a time). Its tokens and stylesheet ship in
  `ai_anthro_toolkit/design/`; its brand book, components and generated brand spec and guide live
  in `design/` (R8.6). The design system's Byline gains the ORCID link and the author description,
  in the order R8.3 sets.
- The desk is built into the toolkit and does not depend on the `ratify` plugin.
- The colophon reads "AI Anthropology Toolkit by Matt Artz · v{version}", then "Matt Artz is an AI
  anthropologist, designer, and technologist who works with AI to study, use, and contribute to the
  development and governance of AI, establishing AI anthropology as a field." (set with
  `text-wrap: balance` at the design system's measure, so its lines wrap evenly), then links to the Website, the Toolkit on
  GitHub, Cite (DOI), and ORCID.
- **A2UI inside the toolkit's MCP App** (Matt, 2026-11-15; replaces "A2UI is not used"). The
  server describes each desk as A2UI v1.0, and an A2UI web renderer bundled in the toolkit draws
  it inside the MCP App, styled by the design system (R1.8, R7.11). Actions go to app-only tools,
  so the model never carries a decision, and blind-first proposals stay on the server until the
  ruling is saved (R3.9). The same description can later be served to hosts that render A2UI
  themselves (see Out of scope).

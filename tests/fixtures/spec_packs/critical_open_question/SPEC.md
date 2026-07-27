# Visual Anthropology Skill

## Outcome
A researcher asking about photo elicitation, film, or sensory methods is routed to
a skill written for those methods, rather than to the general fieldwork guide,
which currently answers and answers poorly.

## Scope in
One new skill directory with a SKILL.md and two reference files, its trigger
prompts, and its entries in the agent that owns it and in the command catalog.

## Scope out
Deciding which existing skill gives up a trigger phrase when the new one takes it.
That is a judgment about the shape of the library and it stays with me: the checks
can report a collision and cannot say who should own the phrase.
Any change to the 42 canonical stances.

## Constraints
No new dependencies. The description stays under 1024 characters. Content that
could appear unchanged in a generic methods textbook does not ship.

## Prior decisions
The governing conventions are in `skills/DESIGN.md`, which states that "All
content is anthropology-specific. If output could appear unchanged in a generic
social science methods textbook, it fails the library's bar." Reference files sit
one level down and each is cited in SKILL.md with a load condition.

## Likely files and interfaces
- `skills/DESIGN.md`
- `tests/test_repo.py`
- `tests/test_skill_routing.py`
- `commands/skills.md`
- `CLAUDE.md`

## Verification mode
record-checkable

## Verification
- `python3 -m unittest tests.test_repo tests.test_skill_routing -v`
- `wc -w skills/visual-anthropology/SKILL.md`

## Acceptance examples
- Given the prompt "design a photo elicitation study", When routing runs, Then
  visual-anthropology ranks first.
- Given the prompt "create an interview guide", When routing runs, Then
  fieldwork-methods still ranks first and its margin has not narrowed.
- Given the new description, When the collision check runs, Then no pair of
  descriptions exceeds the ceiling.

## Open questions
- critical: I do not know whether the stance list can be extended.

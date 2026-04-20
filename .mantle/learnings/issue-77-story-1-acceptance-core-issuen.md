---
issue: 77
title: 'story-1: acceptance core + IssueNote integration'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-20'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

## Patterns established (for story 2)

- **Module import inside `issues.py`:** `from mantle.core import acceptance` then reference `acceptance.AcceptanceCriterion`, not `from mantle.core.acceptance import AcceptanceCriterion` — ruff TC001 wants the direct import under TYPE_CHECKING, which breaks runtime Pydantic validation. Story 2 CLI code should mirror this.
- **`render_ac_section` output shape:** starts with `## Acceptance criteria\n\n`, each line `- [x|' '] ac-NN: text[ (waived)]`, trailing newline. Empty tuple renders `_None defined._`.
- **`replace_ac_section` regex is `(?ms)^##\\s+Acceptance\\s+criteria\\b.*?(?=^##\\s|\\Z)`** — case-sensitive on the heading word, tolerant of whitespace. Consumes everything until next `##` or EOF; replacement rstrips the rendered block.
- **`parse_ac_section` strips both `ac-NN:` prefix and trailing `(waived)` suffix**, so regen→parse→regen is a fixed point. `waived` always False on parse (migration cannot recover it).
- **YAML frontmatter:** `model_dump(mode='json')` + `yaml.dump(default_flow_style=False)` serialises tuples as lists with key order `id, text, passes, waived, waiver_reason`.
- **Gate placement:** `transition_to_approved` does the AC check **before** `_transition_issue`, so a blocked approval leaves issue status at `verified` and no hook is dispatched.
- **Empty tuple = back-compat escape hatch:** `all_pass_or_waived(()) → True`; `save_issue` skips regen when `acceptance_criteria == ()`. Until `migrate-acs` runs, existing issues behave as before.
- **`migrate_all_acs` return shape:** `list[tuple[int, int]]` where each is `(issue_number, criteria_count)`; already-migrated or AC-less issues are silently skipped.

## Gotchas

- `IssueNote` annotation uses `acceptance.AcceptanceCriterion` as the forward reference; the import is NOT under TYPE_CHECKING.
- The regex uses `(?ms)` multiline/dotall — remember when reasoning about substitutions.
---
issue: 48
title: Add groups.py registry and annotate all CLI commands with Cyclopts help panels
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a mantle user scanning 'mantle --help', I want commands grouped into labelled panels by workflow phase so that I can find the right command without reading a flat 48-line list.

## Depends On

None — independent (single-issue story).

## Approach

Introduce a central 'GROUPS' registry of cyclopts 'Group' objects in a new 'src/mantle/cli/groups.py', then annotate every '@app.command(...)' decorator in 'src/mantle/cli/main.py' with 'group=GROUPS[key]'. A regression test renders '--help' output via a deterministic Rich Console and asserts every command lives under its expected panel header. This follows the cyclopts 'Group Validator Example' pattern and the '--help' testing pattern from the cyclopts skill.

## Implementation

### src/mantle/cli/groups.py (new file)

Export a 'GROUPS' dict mapping stable keys to 'cyclopts.Group' objects with labelled panel titles and explicit monotonic 'sort_key' ordering. Use this exact content:

```python
"""Central registry of cyclopts Group objects for 'mantle --help' panels.

Every command registered on the top-level app must reference one of these
groups via 'group=GROUPS[key]'. The key set is closed; adding a group means
adding an entry here and updating the taxonomy test.
"""

from cyclopts import Group

GROUPS: dict[str, Group] = {
    "setup":     Group("Setup & plumbing",       sort_key=1),
    "idea":      Group("Idea & Validation",      sort_key=2),
    "design":    Group("Design",                  sort_key=3),
    "planning":  Group("Planning",                sort_key=4),
    "impl":      Group("Implementation",          sort_key=5),
    "review":    Group("Review & Verification",   sort_key=6),
    "capture":   Group("Capture",                 sort_key=7),
    "knowledge": Group("Knowledge",               sort_key=8),
}
```

### src/mantle/cli/main.py (modify)

1. Add import: 'from mantle.cli.groups import GROUPS'.
2. For every '@app.command(name="<cmd>")' decorator, add 'group=GROUPS[key]' kwarg. Apply this taxonomy (covers every command currently registered):

| Group key | Commands |
|---|---|
| setup     | init, init-vault, install, compile, where, introspect-project, set-slices, storage, migrate-storage |
| idea      | save-idea, save-challenge, save-brainstorm, save-research, save-scout |
| design    | save-product-design, save-revised-product-design, save-system-design, save-revised-system-design, save-adoption, save-decision, save-verification-strategy |
| planning  | save-issue, save-shaped-issue, save-story, update-skills, transition-issue-approved, transition-issue-implementing, transition-issue-implemented, transition-issue-verified |
| impl      | update-story-status, collect-changed-files, collect-issue-files, collect-issue-diff-stats, build-start, build-finish |
| review    | save-review-result, load-review-result |
| capture   | save-bug, save-inbox-item, save-session, update-bug-status, update-inbox-status |
| knowledge | save-learning, save-distillation, load-distillation, list-distillations, save-skill, list-skills, list-tags, show-patterns |

3. No command renames, no signature changes, no other edits.

#### Design decisions

- **Central registry (not decorator factories):** single source of truth; adding a command is one dict lookup, not a new wrapper. Pulls complexity downward via data, not abstraction.
- **Closed key set:** typos fail at lookup rather than silently creating a new panel.
- **Every command groups:** Cyclopts will render ungrouped commands under a default 'Commands' panel, which re-creates the problem the issue is fixing. The regression test guards this.

## Tests

### tests/cli/test_help_groups.py (new file)

Use the cyclopts '--help' testing pattern with a deterministic Rich Console (width=120, force_terminal=True, color_system=None, legacy_windows=False) and capture the rendered help text.

- **test_all_eight_panels_render_in_order**: asserts the panel titles appear in the rendered '--help' output in the order declared in 'GROUPS' (sort_key 1→8).
- **test_every_command_assigned_to_expected_panel**: for a hardcoded expectation dict mirroring the taxonomy above, asserts each command name appears under its expected panel title in the rendered '--help' output (slice the output between panel headers and check the command name is in that slice).
- **test_no_command_ungrouped**: iterates 'app.commands' (or equivalent cyclopts API) and asserts every registered top-level command has a non-default 'group' attribute pointing to one of the 'GROUPS' values. Fails if a new command is added without a group annotation.
- **test_groups_registry_keys_and_order**: asserts 'GROUPS' keys and 'sort_key' values match the expected 8-entry taxonomy, catching accidental renames or reordering of the registry itself.

Test fixtures: no 'tmp_path' needed — pure rendering. Import 'app' from 'mantle.cli.main' and 'GROUPS' from 'mantle.cli.groups'. Use 'pytest.raises(SystemExit)' around 'app("--help", console=console)' per the cyclopts testing example.
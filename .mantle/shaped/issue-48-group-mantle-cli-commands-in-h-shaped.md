---
issue: 48
title: Group mantle CLI commands in --help with Cyclopts help panels
approaches:
- 'A: Central GROUPS registry + group= on every decorator'
- 'B: Decorator factories per group'
chosen_approach: 'A: Central GROUPS registry + group= on every decorator'
appetite: small batch
open_questions:
- None — taxonomy matches issue spec; extras (show-patterns, build-*, collect-issue-diff-stats)
  slot into Knowledge and Implementation
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-12'
updated: '2026-04-12'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Chosen approach

A central 'GROUPS' mapping in 'src/mantle/cli/groups.py' declares one Cyclopts Group object per taxonomy category with explicit 'sort_key' ordering. Every '@app.command(...)' decorator in 'main.py' gets a 'group=GROUPS[...]' argument. No command renames, no runtime behaviour changes, no prompt edits.

Chosen over decorator factories (approach B) because:
- GROUPS dict is a single source of truth — adding commands requires only picking a key. Factories would hide that behind indirection.
- Cyclopts already supports 'group=Group(...)'; no new abstraction needed. Pull complexity downward via a data structure, not a new wrapper.
- Taxonomy changes (renaming a panel, re-ordering) are one-line edits in groups.py.

## Strategy

1. New module 'src/mantle/cli/groups.py' exports a 'GROUPS' dict mapping stable keys ('setup', 'idea', 'design', 'planning', 'impl', 'review', 'capture', 'knowledge') to 'cyclopts.Group' objects with labelled panels and monotonic 'sort_key'.
2. 'src/mantle/cli/main.py' imports GROUPS and passes 'group=GROUPS[key]' to every '@app.command(...)' decorator.
3. Taxonomy (all ~48 commands including ones not in the issue table: 'show-patterns' → knowledge; 'build-start','build-finish','collect-issue-diff-stats' → impl).
4. Regression test 'tests/cli/test_help_groups.py' renders '--help' via Rich Console (deterministic width, no colour) and asserts: (a) every registered command name appears exactly once in the help output, (b) each command appears under its expected panel header.

## Fits architecture by

- Lives entirely in 'cli/' slice — 'core/' untouched (CLAUDE.md: core never imports from cli).
- Uses cyclopts' native 'Group' API — no new framework abstraction; aligns with the cyclopts skill ('Group Validator Example' pattern).
- Test uses the '--help' testing pattern from the cyclopts skill (Rich Console with width=70, force_terminal=True, color_system=None).

## Does not

- Rename any command.
- Change prompts under 'src/mantle/commands/'.
- Collapse save-* / transition-* / update-* families into polymorphic commands (explicitly killed in brainstorm).
- Touch non-CLI modules.
- Add global/environment flags or reorder subcommand positional arguments.
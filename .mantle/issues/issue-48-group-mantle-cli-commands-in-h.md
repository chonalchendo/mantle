---
title: Group mantle CLI commands in --help with Cyclopts help panels
status: verified
slice:
- cli
- tests
story_count: 1
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- DuckLake
- Earnings Transcript Data Sources
- Howard Marks Investment Philosophy
- John Templeton Investment Philosophy
- Mohnish Pabrai Investment Philosophy
- Nick Sleep Investment Philosophy
- OpenRouter LLM Gateway
- Production Project Readiness
- Python 3.14
- Python Project Conventions
- Python package structure
- Software Design Principles
- Tom Gayner Investment Philosophy
- claude-sdk-structured-analysis-pipelines
- cyclopts
- omegaconf
- pydantic-discriminated-unions
- pydantic-project-conventions
tags:
- type/issue
- status/verified
---

## Parent PRD

product-design.md, system-design.md

## Why

`mantle --help` currently dumps ~48 top-level commands in a single flat list. There is no mental grouping — the `save-*`, `transition-*`, `update-*`, `collect-*`, `list-*`, and `load-*` families are all interleaved with bootstrapping commands (`init`, `install`, `compile`, `where`). Scanning the help output to find the right command is noticeably painful, and the surface will only grow from here.

The /mantle:brainstorm session on 2026-04-09 explored a larger refactor (polymorphic `mantle save --type X` with flag-driven customisation) and killed it on first-principles grounds:

- The 22 `save-*` commands share **zero** common required flags (e.g. `save-idea` needs problem/insight/target-user, `save-brainstorm` needs title/verdict, `save-story` needs issue/title/content). Collapsing them would force either a 40-flag help wall, a type-less `--field key=val` bag, or a discriminated-union that is just a subcommand in disguise.
- It conflicts with design principle #8 in product-design.md: "One command, one job… no overloaded multi-purpose commands."

The brainstorm verdict was **proceed** but scoped down to the cheapest fix that solves 100% of the stated pain: add Cyclopts `Group()` annotations so `mantle --help` renders commands in labelled panels. No command renames, no prompt changes, no breaking changes.

## What to build

Introduce a central group registry and annotate every existing CLI command so `mantle --help` renders in labelled Cyclopts help panels.

1. Create `src/mantle/cli/groups.py` with a `GROUPS` mapping of `Group` objects, one per category, with explicit ordering. Example:

   ```python
   from cyclopts import Group

   GROUPS = {
       "setup":      Group("Setup & plumbing",     sort_key=1),
       "idea":       Group("Idea & Validation",    sort_key=2),
       "design":     Group("Design",               sort_key=3),
       "planning":   Group("Planning",             sort_key=4),
       "impl":       Group("Implementation",       sort_key=5),
       "review":     Group("Review & Verification",sort_key=6),
       "capture":    Group("Capture",              sort_key=7),
       "knowledge":  Group("Knowledge",            sort_key=8),
   }
   ```

2. Add `group=GROUPS["<key>"]` to every `@app.command(...)` decorator (or equivalent registration) across `src/mantle/cli/`, using the taxonomy below.
3. Verify `mantle --help` output renders 8 labelled panels in the declared order and every command appears in exactly one panel.

### Proposed taxonomy (all 48 existing commands)

| Group | Commands |
|---|---|
| **Setup & plumbing** | init, init-vault, install, compile, where, introspect-project, set-slices, storage, migrate-storage |
| **Idea & Validation** | save-idea, save-challenge, save-brainstorm, save-research, save-scout |
| **Design** | save-product-design, save-revised-product-design, save-system-design, save-revised-system-design, save-adoption, save-decision, save-verification-strategy |
| **Planning** | save-issue, save-shaped-issue, save-story, update-skills, transition-issue-approved, transition-issue-implementing, transition-issue-implemented, transition-issue-verified |
| **Implementation** | update-story-status, collect-changed-files, collect-issue-files |
| **Review & Verification** | save-review-result, load-review-result |
| **Capture** | save-bug, save-inbox-item, save-session, update-bug-status, update-inbox-status |
| **Knowledge** | save-learning, save-distillation, load-distillation, list-distillations, save-skill, list-skills, list-tags |

Refine the taxonomy at shape time if anything feels off — for example, `save-adoption` might belong under Setup rather than Design, and `save-session` is arguable between Capture and Knowledge.

### Flow

1. User runs `mantle --help`.
2. Cyclopts renders output in 8 labelled panels in the declared order.
3. Every existing command appears in exactly one panel. Zero runtime behaviour changes.
4. Prompts and tests that invoke `mantle <command>` continue to work with no edits.

## Acceptance criteria

- [ ] `src/mantle/cli/groups.py` exists and exports a `GROUPS` dict of Cyclopts `Group` objects with explicit `sort_key` ordering.
- [ ] Every existing top-level command in `src/mantle/cli/` is registered with a group via `group=GROUPS[...]`.
- [ ] `mantle --help` renders 8 distinct labelled panels in the declared order (Setup & plumbing → Knowledge).
- [ ] No command appears in more than one panel and no command is missing from the panels.
- [ ] A regression test (`tests/cli/test_help_groups.py` or similar) parses `mantle --help` output and asserts each command is in its expected group.
- [ ] Every existing `mantle <command>` invocation — including every call from the Claude Code prompts under `src/mantle/commands/` — continues to work unchanged. No prompt files are edited.
- [ ] `uv run pytest` and `just check` both pass.

## Brainstorm reference

.mantle/brainstorms/2026-04-09-cli-refactor-help-grouping.md

## Blocked by

None

## User stories addressed

- As a mantle user who occasionally runs `mantle --help` to discover or remind myself what's available, I want commands grouped by workflow phase so that I can scan the surface without reading a 48-line flat list.
- As a prompt author (human or LLM) extending mantle, I want the CLI help output to clearly signal where new commands belong, so that the surface stays organised as it grows.
- As a mantle maintainer, I want the grouping taxonomy defined centrally in one file so that typos and group drift are impossible as the CLI evolves.
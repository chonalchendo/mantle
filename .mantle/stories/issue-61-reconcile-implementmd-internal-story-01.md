---
issue: 61
title: Remove skill-file references from implement.md Step 3 and Step 4
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle contributor maintaining command templates, I want `implement.md` to give a single coherent instruction about skill-file consumption so that a future edit does not compound the drift.

## Depends On

None — independent.

## Approach

Direction B from the shaped doc: skills load once during shaping, then propagate via the shaped doc's code design. Delete the two references to `.claude/skills/*/SKILL.md` that contradict the Step 5 paragraph at lines 180-183. The surviving paragraph then accurately describes the flow with no ambiguity. Pure documentation edit in a single file, no test-driven-development cycle applies (no production code involved).

## Implementation

### claude/commands/mantle/implement.md (modify)

Two surgical deletions:

**Deletion 1 — Step 3 context list (currently line 106):**

Remove the bullet:

```
- `.claude/skills/*/SKILL.md` — compiled vault skills (these provide domain-specific knowledge to story agents)
```

Leave the other bullets (`issues/issue-{NN}.md`, `system-design.md`, `product-design.md`, `stories/issue-{NN}-story-*.md`) unchanged.

**Deletion 2 — Step 4 per-story context bullet list (currently lines 145-147):**

Remove the three-line bullet:

```
- `.claude/skills/*/SKILL.md` — scan compiled skill summaries. Pick skills
  whose domain matches this story's work. A story about database migrations
  doesn't need the WebSocket skill.
```

Leave the surrounding bullets (`learnings/` and `decisions/`) unchanged.

**Do not touch:**

- Lines 180-183 (the clarifying paragraph) — these remain intact.
- The `mantle update-skills --issue {NN}` and `mantle compile --issue {NN}` calls at the top of Step 3 — they still serve status/resume templates and other consumers.
- Any other file: `shape-issue.md`, `plan-stories.md`, `build.md`, Python source, tests.

#### Design decisions

- **Keep deletion surgical, not exhaustive:** don't rewrite surrounding paragraphs even if they could be tightened. The acceptance criteria require that only the contradiction be resolved. Other edits widen the commit's blast radius without benefit.
- **Preserve lines 180-183 verbatim:** they already describe the now-uncontradicted flow correctly. Rewriting them would invite the "distillation vs. injection" ambiguity Direction A was rejected for.

## Tests

No test file changes. This is a documentation edit to a Claude Code prompt template — there are no unit tests covering prompt text. Verification is manual (grep + read) plus `just check` for project-wide lint/type/test regression safety.

### Manual verification (no new test file)

- `grep -n 'claude/skills' claude/commands/mantle/implement.md` should return **zero matches** after the edits.
- `just check` must pass (ruff, ty, pytest — all unchanged by a docs-only edit but run for safety).
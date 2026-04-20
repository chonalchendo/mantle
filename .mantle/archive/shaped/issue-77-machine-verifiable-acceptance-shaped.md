---
issue: 77
title: Machine-verifiable acceptance criteria with explicit pass/fail state
approaches:
- A — Extend IssueNote with structured acceptance_criteria list; body AC section regenerated
  on every save; flip-ac + migrate-acs CLI
- B — Sidecar issue-NN-acs.yaml file per issue; body renders from sidecar; verify/review
  read sidecar
- 'C — Keep markdown as source of truth; regex-substitute checkboxes at verify-time
  (rejected: no Pydantic schema, fails AC 1)'
chosen_approach: A — Extend IssueNote with structured acceptance_criteria list; body
  AC section regenerated on every save; flip-ac + migrate-acs CLI
appetite: small batch
open_questions:
- 'Should waiver require reviewer identity capture (author + date) or just a free-text
  reason? Initial implementation: free-text reason, no identity.'
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-20'
updated: '2026-04-20'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Problem

Acceptance criteria live as prose checkboxes in the issue body. `verify` and `review` infer pass/fail by parsing markdown and reading code, which is the documented "declare victory too early" failure mode — an agent can see code-level progress, check a box, and move on without real verification. Ground truth must move into structured frontmatter so:

- The AC list is schema-validated (Pydantic catches typos).
- A `passes` bit per criterion is the one signal `verify` flips and `review` gates on.
- The bit only flips via a dedicated CLI operation, not raw markdown edits.

## Approaches considered

### A — Extend `IssueNote` with structured `acceptance_criteria`, regenerate body on save *(chosen)*

- Add `AcceptanceCriterion` Pydantic model: `{id: str, text: str, passes: bool = False, waived: bool = False, waiver_reason: str | None = None}`.
- Extend `IssueNote` with `acceptance_criteria: tuple[AcceptanceCriterion, ...] = ()`.
- `save_issue` (in `core/issues.py`) regenerates the `## Acceptance criteria` section of the body from the structured list before `vault.write_note`, so the body stays a generated view.
- `mantle flip-ac --issue N --ac-id ac-01 [--pass|--fail] [--waive --reason ...]` CLI mutates the list and writes atomically.
- `mantle migrate-acs` reads every issue in live + archive, parses existing `- [ ] / - [x]` checkboxes into structured form, writes back.
- Approval gate (`transition_to_approved`) refuses when any AC has `passes=False` and `waived=False`.

**Appetite**: small batch (1-2 days).
**Tradeoffs gained**: schema validation, one CLI-mediated flip path, no new file types.
**Tradeoffs given up**: the issue body is now partially generated — hand-edits to the AC section are clobbered on next save. This is intentional; frontmatter is the source of truth.
**Rabbit holes**: body regeneration must be idempotent when the AC section is missing or has extra content; migration has to tolerate issues with no AC section at all; tags must not interfere with AC frontmatter.
**No-gos**: no separate AC file; no per-story ACs; no AC text diffing between revisions.
**Side-effect impact scan**: `save_issue` gains body regeneration — every call site that writes an issue now round-trips the AC section. Callers: `cli/issues.py::run_save_issue` (plan-issues, add-issue), the new `flip_ac` path, and `migrate_acs`. Nothing downstream of save reads the markdown checkboxes directly after migration, so regenerated body is safe.

### B — Sidecar AC file per issue

Store ACs in `.mantle/issues/issue-NN-acs.yaml` alongside the issue markdown. Verify/review read the sidecar.

**Appetite**: medium batch (3-5 days).
**Why rejected**: doubles the file surface per issue. Archive, compile, and list logic must all handle two files. One-concept-one-file is the prevailing convention in this codebase (see `core/shaping.py`, `core/learning.py`). Extra surface for no gain.

### C — Regex parse-on-read

Keep markdown as truth; regex-substitute `- [ ]` → `- [x]` at verify-time. No Pydantic schema.

**Appetite**: small batch.
**Why rejected**: AC 1 demands a Pydantic-validated schema. This approach fails AC 1 by construction.

## Code design — Approach A

### Strategy

- **New module `core/acceptance.py`** (deep module — complex internals, simple surface):
  - `AcceptanceCriterion(pydantic.BaseModel, frozen=True)` with `id, text, passes, waived, waiver_reason`.
  - `render_ac_section(criteria) -> str` — produces the canonical `## Acceptance criteria\n\n- [x] ac-01: ...` block.
  - `replace_ac_section(body, rendered) -> str` — swaps or appends the section in a markdown body, tolerant of missing section.
  - `parse_ac_section(body) -> tuple[AcceptanceCriterion, ...]` — for migration: walks `- [ ]/- [x]` items under the section header, auto-assigns IDs `ac-01..N`, sets `passes` from the checkbox state.
  - `flip_criterion(criteria, ac_id, *, passes, waived, waiver_reason) -> tuple[...]` — pure helper returning a new tuple.
  - Exceptions: `CriterionNotFoundError`, `DuplicateCriterionIdError`.
- **`core/issues.py`**:
  - Extend `IssueNote` with `acceptance_criteria: tuple[AcceptanceCriterion, ...] = ()`.
  - Inside `save_issue`, before `vault.write_note`, compute `body = replace_ac_section(content, render_ac_section(note.acceptance_criteria))` so the body view is always in sync.
  - Add `flip_acceptance_criterion(project_dir, issue, ac_id, *, passes, waived=False, waiver_reason=None) -> IssueNote` — loads, flips, saves; raises `CriterionNotFoundError` on bad id.
  - Add `all_acs_pass_or_waived(note) -> bool` predicate.
  - Extend `transition_to_approved` to raise `UnresolvedAcceptanceCriteriaError` if not `all_acs_pass_or_waived`.
  - Add `migrate_all_acs(project_dir) -> list[MigrationResult]` that walks live + archive issues.
- **`cli/issues.py`**:
  - `run_flip_ac(issue, ac_id, *, passes, waived, waiver_reason)` → wires into `issues.flip_acceptance_criterion`, prints state transition.
  - `run_migrate_acs(dry_run=False)` → prints a per-issue report (count migrated, skipped, errors).
- **Claude Code prompts**:
  - `claude/commands/mantle/verify.md` Step 5/6 — fetch ACs via `mantle list-acs --issue N --json`, flip via `mantle flip-ac` per criterion, never raw edit.
  - `claude/commands/mantle/review.md` Step 3/6 — read structured ACs, surface still-failing ones, refuse approval transition until all pass/waived (enforced in core).

### Fits architecture by

- Core owns schema, parse, render, flip, gate. CLI is a thin consumer. Prompts invoke CLI, not raw edits. Matches the "prompt orchestrates, CLI mutates state" pattern in `system-design.md`.
- Extending `IssueNote` keeps one note per issue — matches the one-file-per-concept convention used across shaping/learning/review modules.
- Gate at `transition_to_approved` puts the iron law in a single testable place.
- Follows project Pydantic conventions: `frozen=True`, populated defaults, tuples (not lists) in frontmatter.

### Does not

- Does not introduce per-story ACs (stories keep their existing `Tests` section).
- Does not add a sidecar file.
- Does not diff AC text across revisions or preserve `passes` state when an AC is renamed — IDs are the stable anchor; text is free.
- Does not handle partial verify runs by persisting intermediate state — one flip per successful evidence, one raw state in the file.
- Does not touch review result storage (`.mantle/reviews/`) or the existing `ReviewItem` model.
- Does not block `transition_to_verified` on AC state — only `transition_to_approved` gates.
- Does not auto-regenerate the body for notes other than issues.
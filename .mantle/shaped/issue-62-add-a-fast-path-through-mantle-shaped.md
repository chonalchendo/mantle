---
issue: 62
title: Add a fast-path through /mantle:build for trivial single-file edits
approaches:
- 'A: Explicit fast_path frontmatter field from shape-issue'
- 'B: Heuristic on shaped doc at build time'
- 'C: Slice signature (claude-code only)'
chosen_approach: 'B: Heuristic on shaped doc at build time'
appetite: small batch
open_questions:
- Should the fast-path require at least one story be planned first (safety belt) or
  truly skip planning?
- Is 10 lines the right threshold for 'tiny edit' or should it match simplify-skip's
  50?
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-17'
updated: '2026-04-17'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

# Shaped: Issue 62 — Fast-path through /mantle:build

## Context

`/mantle:build` is a 9-step pipeline that spawns at least two agents (story-implementer for implementation, general-purpose for verification). Issue 60 exposed that this is overkill for genuinely trivial changes: ~15 minutes wall-time on a 2-minute edit. Issue 62 asks for a fast-path that skips the story-implementer spawn when the shape describes a trivial single-file change — while preserving the rest of the pipeline's safety properties (simplify-skip threshold, verify agent, review handoff).

## Approaches evaluated

### Approach A — Explicit `fast_path` frontmatter field
Shape-issue emits `fast_path: true` in the shaped doc's frontmatter. Build.md Step 6 reads it and branches.

- **Appetite:** medium batch — touches `shape-issue.md`, `save-shaped-issue` CLI signature, shaped-doc parsing, `build.md`, plus tests.
- **Pro:** explicit, reviewable artifact.
- **Con:** widens scope into CLI and shaping layers. New shaping decision to make.

### Approach B — Heuristic on shaped doc (CHOSEN)
Build.md Step 6 inspects the shaped Strategy. If the rubric below matches, take the fast-path; otherwise take the existing agent path.

- **Appetite:** small batch — pure `build.md` template edit + one regression test.
- **Pro:** zero shaping overhead, zero CLI changes, retroactively eligible for existing shaped docs.
- **Con:** LLM-heuristic interpretation. Mitigation: the build orchestrator is already an LLM reading the shaped doc; a bounded rubric is reliable in practice, and the verify agent in Step 8 is the authoritative quality gate regardless of which branch ran.

### Approach C — Slice signature (`[claude-code]` only)
If issue slice is exactly `[claude-code]`, fast-path.

- **Appetite:** tiny — one-line check.
- **Pro:** cheapest.
- **Con:** too narrow. Misses trivial CLI-help typo fixes, single-line core changes. Issue body itself calls this out.

## Auto-choice rationale

Smallest appetite that satisfies all ACs: **B**. C fails the spirit of AC 2 (not a clear general skip condition — just "docs only"). A is correct but heavier than needed; the underlying work is small enough that a heuristic branch is proportionate. If B later proves unreliable in practice, upgrading to A is a follow-up issue with strictly less surface area than doing A now.

## Strategy

Edit `claude/commands/mantle/build.md` Step 6 to split into two explicit branches.

**Step 6 structure (new):**

1. **Pre-implement rev capture** — unchanged (captured before either branch).
2. **Transition to implementing** — unchanged, runs before branching.
3. **Fast-path eligibility check (new).** Read the shaped doc at `$MANTLE_DIR/shaped/issue-{NN}-shaped.md` and evaluate a bounded rubric (all four must be true):
   - Exactly one file named in the shaped Strategy section.
   - Strategy describes a removal, rename, or ≤ 10-line edit.
   - No AC mentions new tests or new CLI surface.
   - Appetite is `small batch`.
4. **Branch A — fast-path (if eligible).** Orchestrator performs the edit inline (no agent spawn), runs `just check`, commits via `git add` + `git commit` with conventional message. Captures a single inline-implement record.
5. **Branch B — agent-path (default).** Existing flow: Read `claude/commands/mantle/implement.md` and spawn the story-implementer per story.
6. **Both branches converge** at `mantle transition-issue-implemented --issue {NN}`.

The branch structure mirrors the "skip when X, otherwise run Y" language already used by Step 7 simplify-skip.

**Mandatory safety text (must appear in fast-path branch verbatim):**
- "Run `just check` after the edit. If it fails, revert and fall back to agent-path."
- "Step 8 (Verify) runs regardless — the fast-path only skips Step 6's agent spawn, never Step 8."

## Regression check

New test in `tests/test_workflows.py` (existing project-wide infra test file):

```python
def test_build_fast_path_cannot_skip_verify():
    build_md = (PROJECT_ROOT / "claude/commands/mantle/build.md").read_text()
    fast_path_section = extract_section(build_md, "Fast-path")
    # Fast-path must reference Step 8 / verify; never claim to skip it.
    assert "Step 8" in fast_path_section or "verify" in fast_path_section.lower()
    # Iron Law #2 guard: the verify step header must appear exactly once and not be inside a skip block.
    assert build_md.count("## Step 8 — Verify") == 1
```

Implementation detail: if `extract_section` is overkill, a simpler string-substring assertion suffices. Avoid `inline-snapshot` for this — we are specifying an invariant ("fast-path cannot skip Step 8"), not capturing exact text that may drift.

## Fits architecture by

- Entirely within `claude-code` (`claude/commands/mantle/build.md`) + `tests` slices — matches the issue's declared slice.
- No changes to `core/` or `cli/` — honours `core/ never imports cli/` trivially.
- Follows the "Skip condition: ..." prose style already present in Step 7.
- Preserves Iron Law #2 ("NO claiming pipeline success without verification evidence") — the regression test is the enforcement.
- Preserves Iron Law #1 ("NO skipping steps") — the fast-path is a branch *within* Step 6, not a skip of Step 6.

## Does not

- Does not change how shaping works — no `fast_path` frontmatter field, no `save-shaped-issue` CLI changes.
- Does not change what the verify agent does or how Step 8 is spawned.
- Does not change the simplify skip threshold (files ≤ 3 AND lines_changed ≤ 50 remains).
- Does not remove the story-implementer agent path — the fast-path is an *additional* branch.
- Does not handle multi-file trivial edits — fast-path is explicitly "single-file".
- Does not add telemetry or metrics for fast-path usage.
- Does not modify `plan-stories.md` — the fast-path skips story planning entirely via the eligibility rubric; when eligibility fails, story planning runs normally.
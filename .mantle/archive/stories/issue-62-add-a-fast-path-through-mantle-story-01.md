---
issue: 62
title: Add fast-path branch to build.md Step 6 with regression test
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle user running `/mantle:build` on a trivial single-file edit, I want the pipeline to skip the story-implementer agent spawn and do the edit inline, so the workflow stays the right tool for both large and small issues.

## Depends On

None — independent (single-story issue).

## Approach

Pure template edit in `claude/commands/mantle/build.md` to introduce a fast-path branch inside Step 6 (Implement), plus one regression test in `tests/test_workflows.py` following the `test_implement_md_references_build_telemetry` precedent (template-content assertion on a Markdown file under `claude/commands/mantle/`). No Python source changes, no CLI changes, no changes to other templates.

## Implementation

### claude/commands/mantle/build.md (modify)

Rewrite Step 6 to introduce a fast-path eligibility check and two explicit branches that converge before the `transition-issue-implemented` call.

**Preserved (no changes):**
- The "First, capture the pre-implement git rev" paragraph and the `git rev-parse HEAD` capture.
- The `mantle transition-issue-implementing --issue {NN}` call (runs before branching — both branches need the transition).
- The Inbox capture paragraph at the end of Step 6.
- The final `mantle transition-issue-implemented --issue {NN}` call.

**New content after "Then transition the issue to implementing" and before the existing `Read claude/commands/mantle/implement.md` paragraph:**

1. A new subsection heading: `### Fast-path eligibility check` with one paragraph of prose explaining the rationale and a four-item rubric (all must be true):
   - Exactly one file is named in the shaped doc's Strategy section.
   - Strategy describes a removal, rename, or ≤ 10-line edit.
   - No acceptance criterion mentions new tests or new CLI surface.
   - Shaped appetite is `small batch`.

2. Explicit skip-condition prose mirroring Step 7's style:
   > **Fast-path condition:** If all four rubric items are true, take the fast-path branch below. Otherwise, take the agent-path branch.

3. `### Branch A — Fast-path (inline edit)` subsection:
   - Orchestrator performs the edit inline (no agent spawn) using `Read` + `Edit`/`Write`.
   - Runs `just check` (or the project's check command from CLAUDE.md).
   - If `just check` fails, revert the edit (`git checkout -- <file>`) and fall back to the agent-path branch below.
   - On success, commit via `git add <file> && git commit -m \"<conventional message>\"`.
   - A verbatim note: `Step 8 (Verify) runs regardless — the fast-path only skips Step 6's agent spawn, never Step 8.`

4. `### Branch B — Agent-path (default)` subsection:
   - Wraps the existing `Read claude/commands/mantle/implement.md and follow Steps 3-5 with these build-mode overrides` text and the per-story progress reporting. No semantic change.

5. The existing Inbox capture paragraph and `transition-issue-implemented` call remain after the branches — both paths converge there.

#### Design decisions

- **Fast-path runs after `transition-issue-implementing`**, not before. Rationale: the transition is idempotent and both branches need it; moving it out of the branch avoids duplicating the call.
- **Fallback to agent-path on `just check` failure** (rather than halting): the agent-path is the safety net. The fast-path claims the edit is trivial; if the trivial edit breaks checks, the original plan was wrong — the agent-path gets a chance to reason through it rather than aborting.
- **Rubric is prose, not code** — the build orchestrator is an LLM reading the shaped doc; a bounded four-item rubric is reliable for LLM pattern-matching. No new CLI subcommand or Python helper.
- **Ten-line threshold** chosen (not 50) because fast-path is specifically about *trivial* edits; simplify-skip's 50 is a different threshold (skip simplification, not skip implementation). Different decisions, different numbers.

### tests/test_workflows.py (modify — append new test)

Add one function-level test (no new class) following the precedent of `test_implement_md_references_build_telemetry` at line 63.

```python
def test_build_md_fast_path_cannot_skip_verify():
    \"\"\"Regression: build.md fast-path must not short-circuit Step 8 (Verify).\"\"\"
    path = REPO_ROOT / \"claude\" / \"commands\" / \"mantle\" / \"build.md\"
    text = path.read_text(encoding=\"utf-8\")
    # Fast-path branch must exist.
    assert \"Fast-path\" in text or \"fast-path\" in text
    # Step 8 (Verify) header must appear exactly once — never inside a fast-path skip block.
    assert text.count(\"## Step 8 — Verify\") == 1
    # Fast-path branch must explicitly state Step 8 still runs.
    fast_path_note = \"Step 8 (Verify) runs regardless\"
    assert fast_path_note in text, (
        \"Fast-path branch must contain the verbatim note: \"
        f\"{fast_path_note!r} — protects Iron Law #2 (no skipping verification).\"
    )
```

#### Design decisions

- **Three assertions, not one.** The first checks the branch exists; the second guards against anyone duplicating or hiding the verify header inside a conditional; the third pins the exact protection text so a refactor can't silently delete it.
- **Function-level, not class.** Matches the `test_implement_md_references_build_telemetry` pattern at the bottom of the existing file — no reason to introduce a class for a single test.
- **No `inline-snapshot`.** We are specifying an invariant (\"fast-path cannot skip Step 8\"), not capturing drift-prone exact text. `inline-snapshot` would be the wrong tool — its anti-pattern list explicitly calls out \"business-logic thresholds or security constants — those need *specification*, not *capture*\".

## Tests

### tests/test_workflows.py (modify)

- **test_build_md_fast_path_cannot_skip_verify**: asserts build.md contains a fast-path branch, that `## Step 8 — Verify` appears exactly once, and that the verbatim note `Step 8 (Verify) runs regardless` is present in the template. Protects Iron Law #2 from silent erosion.

No other tests apply — this is a docs/template change with one regression guard.
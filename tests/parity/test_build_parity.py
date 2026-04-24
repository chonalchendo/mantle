"""Parity test for /mantle:build prompt."""

from __future__ import annotations

from typing import TYPE_CHECKING

from inline_snapshot import snapshot

from tests.parity import fixtures, harness

if TYPE_CHECKING:
    from pathlib import Path


def test_build_prompt_parity(tmp_path: Path) -> None:
    """Snapshot the normalized /mantle:build prompt for regression detection."""
    fixture = fixtures.build_sandbox_fixture(tmp_path)
    result = harness.run_prompt_parity(
        command="build",
        fixture=fixture,
        baseline=snapshot("""\
---
description: Use when you want to take a planned issue from design to verified code in one automated pass
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle *), Bash(git add*), Bash(git commit*), Bash(git checkout -- *), Bash(uv run pytest*), Bash(npm test*), Bash(cargo test*), Bash(go test*), Agent
---

Orchestrate the full journey from a planned issue to verified code without
human confirmation at each step.

## Iron Laws

These rules are absolute. No exceptions, no "just this once", no edge cases.

1. **NO skipping steps.** Every step runs unless its explicit skip condition is met. Each catches different problems.
2. **NO claiming pipeline success without verification evidence.** Step 8 must run and produce a per-criterion result. "It probably passes" is not a result.
3. **NO continuing past blocked stories.** If Step 6 blocks, stop. Do not continue to simplification or verification.
4. **NO silent failures.** Report errors and warnings verbatim — never summarise away.
5. **NO reporting "Skills loaded" without Read evidence.** Every skill named in the Step 4 report must have a corresponding `Read` call on `.claude/skills/<slug>/references/core.md` or `.claude/skills/<slug>/SKILL.md`. Codebase samples do not substitute — skill files encode patterns and anti-patterns codebase samples do not surface.

### Red Flags — thoughts that mean STOP

| Thought | Reality |
|---------|---------|
| "Simplification isn't needed, the code looks clean" | You haven't reviewed it yet. Run the step. |
| "Verification will pass, the tests already passed" | Tests check code correctness. Verification checks acceptance criteria. Different things. |
| "I'll skip skill loading since we already have skills" | Skills may be stale or missing for new technologies in this issue. |
| "I'll list the skills I *would* consult — naming them is enough" | Naming a skill is not loading it. If you have not Read the file, the skill is not loaded. |
| "The codebase example I read covers what the skill would say" | Skill files encode patterns and anti-patterns codebase samples do not surface. Read the skill. |
| "The story is blocked but the rest are independent, I'll continue" | Blocked stories signal problems that may affect dependent work. Stop. |
| "I can report the pipeline result without running verification" | A build without verification is an unverified build. Run Step 8. |

Use TaskCreate for each of the 9 steps ("Step 1 — Prerequisites" … "Step 9 — Summary").
Use TaskUpdate to set each to `in_progress` when starting, `completed` when done.

Stop early only if a story is blocked after retry in Step 6. Report progress at
each stage without asking for permission. Surface problems immediately.

**Tip:** Start a fresh conversation — prior conversation history adds noise.

## Step 1 — Prerequisites

Record the stage:

    mantle stage-begin build

Resolve the project's .mantle/ directory:

    MANTLE_DIR="${MANTLE_DIR:-$(mantle where)}"

All subsequent `Read` and `Grep`/`Glob` calls must use `$MANTLE_DIR/...`.

Read `$MANTLE_DIR/state.md` and verify:
- `.mantle/` exists (if not, tell the user to run `mantle init`)
- Status is `planning` or `implementing`
- If earlier, tell the user and suggest the appropriate next command

Read `$MANTLE_DIR/product-design.md` and `$MANTLE_DIR/system-design.md`. If
neither exists, stop:

> The build pipeline automates from design to verified code. You need at least
> a product design first. Run `claude/commands/mantle/design-product.md` to get started.

Check git working tree status. If dirty:

1. Resolve the target issue's `slice:` field from `$MANTLE_DIR/issues/issue-{NN}.md`.
2. Run `git status --short` and inspect each dirty path.
3. If any dirty path maps to a slice layer (`tests/` ↔ tests, `src/mantle/cli/` ↔ cli,
   `src/mantle/core/` ↔ core, `claude/` or `.claude/` ↔ claude-code) — **hard warning**:
   the overlap contaminates the issue's commit range and breaks Step 7's simplifier scope.
   Report explicitly, show which paths overlap which slice, require commit/stash before proceeding.
4. If no overlap, report as a soft warning and ask whether to proceed or commit/stash first.

Example overlap report:

> **Dirty tree overlaps issue slice.** Issue {NN}'s slice is `tests, cli`.
> These dirty files overlap:
> - `tests/core/test_foo.py` → tests slice
> - `src/mantle/cli/bar.py` → cli slice
>
> Commit or stash before building — otherwise the simplifier in Step 7
> cannot distinguish issue-58 code from this prior work.

## Step 2 — Select issue

Use `$ARGUMENTS` as the issue number if provided. Otherwise, read
`$MANTLE_DIR/issues/` for issues with status `planned` or `implementing`;
if multiple, show list and ask; if one, confirm it.

Display:
> **Building issue {NN}**: {title}
> **Slice**: {slices}
> **Status**: {status}
> **Stories**: {count} planned

## Step 3 — Load skills and model tier

1. Run `mantle list-skills`.
2. Run `mantle update-skills --issue {NN}` — auto-detects matching vault skills.
3. Run `mantle model-tier` and record as `STAGE_MODELS`. Pass each stage's model
   via the Agent tool's `model:` parameter. If a stage's value is unknown, drop
   `model:` and warn in Step 9.
4. For any technology in the issue without a matching vault skill, create it by
   spawning an Agent (`subagent_type: "general-purpose"`) with:

   > Read `claude/commands/mantle/add-skill.md`. Follow Steps 1-7.
   >
   > Build-mode overrides:
   > - No user interaction — auto-fill all fields
   > - Proficiency: "5/10" (baseline for AI-authored skills)
   > - Skip the "offer to continue" step
   >
   > Skill to create: {technology/pattern name}

   Use model `STAGE_MODELS.plan_stories`. After each skill is created, run
   `mantle update-skills --issue {NN}` again.

5. Run `mantle compile --issue {NN}`.

## Output Format — Step 3

> **Skills loaded:** {list of matched skills}
> **Skills created:** {list of new skills, or "none"}
> **Model tier:** {preset or "balanced (fallback)"} —
> shape={shape}, plan_stories={plan_stories}, implement={implement},
> simplify={simplify}, verify={verify}, review={review}, retrospective={retrospective}

## Step 4 — Shape (inline)

Record the stage:

    mantle stage-begin shape

Runs inline. Check if `$MANTLE_DIR/shaped/issue-{NN}-shaped.md` exists.

**If already shaped**, read it and report:
> **Shape:** Already shaped — approach: {chosen_approach}, appetite: {appetite}

**If not shaped**, read `claude/commands/mantle/shape-issue.md` and follow
Steps 2-5 with these build-mode overrides:
- No user interaction — auto-choose the smallest-appetite approach that
  satisfies all acceptance criteria
- Follow Step 2.3 "Load skills" **as written** — run `mantle list-skills`,
  select 2-4 matching skills, read each in full. Do **not** substitute compile
  output — `mantle compile` often omits internal-tooling skills.
- **Evidence requirement (Iron Law #5):** For each skill named in the report,
  make a `Read` call on `.claude/skills/<slug>/references/core.md` (fallback
  `.claude/skills/<slug>/SKILL.md`) before reporting. Drop skills you did not Read.
- **Report format:**

  > **Skills read:**
  > - `cyclopts` → `.claude/skills/cyclopts/references/core.md`

- Skip the "next steps" recommendation

Report:
> **Auto-shaped issue {NN}:** {chosen approach} — {appetite}

## Step 5 — Plan stories (inline)

Record the stage:

    mantle stage-begin plan_stories

Check if stories exist in `$MANTLE_DIR/stories/issue-{NN}-story-*.md`.

**If already planned**, read them and report:
> **Stories:** {count} stories already planned. Proceeding to implementation.

**If not**, read `claude/commands/mantle/plan-stories.md` and follow Steps 2-5c:
- Auto-approve all stories — no user input
- Skip the "next steps" recommendation

Report:
> **Stories planned:** {count}
> **Acceptance criteria coverage:** {covered}/{total}

## Step 6 — Implement

Before any `mantle transition-*` or `mantle save-*` command, capture the
pre-implement git rev:

    git rev-parse HEAD

Record as `PRE_IMPLEMENT_REV`; Step 7 needs it. Then:

    mantle transition-issue-implementing --issue {NN}

### Fast-path eligibility check

All four must be true for Branch A:

1. Exactly one file is named in the shaped doc's Strategy section.
2. The Strategy describes a removal, rename, or edit of ≤ 10 lines.
3. No acceptance criterion mentions new tests or new CLI surface.
4. The shaped appetite is `small batch`.

### Branch A — Fast-path (inline edit)

1. Use `Read` + `Edit` or `Write` to make the change.
2. Run `just check`.
3. If `just check` fails, revert (`git checkout -- <file>`) and fall back to Branch B.
4. On success: `git add <file> && git commit -m "<conventional message>"`.

**Step 8 (Verify) runs regardless — fast-path only skips the agent spawn.**

Report:
> **Story 1:** {title} — completed (fast-path)

### Branch B — Agent-path (default)

Read `claude/commands/mantle/implement.md` and follow Steps 3-5:
- Skip user confirmation on issue selection
- Don't recommend next steps
- Pass `STAGE_MODELS.implement` to every per-story Agent spawn, including retries

Report after each story:
> **Story {S}:** {title} — {completed/blocked}

If any story is blocked after retry, stop. Do not continue to Step 7.

---

After both branches complete:

    mantle transition-issue-implemented --issue {NN}

**Inbox capture:** Capture off-topic patterns or ideas via
`mantle save-inbox-item --title "..." --description "..." --source ai`.
Don't interrupt the pipeline.

## Step 7 — Simplify (conditional)

Run `mantle collect-issue-diff-stats --issue {NN}`. Skip only when **both**
`files ≤ 3` **AND** `lines_changed ≤ 50`. Otherwise run.

Report one of:
> **Simplification:** Skipped (files=N, lines_changed=N — below threshold)
> **Simplification:** Running (files=N, lines_changed=N — above threshold)

Stats count only `src/` and `tests/` paths.

**If running**, capture:

    git diff --name-only $PRE_IMPLEMENT_REV..HEAD -- src/ tests/

Spawn an Agent (`subagent_type: "refactorer"`, model `STAGE_MODELS.simplify`):

> Before starting, review your project memory for relevant context.
>
> Read `claude/commands/mantle/simplify.md`. Follow Steps 2-6.
>
> Build-mode overrides:
> - Use issue-scoped mode with issue number {NN}
> - Don't ask about dirty working tree — the build pipeline manages git state
>
> **Scope is fixed. You may only edit files in this exact list:**
>
> ```
> {file-list-from-git-diff}
> ```
>
> Any file outside this list is out of scope — report it for a follow-up if it
> genuinely needs changes.
>
> **Python version note:** this project is Python 3.14+. PEP 758 allows
> `except A, B:` without parentheses — do not "fix" it.
>
> When done, report: files reviewed, files simplified, tests passed.

After the agent returns, run the project's test command yourself. If tests
fail, revert the simplification commit and continue to Step 8.

## Output Format — Step 7

> **Simplification:** {files simplified}/{files reviewed} files changed
> **Post-simplify tests:** {passed/failed}

## Step 8 — Verify (agent)

Spawn an Agent (`subagent_type: "general-purpose"`, model `STAGE_MODELS.verify`):

> Before starting, review your project memory for relevant context.
>
> Read `claude/commands/mantle/verify.md`. Follow Steps 3-8.
>
> Build-mode overrides:
> - Skip user confirmation — auto-verify all criteria
> - Check `$MANTLE_DIR/config.md` for `verification_strategy` first. If set,
>   use it verbatim. If absent, run `mantle introspect-project` and save via
>   `mantle save-verification-strategy --strategy "<generated strategy>"`.
>
> Issue number: {NN}
>
> When done:
> 1. If all criteria pass, call `mantle transition-issue-verified --issue {NN}`.
> 2. Report: per-criterion pass/fail table and overall result (PASSED/FAILED).

Report the agent's verification table and overall result.

## Step 9 — Summary

> ## Build Pipeline Complete — Issue {NN}
>
> | Stage | Result |
> |-------|--------|
> | Shape | {auto-shaped / pre-existing} |
> | Model tier | {preset} |
> | Skills | {count loaded, count gaps} |
> | Stories | {count} planned |
> | Implementation | {completed/blocked} stories |
> | Simplification | {files changed} |
> | Verification | {PASSED / FAILED} |
> | Build report | `.mantle/builds/build-{NN}-<timestamp>.md` |
> | Inbox ideas | {count captured, or "none"} |
>
> **Total commits:** {count}

If inbox items were captured, list:

> **Ideas captured:**
> - {title} — {description}

**If verification passed:**

> **Recommended next step:** `claude/commands/mantle/review.md` — human review
> of acceptance criteria.
>
> After review: `claude/commands/mantle/retrospective.md` to capture learnings.

**If verification failed or stories blocked:**

> **Pipeline stopped.** Fix the issues listed above and re-run
> `claude/commands/mantle/build.md {NN}` to resume. Stories already completed
> will be skipped.

---

Pipeline sequence:
1. Prerequisites → 2. Select issue → 3. Load skills → 4. Shape →
5. Plan stories → 6. Implement → 7. Simplify → 8. Verify → 9. Summary
"""),
    )
    assert result.matches, result.diff

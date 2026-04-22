---
description: Use when you want to take a planned issue from design to verified code in one automated pass
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle *), Bash(git add*), Bash(git commit*), Bash(git checkout -- *), Bash(uv run pytest*), Bash(npm test*), Bash(cargo test*), Bash(go test*), Agent
---

Orchestrate the full journey from a planned issue to verified code without
requiring human confirmation at each step.

## Iron Laws

These rules are absolute. There are no exceptions, no "just this once", no edge cases.

1. **NO skipping steps.** Every step runs unless its explicit skip condition is met. Each catches different problems.
2. **NO claiming pipeline success without verification evidence.** Step 8 must run and produce a per-criterion result. "It probably passes" is not a result.
3. **NO continuing past blocked stories.** If Step 6 blocks, the pipeline stops. Do not optimistically continue to simplification or verification.
4. **NO silent failures.** If any step produces errors or warnings, they are reported verbatim — never summarised away.
5. **NO reporting "Skills loaded" without Read evidence.** In Step 4, every skill named in the report must correspond to an actual `Read` call on that skill's reference file (`.claude/skills/<slug>/references/core.md` or `.claude/skills/<slug>/SKILL.md`). Substituting "I skimmed a codebase example" for reading the skill file is the violation — skill files encode patterns and anti-patterns that codebase samples do not surface.

### Red Flags — thoughts that mean STOP

If you catch yourself thinking any of these, you are about to violate an Iron Law:

| Thought | Reality |
|---------|---------|
| "Simplification isn't needed, the code looks clean" | You haven't reviewed it yet. Run the step. |
| "Verification will pass, the tests already passed" | Tests check code correctness. Verification checks acceptance criteria. Different things. |
| "I'll skip skill loading since we already have skills" | Skills may be stale or missing for new technologies in this issue. |
| "I'll list the skills I *would* consult — naming them is enough" | Naming a skill is not loading it. If you have not Read the file, the skill is not loaded. |
| "The codebase example I read covers what the skill would say" | Skill files encode patterns and anti-patterns that codebase samples do not surface. Read the skill. |
| "The story is blocked but the rest are independent, I'll continue" | Blocked stories signal problems that may affect dependent work. Stop. |
| "I can report the pipeline result without running verification" | A build without verification is an unverified build. Run Step 8. |

Use TaskCreate to create a task for each of the 9 steps:
1. "Step 1 — Prerequisites" … 9. "Step 9 — Summary"

Use TaskUpdate to set each to `in_progress` when starting, `completed` when
done. This creates a persistent progress tracker visible above the input bar.

Stop early only if a story is blocked after retry in Step 6. Report progress
at each stage; don't ask for permission. Surface problems immediately.

**Tip:** Start a fresh conversation before running this command — prior
conversation history adds noise.

## Step 1 — Prerequisites

Resolve the project's .mantle/ directory:

    MANTLE_DIR="${MANTLE_DIR:-$(mantle where)}"

All subsequent `Read` and `Grep`/`Glob` calls must use `$MANTLE_DIR/...` in
place of `.mantle/...`.

Read `$MANTLE_DIR/state.md` and verify:
- `.mantle/` exists (if not, tell the user to run `mantle init`)
- Status is `planning` or `implementing`
- If status is earlier, tell the user the current status and suggest the
  appropriate next command

Read `$MANTLE_DIR/product-design.md` and `$MANTLE_DIR/system-design.md`. If
neither exists, stop:

> The build pipeline automates from design to verified code. You need at least
> a product design first. Run `claude/commands/mantle/design-product.md` to get started.

Check git working tree status. If dirty:

1. Resolve the target issue's `slice:` field from
   `$MANTLE_DIR/issues/issue-{NN}.md` (or the issue file the user named).
2. Run `git status --short` and inspect each dirty path.
3. If any dirty path maps to one of the issue's slice layers (`tests/` ↔ tests
   slice, `src/mantle/cli/` ↔ cli slice, `src/mantle/core/` ↔ core slice,
   `claude/` or `.claude/` ↔ claude-code slice), this is a **hard warning** —
   the overlap will contaminate the issue's commit range and break Step 7's
   simplifier scope. Report it explicitly, show which dirty paths overlap which
   slice, and require the user to commit/stash before proceeding.
4. If no overlap, report dirty paths as a soft warning and ask whether to
   proceed or commit/stash first.

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
2. Run `mantle update-skills --issue {NN}` — auto-detects matching vault skills,
   updating `skills_required` in `state.md`.
3. Run `mantle model-tier` and record the result as `STAGE_MODELS`. Pass each
   stage's model via the Agent tool's `model:` parameter (e.g. Step 7 uses
   `STAGE_MODELS.simplify`, Step 8 uses `STAGE_MODELS.verify`). If a stage's
   value is unknown to the Agent tool, drop `model:` and warn in Step 9.
4. Read the issue to identify technologies. For any technology without a
   matching vault skill, create it by spawning an Agent
   (`subagent_type: "general-purpose"`) with:

   > Read `claude/commands/mantle/add-skill.md` for detailed instructions.
   > Follow Steps 1-7.
   >
   > Build-mode overrides:
   > - No user interaction — auto-fill all fields based on your knowledge
   > - Use a proficiency of "5/10" (baseline for AI-authored skills)
   > - Skip the "offer to continue" step (Step 8 in that file)
   >
   > Skill to create: {technology/pattern name}

   Use model `STAGE_MODELS.plan_stories` for this agent spawn. After each
   skill is created, run `mantle update-skills --issue {NN}` again.

5. Run `mantle compile --issue {NN}` to compile issue-relevant vault skills
   into `.claude/skills/`.

## Output Format — Step 3

> **Skills loaded:** {list of matched skills}
> **Skills created:** {list of new skills, or "none"}
> **Model tier:** {preset or "balanced (fallback)"} —
> shape={shape}, plan_stories={plan_stories}, implement={implement},
> simplify={simplify}, verify={verify}, review={review}, retrospective={retrospective}

## Step 4 — Shape (inline)

Runs inline (no agent spawn). (`STAGE_MODELS.shape` reserved for future
out-of-process shape agents.)

Check if `$MANTLE_DIR/shaped/issue-{NN}-shaped.md` exists.

**If already shaped**, read it and report:
> **Shape:** Already shaped — approach: {chosen_approach}, appetite: {appetite}

**If not shaped**, read `claude/commands/mantle/shape-issue.md` and follow
Steps 2-5 with these build-mode overrides:
- No user interaction — auto-choose the smallest-appetite approach that
  satisfies all acceptance criteria
- Follow `shape-issue.md` Step 2.3 "Load skills" **as written** — run
  `mantle list-skills`, select 2-4 skills whose descriptions directly match
  the work, and read each selected skill's full content. Do **not** substitute
  "read whatever compile emitted" — `mantle compile` only populates
  `.claude/skills/` for auto-matched skills, which is often empty for
  internal-tooling issues.
- **Evidence requirement (Iron Law #5):** For each skill named in the Step 4
  report, you MUST make a `Read` tool call on that skill's reference file
  before reporting. Path: `.claude/skills/<slug>/references/core.md`
  (fallback `.claude/skills/<slug>/SKILL.md`). "Reading a codebase example
  instead" does not satisfy this — codebase samples lack the patterns and
  anti-patterns that skill files encode.
- **Report format:** include an explicit evidence block listing each skill
  with the exact path Read, e.g.:

  > **Skills read:**
  > - `cyclopts` → `.claude/skills/cyclopts/references/core.md`

  Drop any skill you did not Read.
- Skip the "next steps" recommendation (Step 6 in that file)

Report:
> **Auto-shaped issue {NN}:** {chosen approach} — {appetite}

## Step 5 — Plan stories (inline)

Runs inline (no agent spawn). (`STAGE_MODELS.plan_stories` reserved for future
out-of-process agents.)

Check if stories exist in `$MANTLE_DIR/stories/issue-{NN}-story-*.md`.

**If stories already exist**, read them and report:
> **Stories:** {count} stories already planned. Proceeding to implementation.

**If no stories exist**, read `claude/commands/mantle/plan-stories.md` and
follow Steps 2-5c with these build-mode overrides:
- Auto-approve all stories — don't wait for user input
- Skip the "next steps" recommendation (Step 6 in that file)

Report:
> **Stories planned:** {count}
> **Acceptance criteria coverage:** {covered}/{total}

## Step 6 — Implement

Before any `mantle transition-*` or `mantle save-*` command runs, capture
the pre-implement git rev (those commands can trigger auto-commits):

    git rev-parse HEAD

Record as `PRE_IMPLEMENT_REV`; Step 7 needs it. Then transition:

    mantle transition-issue-implementing --issue {NN}

### Fast-path eligibility check

Check all four against the shaped doc before deciding which branch to take:

1. Exactly one file is named in the shaped doc's Strategy section.
2. The Strategy describes a removal, rename, or edit of ≤ 10 lines.
3. No acceptance criterion mentions new tests or new CLI surface.
4. The shaped appetite is `small batch`.

**Fast-path condition:** If all four rubric items are true, take Branch A.
Otherwise, take Branch B.

### Branch A — Fast-path (inline edit)

1. Use `Read` + `Edit` or `Write` to make the change in the shaped doc's
   Strategy section.
2. Run `just check` (or the project's check command from CLAUDE.md).
3. If `just check` fails, revert (`git checkout -- <file>`) and fall back to
   Branch B.
4. On success: `git add <file> && git commit -m "<conventional message>"`.

**Step 8 (Verify) runs regardless — the fast-path only skips Step 6's agent
spawn, never Step 8.**

Report:
> **Story 1:** {title} — completed (fast-path)

### Branch B — Agent-path (default)

Read `claude/commands/mantle/implement.md` and follow Steps 3-5 with these
build-mode overrides:
- Skip user confirmation on issue selection
- Don't recommend next steps — the pipeline continues automatically
- Pass `STAGE_MODELS.implement` to every per-story Agent spawn inside
  implement.md's Step 4 loop. Other Agent spawns (e.g. retry agents) use the
  same value.

Report after each story:
> **Story {S}:** {title} — {completed/blocked}

If any story is blocked after retry, stop the pipeline here. Do not continue
to Step 7.

---

After both branches complete successfully:

    mantle transition-issue-implemented --issue {NN}

**Inbox capture:** Silently capture off-topic patterns, ideas, or improvements
via `mantle save-inbox-item --title "..." --description "..." --source ai`.
Don't interrupt the pipeline.

## Step 7 — Simplify (conditional)

**Skip condition:** Run `mantle collect-issue-diff-stats --issue {NN}` to read
`files`, `lines_added`, `lines_removed`, and `lines_changed` (added+removed).
Skip only when **both** `files ≤ 3` **AND** `lines_changed ≤ 50`. Otherwise run.

Report one of:
> **Simplification:** Skipped (files=N, lines_changed=N — below threshold)
> **Simplification:** Running (files=N, lines_changed=N — above threshold)

The stats command counts only `src/` and `tests/` paths.

**If running**, capture the exact file list:

    git diff --name-only $PRE_IMPLEMENT_REV..HEAD -- src/ tests/

Record the file list, then spawn an Agent (`subagent_type: "refactorer"`) with:

Use model `STAGE_MODELS.simplify` for this agent spawn.

> Before starting, review your project memory for relevant context.
>
> Read `claude/commands/mantle/simplify.md` for detailed instructions.
> Follow Steps 2-6.
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
> Any other file is out of scope, even if you notice a smell there. If a file
> outside this list genuinely needs changes, report it in your summary — the
> orchestrator will file a follow-up. Files listed above were introduced or
> modified by this issue; nothing else was.
>
> **Python version note:** this project is Python 3.14+. PEP 758 allows
> `except A, B:` without parentheses — do not "fix" it back to
> `except (A, B):`. Consult the `python-314` skill if unsure.
>
> When done, report: files reviewed count, files simplified count, and whether
> tests passed after simplification.

After the agent returns, **run the project's test command yourself** (e.g.,
`uv run pytest`) — the refactorer agent may not have bash access. If tests
fail, revert the simplification commit and continue to Step 8.

## Output Format — Step 7

> **Simplification:** {files simplified}/{files reviewed} files changed
> **Post-simplify tests:** {passed/failed}

## Step 8 — Verify (agent)

Spawn an Agent (`subagent_type: "general-purpose"`) with:

Use model `STAGE_MODELS.verify` for this agent spawn.

> Before starting, review your project memory for relevant context.
>
> Read `claude/commands/mantle/verify.md` for detailed instructions.
> Follow Steps 3-8.
>
> Build-mode overrides:
> - Skip user confirmation — auto-verify all criteria
> - **Verification strategy precedence**: check
>   `$MANTLE_DIR/config.md` for a non-empty `verification_strategy` field
>   first. If present, use it verbatim. Only if absent or empty, run
>   `mantle introspect-project` as a last-resort fallback, then save via
>   `mantle save-verification-strategy --strategy "<generated strategy>"`.
> - Do not ask the user to define a strategy.
>
> Issue number: {NN}
>
> When done:
> 1. If all criteria pass, call `mantle transition-issue-verified --issue {NN}`
>    (verify.md Step 8 requires this — do not skip it).
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

If inbox items were captured via `mantle save-inbox-item --source ai`, list:

> **Ideas captured:**
> - {title} — {description}

**If verification passed:**

> **Recommended next step:** `claude/commands/mantle/review.md` — human review
> of acceptance criteria. This is the one checkpoint that matters.
>
> After review: `claude/commands/mantle/retrospective.md` to capture learnings.

**If verification failed or stories blocked:**

> **Pipeline stopped.** Fix the issues listed above and re-run
> `claude/commands/mantle/build.md {NN}` to resume from where it left off.
> Stories already completed will be skipped.

---

Reminder — the full pipeline sequence is:
1. Prerequisites → 2. Select issue → 3. Load skills → 4. Shape →
5. Plan stories → 6. Implement → 7. Simplify → 8. Verify → 9. Summary

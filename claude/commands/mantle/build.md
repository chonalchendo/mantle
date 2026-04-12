---
description: Use when you want to take a planned issue from design to verified code in one automated pass
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle *), Bash(git add*), Bash(git commit*), Bash(git checkout -- *), Bash(uv run pytest*), Bash(npm test*), Bash(cargo test*), Bash(go test*), Agent
---

Orchestrate the full journey from a planned issue to verified code — without
requiring human confirmation at each intermediate step.

## Iron Laws

These rules are absolute. There are no exceptions, no "just this once", no edge cases.

1. **NO skipping steps.** Every step runs unless its explicit skip condition is met. Each catches different problems.
2. **NO claiming pipeline success without verification evidence.** Step 8 must run and produce a per-criterion result. "It probably passes" is not a result.
3. **NO continuing past blocked stories.** If Step 6 blocks, the pipeline stops. Do not optimistically continue to simplification or verification.
4. **NO silent failures.** If any step produces errors or warnings, they are reported verbatim — never summarised away.

### Red Flags — thoughts that mean STOP

If you catch yourself thinking any of these, you are about to violate an Iron Law:

| Thought | Reality |
|---------|---------|
| "Simplification isn't needed, the code looks clean" | You haven't reviewed it yet. Run the step. |
| "Verification will pass, the tests already passed" | Tests check code correctness. Verification checks acceptance criteria. Different things. |
| "I'll skip skill loading since we already have skills" | Skills may be stale or missing for new technologies in this issue. |
| "The story is blocked but the rest are independent, I'll continue" | Blocked stories signal problems that may affect dependent work. Stop. |
| "I can report the pipeline result without running verification" | A build without verification is an unverified build. Run Step 8. |

The pipeline has 9 steps. Execute them in order. Before starting, use
TaskCreate to create a task for each step:

1. "Step 1 — Prerequisites"
2. "Step 2 — Select issue"
3. "Step 3 — Load skills"
4. "Step 4 — Shape"
5. "Step 5 — Plan stories"
6. "Step 6 — Implement"
7. "Step 7 — Simplify"
8. "Step 8 — Verify"
9. "Step 9 — Summary"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`. This creates a persistent
progress tracker visible above the input bar throughout the build.

The only reason to stop early is if a story is blocked after retry in Step 6.
Every other step always runs because each one catches different problems —
skill loading ensures implementation agents have domain knowledge,
simplification removes bloat that verification would otherwise flag, and
verification catches issues that implementation missed.

Be efficient, transparent, and progress-focused. Report what you're doing at
each stage but don't ask for permission. Surface problems immediately.

**Tip:** For best results, start a fresh conversation before running this
command. It reads all context it needs from `.mantle/` — prior conversation
history just adds noise and slows things down.

## Step 1 — Prerequisites

First, resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls in this prompt must use
`$MANTLE_DIR/...` in place of `.mantle/...`.

Read `$MANTLE_DIR/state.md` and verify:
- `.mantle/` exists (if not, tell the user to run `mantle init`)
- Status is `planning` or `implementing`
- If status is earlier, tell the user the current status and suggest the
  appropriate next command

Read `$MANTLE_DIR/product-design.md` and `$MANTLE_DIR/system-design.md`. If
neither exists, stop:

> The build pipeline automates from design to verified code. You need at least
> a product design first. Run `claude/commands/mantle/design-product.md` to get started.

Check git working tree status. If dirty, warn the user and ask whether to
proceed or commit/stash first.

## Step 2 — Select issue

If the user provided `$ARGUMENTS`, use that as the issue number.
Otherwise, read `$MANTLE_DIR/issues/` to find issues with status `planned` or
`implementing`. If multiple exist, show the list and ask the user which to
build. If only one exists, confirm it.

Display:
> **Building issue {NN}**: {title}
> **Slice**: {slices}
> **Status**: {status}
> **Stories**: {count} planned

## Step 3 — Load skills

Why: vault skills give agents domain-specific knowledge (patterns, conventions,
anti-patterns) that improves both shaping decisions and code quality. Loading
skills first ensures the shaping agent can make informed approach choices.

1. Run `mantle list-skills` to see what skills exist in the vault.
2. Run `mantle update-skills --issue {NN}` to auto-detect which vault skills
   match the issue, updating `skills_required` in `state.md`.
3. Read the issue to identify technologies and patterns involved. For any
   technology referenced that doesn't have a matching vault skill, create
   it now by spawning an Agent (`subagent_type: "general-purpose"`) with this prompt:

   > Read `claude/commands/mantle/add-skill.md` for detailed instructions.
   > Follow Steps 1-7.
   >
   > Build-mode overrides:
   > - No user interaction — auto-fill all fields based on your knowledge
   > - Use a proficiency of "5/10" (baseline for AI-authored skills)
   > - Skip the "offer to continue" step (Step 8 in that file)
   >
   > Skill to create: {technology/pattern name}

   After each skill is created, run `mantle update-skills --issue {NN}` again
   to pick up the new skill.

4. Run `mantle compile --issue {NN}` to compile only issue-relevant vault
   skills into `.claude/skills/` so they are available to shaping, planning,
   and implementation agents.

Report:
> **Skills loaded:** {list of matched skills}
> **Skills created:** {list of new skills, or "none"}

## Step 4 — Shape (inline)

Why: shaping evaluates approaches before committing to one, preventing wasted
implementation effort on suboptimal designs. Skills loaded in Step 3 provide
domain knowledge that informs approach selection.

**Performance note:** This step runs inline (no agent spawn) to avoid
unnecessary startup overhead. The build orchestrator already has all the
context needed.

Check if `$MANTLE_DIR/shaped/issue-{NN}-shaped.md` exists.

**If already shaped**, read it and report:
> **Shape:** Already shaped — approach: {chosen_approach}, appetite: {appetite}

**If not shaped**, read `claude/commands/mantle/shape-issue.md` and follow
Steps 2-5 directly with these build-mode overrides:
- No user interaction — auto-choose the smallest-appetite approach that
  satisfies all acceptance criteria
- Read any compiled skills in `.claude/skills/*/SKILL.md` that are relevant
  to this issue — they contain domain knowledge that should inform approach
  evaluation
- Skip the "next steps" recommendation (Step 6 in that file)

Report the result:
> **Auto-shaped issue {NN}:** {chosen approach} — {appetite}

## Step 5 — Plan stories (inline)

Why: stories break the issue into session-sized units so each implementation
agent has focused, completable work with clear test criteria.

**Performance note:** This step runs inline (no agent spawn) to avoid
unnecessary startup overhead.

Check if stories exist in `$MANTLE_DIR/stories/issue-{NN}-story-*.md`.

**If stories already exist**, read them and report:
> **Stories:** {count} stories already planned. Proceeding to implementation.

**If no stories exist**, read `claude/commands/mantle/plan-stories.md` and
follow Steps 2-5c directly with these build-mode overrides:
- Auto-approve all stories — don't wait for user input on each story
- Skip the "next steps" recommendation (Step 6 in that file)

Report the result:
> **Stories planned:** {count}
> **Acceptance criteria coverage:** {covered}/{total}

## Step 6 — Implement

Why: each story is implemented by a dedicated agent with focused context,
then verified with tests before moving to the next.

Before reading implement.md, transition the issue to implementing:

    mantle transition-issue-implementing --issue {NN}

Read `claude/commands/mantle/implement.md` and follow Steps 3-5 with these
build-mode overrides:
- Skip user confirmation on issue selection
- Don't recommend next steps — the pipeline continues automatically

Report progress after each story:
> **Story {S}:** {title} — {completed/blocked}

If any story is blocked after retry, stop the pipeline here. Do not continue
to Step 7.

After all stories complete successfully, transition the issue to implemented:

    mantle transition-issue-implemented --issue {NN}

**Inbox capture:** During implementation, if you spot patterns, ideas, or
potential improvements that aren't part of the current issue, silently capture
them via `mantle save-inbox-item --title "..." --description "..." --source ai`.
Do not interrupt the pipeline — just save and continue. These will be reported
in Step 9.

## Step 7 — Simplify (conditional)

Why: AI-generated code accumulates bloat (unnecessary abstractions, defensive
over-engineering, dead code). Cleaning this up before verification produces
cleaner code and fewer false verification issues.

**Skip condition:** Run `mantle collect-issue-diff-stats --issue {NN}` to read
`files`, `lines_added`, `lines_removed`, and `lines_changed` (added+removed).
Skip simplification only when **both** `files ≤ 3` **AND** `lines_changed ≤ 50`.
Otherwise, run simplification. Report one of:
> **Simplification:** Skipped (files=N, lines_changed=N — below threshold)
> **Simplification:** Running (files=N, lines_changed=N — above threshold)

**If the skip condition is not met**, spawn an Agent (`subagent_type: "refactorer"`) with this prompt:

> Before starting, review your project memory for relevant context.
>
> Read `claude/commands/mantle/simplify.md` for detailed instructions.
> Follow Steps 2-6.
>
> Build-mode overrides:
> - Use issue-scoped mode with issue number {NN}
> - Don't ask about dirty working tree — the build pipeline manages git state
>
> When done, report: files reviewed count, files simplified count, and whether
> tests passed after simplification.

After the agent returns, **run the project's test command yourself** to
independently confirm the simplification didn't regress anything — the
refactorer agent may not have bash access, so its "tests passed" claim is
unverified until the orchestrator confirms. Use the test command from
CLAUDE.md (e.g., `uv run pytest`). If tests fail, revert the simplification
commit and continue to Step 8 with the pre-simplify state.

Report the agent's result:
> **Simplification:** {files simplified}/{files reviewed} files changed
> **Post-simplify tests:** {passed/failed}

## Step 8 — Verify (agent)

Why: verification checks that the implementation actually satisfies every
acceptance criterion — catching gaps that tests alone don't cover.

Spawn an Agent (`subagent_type: "general-purpose"`) with this prompt:

> Before starting, review your project memory for relevant context.
>
> Read `claude/commands/mantle/verify.md` for detailed instructions.
> Follow Steps 3-8.
>
> Build-mode overrides:
> - Skip user confirmation — auto-verify all criteria
> - If no verification strategy is configured, run
>   `mantle introspect-project` to auto-detect the project's test, lint, and
>   check commands, then save the generated strategy via
>   `mantle save-verification-strategy --strategy "<generated strategy>"`
>   before proceeding. This creates a real structured strategy for future runs.
> - Don't ask the user to define a strategy — use introspection to generate one
>
> Issue number: {NN}
>
> When done:
> 1. If all criteria pass, call `mantle transition-issue-verified --issue {NN}`
>    (verify.md Step 8 requires this — do not skip it).
> 2. Report: per-criterion pass/fail table and overall result (PASSED/FAILED).

Report the agent's verification table and overall result.

## Step 9 — Summary

Report the full pipeline run:

> ## Build Pipeline Complete — Issue {NN}
>
> | Stage | Result |
> |-------|--------|
> | Shape | {auto-shaped / pre-existing} |
> | Skills | {count loaded, count gaps} |
> | Stories | {count} planned |
> | Implementation | {completed/blocked} stories |
> | Simplification | {files changed} |
> | Verification | {PASSED / FAILED} |
> | Inbox ideas | {count captured, or "none"} |
>
> **Total commits:** {count}

If any inbox items were captured during the pipeline (via
`mantle save-inbox-item --source ai`), list them:

> **Ideas captured:**
> - {title} — {description}

**If verification passed:**

> **Recommended next step:** `claude/commands/mantle/review.md` — human review of acceptance
> criteria. This is the one checkpoint that matters.
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

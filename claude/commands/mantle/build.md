---
description: Automated build pipeline — shape, plan stories, implement, and verify in one pass
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle *), Bash(git add*), Bash(git commit*), Bash(git checkout -- *), Bash(uv run pytest*), Bash(npm test*), Bash(cargo test*), Bash(go test*), Agent
---

You are the automated build pipeline for a Mantle project. You orchestrate the
full journey from a planned issue to verified code — shaping, story planning,
implementation, simplification, and verification — without requiring human
confirmation at each intermediate step.

**Philosophy:** Checkpoints at phase boundaries, automation within phases. The
user has already defined _what_ to build (issue). You handle _how_ to build it.
The user reviews the output, not the process.

Tone: efficient, transparent, and progress-focused. Report what you're doing at
each stage but don't ask for permission. Surface problems immediately.

**Tip:** For best results, start a fresh conversation before running this
command. It reads all context it needs from `.mantle/` — prior conversation
history just adds noise and slows things down.

## Step 1 — Prerequisites

Read `.mantle/state.md` and verify:
- `.mantle/` exists (if not, tell the user to run `mantle init`)
- Status is `planning` or `implementing`
- If status is earlier, tell the user the current status and suggest the
  appropriate next command

Read `.mantle/product-design.md` and `.mantle/system-design.md`. If neither
exists, stop:

> The build pipeline automates from design to verified code. You need at least
> a product design first. Run `/mantle:design-product` to get started.

Check git working tree status. If dirty, warn the user and ask whether to
proceed or commit/stash first.

## Step 2 — Select issue

If the user provided `$ARGUMENTS`, use that as the issue number.
Otherwise, read `.mantle/issues/` to find issues with status `planned` or
`implementing`. If multiple exist, show the list and ask the user which to
build. If only one exists, confirm it.

Display:
> **Building issue {NN}**: {title}
> **Slice**: {slices}
> **Status**: {status}
> **Stories**: {count} planned

## Step 3 — Shape (if needed)

Check if `.mantle/shaped/issue-{NN}-shaped.md` exists.

**If already shaped**, read it and report:
> **Shape:** Already shaped — approach: {chosen_approach}, appetite: {appetite}

**If not shaped**, read `claude/commands/mantle/shape-issue.md` and follow
Steps 2-5 with these build-mode overrides:
- **No user interaction** — auto-choose the smallest-appetite approach that
  satisfies all acceptance criteria
- Skip the "next steps" recommendation (Step 6)

Report your choice:
> **Auto-shaped issue {NN}:** {chosen approach} — {appetite}

## Step 4 — Plan stories (if needed)

Check if stories exist in `.mantle/stories/issue-{NN}-story-*.md`.

**If stories already exist**, read them and report:
> **Stories:** {count} stories already planned. Proceeding to implementation.

**If no stories exist**, read `claude/commands/mantle/plan-stories.md` and
follow Steps 2-5b with these build-mode overrides:
- **Auto-approve all stories** — don't wait for user input on each story
- Skip the "next steps" recommendation (Step 6)

Report:
> **Stories planned:** {count}
> **Acceptance criteria coverage:** {covered}/{total}

## Step 5 — Implement

Read `claude/commands/mantle/implement.md` and follow Steps 3-4 with these
build-mode overrides:
- Skip user confirmation on issue selection
- Don't recommend next steps — the pipeline continues automatically

Report progress after each story:
> **Story {S}:** {title} — {completed/blocked}

If any story is blocked after retry, stop the pipeline.

## Step 5b — Simplify

Only run this step if all stories completed successfully.

Read `claude/commands/mantle/simplify.md` and follow Steps 2-6 with these
build-mode overrides:
- Use issue-scoped mode (pass the issue number)
- Don't ask about dirty working tree — build manages git state

Report:
> **Simplification:** {files simplified}/{files reviewed} files changed

## Step 6 — Verify

Only run this step if all stories completed successfully.

Read `claude/commands/mantle/verify.md` and follow Steps 3-8 with these
build-mode overrides:
- Skip user confirmation — auto-verify all criteria
- If no verification strategy is configured, use a sensible default: run the
  test suite and check each acceptance criterion against the implementation
- Don't ask the user to define a strategy — just proceed

## Step 7 — Pipeline summary

Report the full pipeline run:

> ## Build Pipeline Complete — Issue {NN}
>
> | Stage | Result |
> |-------|--------|
> | Shape | {auto-shaped / pre-existing} |
> | Stories | {count} planned |
> | Implementation | {completed/blocked} stories |
> | Simplification | {files changed} |
> | Verification | {PASSED / FAILED} |
>
> **Total commits:** {count}

**If verification passed:**

> **Recommended next step:** `/mantle:review` — human review of acceptance
> criteria. This is the one checkpoint that matters.
>
> After review: `/mantle:retrospective` to capture learnings.

**If verification failed or stories blocked:**

> **Pipeline stopped.** Fix the issues listed above and re-run
> `/mantle:build {NN}` to resume from where it left off.
> Stories already completed will be skipped.

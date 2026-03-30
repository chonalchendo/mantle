---
description: Automated build pipeline — shape, plan stories, implement, and verify in one pass
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle *), Bash(git add*), Bash(git commit*), Bash(git checkout -- *), Bash(uv run pytest*), Bash(npm test*), Bash(cargo test*), Bash(go test*), Agent
---

You are the automated build pipeline for a Mantle project. You orchestrate the
full journey from a planned issue to verified code — without requiring human
confirmation at each intermediate step.

The pipeline has 8 steps. Execute them in order. After completing each step,
update the progress tracker below by copying it into your response with the
current step checked off. This keeps you and the user aligned on where you are.

```
## Pipeline Progress
- [ ] Step 1 — Prerequisites
- [ ] Step 2 — Select issue
- [ ] Step 3 — Shape
- [ ] Step 4 — Plan stories
- [ ] Step 5 — Implement
- [ ] Step 6 — Simplify
- [ ] Step 7 — Verify
- [ ] Step 8 — Summary
```

The only reason to stop early is if a story is blocked after retry in Step 5.
Every other step always runs because each one catches different problems —
simplification removes bloat that verification would otherwise flag, and
verification catches issues that implementation missed.

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

## Step 3 — Shape

Why: shaping evaluates approaches before committing to one, preventing wasted
implementation effort on suboptimal designs.

Check if `.mantle/shaped/issue-{NN}-shaped.md` exists.

**If already shaped**, read it and report:
> **Shape:** Already shaped — approach: {chosen_approach}, appetite: {appetite}

**If not shaped**, auto-shape the issue:

1. Read the issue, product design, system design, and any learnings from
   `.mantle/learnings/`.
2. Evaluate 2-3 approaches. For each, assess: description, appetite, tradeoffs,
   rabbit holes, no-gos.
3. Choose the smallest-appetite approach that satisfies all acceptance criteria.
4. Save via CLI:
   ```bash
   mantle save-shaped-issue \
     --issue <number> \
     --title "<issue title>" \
     --approaches "<approach 1>" --approaches "<approach 2>" \
     --chosen-approach "<selected approach name>" \
     --appetite "<appetite>" \
     --content "<full shaping write-up>"
   ```

Report:
> **Auto-shaped issue {NN}:** {chosen approach} — {appetite}

## Step 4 — Plan stories

Why: stories break the issue into session-sized units so each implementation
agent has focused, completable work with clear test criteria.

Check if stories exist in `.mantle/stories/issue-{NN}-story-*.md`.

**If stories already exist**, read them and report:
> **Stories:** {count} stories already planned. Proceeding to implementation.

**If no stories exist**, decompose the issue into stories:

1. Read the shaped issue, product design, system design, and codebase patterns.
2. Break into session-sized stories (1-3 implementation files each, tests
   included). Stories build on each other: foundation first, then layers.
3. Each story needs: title, user story, approach, implementation details, tests.
4. Save each story via CLI:
   ```bash
   mantle save-story \
     --issue <issue_number> \
     --title "<story title>" \
     --content "<full story body>"
   ```
5. Verify each acceptance criterion is covered by at least one story.

Report:
> **Stories planned:** {count}
> **Acceptance criteria coverage:** {covered}/{total}

## Step 5 — Implement

Why: each story is implemented by a dedicated agent with focused context,
then verified with tests before moving to the next.

For each story that is not "completed", in order:

1. Mark in-progress: `mantle update-story-status --issue {N} --story {S} --status in-progress`
2. Spawn a story-implementer agent (`subagent_type: "story-implementer"`)
   with the full story content, issue context, system design, and learnings.
3. Run the project's test command after the agent completes (check CLAUDE.md
   for the command — e.g. `uv run pytest`, `npm test`).
4. If tests fail, spawn one retry agent with the error output.
5. Tests pass: commit as `feat(issue-{N}): {story title}`, mark completed.
   Tests fail after retry: mark blocked, stop the pipeline here.

Report progress after each story:
> **Story {S}:** {title} — {completed/blocked}

If any story is blocked, stop here. Do not continue to Step 6.

## Step 6 — Simplify

Why: AI-generated code accumulates bloat (unnecessary abstractions, defensive
over-engineering, dead code). Cleaning this up before verification produces
cleaner code and fewer false verification issues.

1. Run `mantle collect-issue-files --issue {NN}` to get the file list.
2. Run the test suite as a baseline.
3. For each code file, spawn an implementer agent (`subagent_type: "implementer"`)
   to review and simplify — removing unnecessary abstractions, defensive
   over-engineering, code duplication, dead code, and comment noise. The agent
   must not change what the code does, only how it does it.
4. Run tests again after simplification.
   - Tests pass: commit as `refactor(issue-{NN}): simplify implementation`.
   - Tests fail: revert with `git checkout -- .` and report.

Report:
> **Simplification:** {files simplified}/{files reviewed} files changed

## Step 7 — Verify

Why: verification checks that the implementation actually satisfies every
acceptance criterion — catching gaps that tests alone don't cover.

1. Read the verification strategy from `.mantle/config.md`. If none exists,
   use a sensible default: run the test suite and check each acceptance
   criterion against the implementation.
2. For each acceptance criterion, check via tests, code reading, or running
   commands. Record Pass/Fail with detail.
3. If all pass: `mantle transition-issue-verified --issue {N}`
4. If any fail: report failures and stop. Do not transition.

Report:
> ## Verification Report — Issue {NN}
>
> | # | Criterion | Result | Detail |
> |---|-----------|--------|--------|
> | 1 | {criterion} | Pass/Fail | {detail} |
>
> **Overall: {PASSED | FAILED}**

## Step 8 — Summary

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

---

Reminder — the full pipeline sequence is:
1. Prerequisites → 2. Select issue → 3. Shape → 4. Plan stories →
5. Implement → 6. Simplify → 7. Verify → 8. Summary

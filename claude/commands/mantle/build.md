---
description: Automated build pipeline — shape, plan stories, implement, and verify in one pass
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle *), Bash(git add*), Bash(git commit*), Bash(git checkout -- *), Bash(uv run pytest*), Bash(npm test*), Bash(cargo test*), Bash(go test*), Agent
---

You are the automated build pipeline for a Mantle project. You orchestrate the
full journey from a planned issue to verified code — without requiring human
confirmation at each intermediate step.

The pipeline has 9 steps. Execute them in order. After completing each step,
update this progress tracker by printing it with the current step checked off:

- [ ] Step 1 — Prerequisites
- [ ] Step 2 — Select issue
- [ ] Step 3 — Shape
- [ ] Step 4 — Plan stories
- [ ] Step 5 — Load skills
- [ ] Step 6 — Implement
- [ ] Step 7 — Simplify
- [ ] Step 8 — Verify
- [ ] Step 9 — Summary

The only reason to stop early is if a story is blocked after retry in Step 6.
Every other step always runs because each one catches different problems —
skill loading ensures implementation agents have domain knowledge,
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

**If not shaped**, read `claude/commands/mantle/shape-issue.md` and follow
Steps 2-5 with these build-mode overrides:
- No user interaction — auto-choose the smallest-appetite approach that
  satisfies all acceptance criteria
- Skip the "next steps" recommendation (Step 6 in that file)

Report:
> **Auto-shaped issue {NN}:** {chosen approach} — {appetite}

## Step 4 — Plan stories

Why: stories break the issue into session-sized units so each implementation
agent has focused, completable work with clear test criteria.

Check if stories exist in `.mantle/stories/issue-{NN}-story-*.md`.

**If stories already exist**, read them and report:
> **Stories:** {count} stories already planned. Proceeding to skill loading.

**If no stories exist**, read `claude/commands/mantle/plan-stories.md` and
follow Steps 2-5b with these build-mode overrides:
- Auto-approve all stories — don't wait for user input on each story
- Skip the "next steps" recommendation (Step 6 in that file)

Report:
> **Stories planned:** {count}
> **Acceptance criteria coverage:** {covered}/{total}

## Step 5 — Load skills

Why: vault skills give implementation agents domain-specific knowledge
(patterns, conventions, anti-patterns) that improves code quality. Without
this step, agents work from training data alone.

1. Run `mantle list-skills` to see what skills exist in the vault.
2. Run `mantle update-skills --issue {NN}` to auto-detect which vault skills
   match the issue and stories, updating `skills_required` in `state.md`.
3. Read the issue and stories to identify technologies and patterns involved.
   For any technology referenced that doesn't have a matching vault skill,
   report the gap:
   > **Skill gap:** {technology} — no vault skill found. Consider running
   > `/mantle:add-skill` after this build to improve future implementations.
4. Run `mantle compile` to compile matched vault skills into `.claude/skills/`
   so they are available to story-implementer agents.

Report:
> **Skills loaded:** {list of matched skills}
> **Skill gaps:** {list of unmatched technologies, or "none"}

## Step 6 — Implement

Why: each story is implemented by a dedicated agent with focused context,
then verified with tests before moving to the next.

Read `claude/commands/mantle/implement.md` and follow Steps 3-4 with these
build-mode overrides:
- Skip user confirmation on issue selection
- Don't recommend next steps — the pipeline continues automatically

Report progress after each story:
> **Story {S}:** {title} — {completed/blocked}

If any story is blocked after retry, stop the pipeline here. Do not continue
to Step 7.

## Step 7 — Simplify

Why: AI-generated code accumulates bloat (unnecessary abstractions, defensive
over-engineering, dead code). Cleaning this up before verification produces
cleaner code and fewer false verification issues.

Read `claude/commands/mantle/simplify.md` and follow Steps 2-6 with these
build-mode overrides:
- Use issue-scoped mode (pass the issue number)
- Don't ask about dirty working tree — build manages git state

Report:
> **Simplification:** {files simplified}/{files reviewed} files changed

## Step 8 — Verify

Why: verification checks that the implementation actually satisfies every
acceptance criterion — catching gaps that tests alone don't cover.

Read `claude/commands/mantle/verify.md` and follow Steps 3-8 with these
build-mode overrides:
- Skip user confirmation — auto-verify all criteria
- If no verification strategy is configured, use a sensible default: run the
  test suite and check each acceptance criterion against the implementation
- Don't ask the user to define a strategy — just proceed

## Step 9 — Summary

Report the full pipeline run:

> ## Build Pipeline Complete — Issue {NN}
>
> | Stage | Result |
> |-------|--------|
> | Shape | {auto-shaped / pre-existing} |
> | Stories | {count} planned |
> | Skills | {count loaded, count gaps} |
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
5. Load skills → 6. Implement → 7. Simplify → 8. Verify → 9. Summary

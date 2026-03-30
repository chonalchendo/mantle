---
description: Automated build pipeline — shape, plan stories, implement, and verify in one pass
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle *), Bash(git add*), Bash(git commit*), Bash(git checkout -- *), Bash(uv run pytest*), Bash(npm test*), Bash(cargo test*), Bash(go test*), Agent
---

Orchestrate the full journey from a planned issue to verified code — without
requiring human confirmation at each intermediate step.

The pipeline has 9 steps. Execute them in order. Before starting, use
TaskCreate to create a task for each step:

1. "Step 1 — Prerequisites"
2. "Step 2 — Select issue"
3. "Step 3 — Shape"
4. "Step 4 — Plan stories"
5. "Step 5 — Load skills"
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

Read `.mantle/state.md` and verify:
- `.mantle/` exists (if not, tell the user to run `mantle init`)
- Status is `planning` or `implementing`
- If status is earlier, tell the user the current status and suggest the
  appropriate next command

Read `.mantle/product-design.md` and `.mantle/system-design.md`. If neither
exists, stop:

> The build pipeline automates from design to verified code. You need at least
> a product design first. Run `claude/commands/mantle/design-product.md` to get started.

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

## Step 3 — Shape (agent)

Why: shaping evaluates approaches before committing to one, preventing wasted
implementation effort on suboptimal designs.

Check if `.mantle/shaped/issue-{NN}-shaped.md` exists.

**If already shaped**, read it and report:
> **Shape:** Already shaped — approach: {chosen_approach}, appetite: {appetite}

**If not shaped**, spawn an Agent (`subagent_type: "smart"`) with this prompt:

> Read `claude/commands/mantle/shape-issue.md` for detailed instructions.
> Follow Steps 2-5.
>
> Build-mode overrides:
> - No user interaction — auto-choose the smallest-appetite approach that
>   satisfies all acceptance criteria
> - Skip the "next steps" recommendation (Step 6 in that file)
>
> Issue number: {NN}
>
> When done, report: chosen approach name, appetite, and rationale.

Report the agent's result:
> **Auto-shaped issue {NN}:** {chosen approach} — {appetite}

## Step 4 — Plan stories (agent)

Why: stories break the issue into session-sized units so each implementation
agent has focused, completable work with clear test criteria.

Check if stories exist in `.mantle/stories/issue-{NN}-story-*.md`.

**If stories already exist**, read them and report:
> **Stories:** {count} stories already planned. Proceeding to skill loading.

**If no stories exist**, spawn an Agent (`subagent_type: "smart"`) with this
prompt:

> Read `claude/commands/mantle/plan-stories.md` for detailed instructions.
> Follow Steps 2-5b.
>
> Build-mode overrides:
> - Auto-approve all stories — don't wait for user input on each story
> - Skip the "next steps" recommendation (Step 6 in that file)
>
> Issue number: {NN}
>
> When done, report: story count and acceptance criteria coverage
> (covered/total).

Report the agent's result:
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
   > `claude/commands/mantle/add-skill.md` after this build to improve future implementations.
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

## Step 7 — Simplify (agent)

Why: AI-generated code accumulates bloat (unnecessary abstractions, defensive
over-engineering, dead code). Cleaning this up before verification produces
cleaner code and fewer false verification issues.

Spawn an Agent (`subagent_type: "smart"`) with this prompt:

> Read `claude/commands/mantle/simplify.md` for detailed instructions.
> Follow Steps 2-6.
>
> Build-mode overrides:
> - Use issue-scoped mode with issue number {NN}
> - Don't ask about dirty working tree — the build pipeline manages git state
>
> When done, report: files reviewed count, files simplified count, and whether
> tests passed after simplification.

Report the agent's result:
> **Simplification:** {files simplified}/{files reviewed} files changed

## Step 8 — Verify (agent)

Why: verification checks that the implementation actually satisfies every
acceptance criterion — catching gaps that tests alone don't cover.

Spawn an Agent (`subagent_type: "smart"`) with this prompt:

> Read `claude/commands/mantle/verify.md` for detailed instructions.
> Follow Steps 3-8.
>
> Build-mode overrides:
> - Skip user confirmation — auto-verify all criteria
> - If no verification strategy is configured, use a sensible default: run the
>   test suite and check each acceptance criterion against the implementation
> - Don't ask the user to define a strategy — just proceed
>
> Issue number: {NN}
>
> When done, report: per-criterion pass/fail table and overall result
> (PASSED/FAILED).

Report the agent's verification table and overall result.

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
1. Prerequisites → 2. Select issue → 3. Shape → 4. Plan stories →
5. Load skills → 6. Implement → 7. Simplify → 8. Verify → 9. Summary

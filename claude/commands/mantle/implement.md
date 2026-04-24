---
description: Use when stories are planned and ready to be implemented as code
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle update-story-status*), Bash(mantle save-learning*), Bash(git add*), Bash(git commit*), Agent
---

Implement stories for a given issue by spawning dedicated agents for each story.

## Iron Laws

These rules are absolute. No exceptions, no "just this once", no edge cases.

1. **NO completion claim WITHOUT passing tests.** Tests must run and pass — period.
2. **NO skipping stories.** Every non-completed, non-blocked story runs.
3. **NO silent failure.** Capture and report full error output — never summarise.
4. **NO continuing past a blocked story.** Blocked after retry means stop.

### Red Flags — thoughts that mean STOP

| Thought | Reality |
|---------|---------|
| "The tests probably pass, I'll skip running them" | Run them. |
| "This test failure is unrelated, I'll continue" | Unrelated failures still block. Fix or report. |
| "I'll batch the remaining stories since they're simple" | Each story gets its own agent. No batching. |
| "The retry will just fail again, I'll mark it blocked" | Run the retry. |
| "I can fix this without spawning a new agent" | Spawn the agent. |

## Dynamic Context

- **Current branch**: !`git branch --show-current`
- **Working tree status**: !`git status --short`
- **Recent commits**: !`git log --oneline -5`

**Tip:** Start a fresh conversation — prior history adds noise.

Use TaskCreate for each step. Use TaskUpdate to set `in_progress` / `completed`.
For Step 5, update the task description as stories complete ("Story 1/3 done").

**Step 1 — Check prerequisites**

Record the stage:

    mantle stage-begin implement

Resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

Use `$MANTLE_DIR/...` for all subsequent reads.

Read `$MANTLE_DIR/state.md` and verify:
- `.mantle/` exists (if not, tell the user to run `mantle init`)
- Status is `planning` or `implementing`
- If earlier, tell the user and suggest the appropriate next command

If git working tree is dirty, warn and ask whether to proceed or commit/stash.

**Step 2 — Select issue**

Use `$ARGUMENTS` as the issue number if provided. Otherwise read
`$MANTLE_DIR/issues/` and ask which to implement.

Display:
> **Issue {NN}**: {title}
> **Stories**: {story_count} planned
> **Status**: {issue status}

After confirming:

    mantle transition-issue-implementing --issue {NN}
    mantle build-start --issue {NN}

Confirm with the user before proceeding.

**Step 3 — Load context and stories**

```bash
mantle update-skills --issue {NN}
mantle compile --issue {NN}
```

Read:
- `$MANTLE_DIR/issues/issue-{NN}.md`
- `$MANTLE_DIR/system-design.md` (if it exists)
- `$MANTLE_DIR/product-design.md` (if it exists)
- `$MANTLE_DIR/stories/issue-{NN}-story-*.md`

Note story number, title, and status. Skip completed stories.

**Dependency analysis:** Read each story's `## Depends On` section. Group into waves:

- **Wave 1**: Stories with no dependencies or only already-completed dependencies.
- **Wave 2+**: Stories depending on prior waves.

Fall back to sequential by story number if no `## Depends On` section exists.

Display:
> **Execution plan:**
> - Wave 1 (parallel): Story 1, Story 2
> - Wave 2 (sequential): Story 3

**Step 4 — Select relevant context per story**

For each story, select only directly relevant context:

- `$MANTLE_DIR/learnings/` — learnings whose recommendations or patterns apply
  to the specific technology or module this story touches.
- `$MANTLE_DIR/decisions/` — decisions constraining how this story is implemented.

Build a **context brief** with: key patterns, architectural constraints, domain
knowledge.

If an item is more than 2 days old, prefix it:
> **[N days ago]** This context may reference code that has changed. Verify first.

If a learning claims something is broken or "a known bug", prefix:
> **Verify before applying:** this claim may be fixed or misscoped. Read the
> module before treating it as fact.

Skip if nothing is relevant. Skill knowledge flows through story sections — do
not inject skill files separately.

## Verification Discipline

Before claiming any outcome (story completed, tests passed, story blocked):

1. Identify the verification command.
2. Run it fresh.
3. Read the full output.
4. Confirm the output supports your claim.

**Step 5 — Implement each story**

Process stories wave by wave. Within each wave, launch stories in parallel.
Wait for all stories in a wave to finish before starting the next.

For each story:

1. **Check for blockers**: If "blocked", stop — show story number and failure_log.

2. **Mark in-progress**: `mantle update-story-status --issue {N} --story {S} --status in-progress`

3. **Spawn a story-implementer agent** (`subagent_type: "story-implementer"`).
   Use `isolation: "worktree"` for waves with 2+ stories.

   **Model selection:**
   - **`model: "opus"`** — Default. Multiple files, cross-module integration,
     design judgment, or ambiguous requirements.
   - **`model: "sonnet"`** — Single file, clear spec, no design judgment,
     obvious existing pattern.

   Never use haiku for implementation. When in doubt, use opus.

   Provide:
   - Full story content
   - Issue context
   - System design (if it exists)
   - Context brief from Step 4
   - Instruction: "Before starting, review your project memory. Implement using
     TDD: write tests first, watch them fail, then write production code. Run
     the full test suite after implementation. Show the test command and output
     as evidence. Report patterns, gotchas, or conventions for future stories."
   - Status codes: `STATUS: DONE` / `STATUS: DONE_WITH_CONCERNS` /
     `STATUS: NEEDS_CONTEXT` / `STATUS: BLOCKED` (one per line at the end).

4. **Handle agent status**:
   - **DONE**: verify tests (sub-step 5).
   - **DONE_WITH_CONCERNS**: verify tests; record concerns for commit and learnings.
   - **NEEDS_CONTEXT**: gather missing context, re-spawn with original prompt
     plus context. Counts as first attempt.
   - **BLOCKED**: mark blocked (sub-step 7). Do NOT retry.

5. **Verify tests**: Run the project's test command (from CLAUDE.md). Ask the
   user if no command is documented.

6. **Retry on failure**: If tests fail, spawn one more agent:
   "The previous attempt failed. Error output: {errors}. Diagnose and fix."
   Include status code instruction. Run tests after retry.

7. **Handle outcome**:
   - **Pass**: `git commit -m "feat(issue-{N}): {story title}"`, then
     `mantle update-story-status --issue {N} --story {S} --status completed`.
   - **Fail after retry**:
     `mantle update-story-status --issue {N} --story {S} --status blocked --failure-log "{error summary}"`
     and stop.

8. **Extract learnings**: If the agent reported patterns or gotchas:

   ```bash
   mantle save-learning \
     --issue {N} \
     --title "story-{S}: {brief topic}" \
     --confidence-delta "+0" \
     --content "<structured learnings>" \
     --overwrite
   ```

   Under 100 words. Skip if nothing noteworthy.

   **CLI divergence caveat:** If this issue changes `mantle` CLI behaviour, skip
   this call to avoid re-triggering the bug. Capture via `/mantle:retrospective`
   after releasing.

**Wave completion:**
- Any blocked story → stop, do not start the next wave.
- All completed → proceed to next wave.
- Worktree stories: merge each completed branch into main before the next wave.

**Step 6 — Report results**

    mantle build-finish --issue {NN}

## Output Format — Step 6

Summarise:
- Stories completed this run
- Stories skipped (already completed)
- Stories blocked (show failure_log)

Recommend one next step:

- `/mantle:verify` — all stories completed.
- `/mantle:simplify` — all completed but implementation was complex.
- `/mantle:implement` — a blocked story was fixed.

> **Recommended next step:** `/mantle:<command>` — [reason]
>
> Other options: [brief list]

No "I noticed", no restating the story list, no trailing summary.

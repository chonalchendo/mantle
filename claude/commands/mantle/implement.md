---
description: Use when stories are planned and ready to be implemented as code
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle update-story-status*), Bash(mantle save-learning*), Bash(git add*), Bash(git commit*), Agent
---

Implement stories for a given issue by spawning dedicated agents for each story.

## Iron Laws

These rules are absolute. There are no exceptions, no "just this once", no edge cases.

1. **NO completion claim WITHOUT passing tests.** If tests haven't run and passed, the story is not done.
2. **NO skipping stories.** Every non-completed, non-blocked story runs — either in parallel (same wave) or sequentially (across waves).
3. **NO silent failure.** If a test fails, the error output must be captured and reported — never summarised as "some tests failed".
4. **NO continuing past a blocked story.** When a story is blocked after retry, the loop stops. Period.

### Red Flags — thoughts that mean STOP

If you catch yourself thinking any of these, you are about to violate an Iron Law:

| Thought | Reality |
|---------|---------|
| "The tests probably pass, I'll skip running them" | You don't know until you run them. Run them. |
| "This test failure is unrelated, I'll continue" | Unrelated failures still block the story. Fix or report. |
| "I'll batch the remaining stories since they're simple" | Each story gets its own agent. No batching. |
| "The retry will just fail again, I'll mark it blocked" | Run the retry. You don't know the outcome in advance. |
| "I can fix this without spawning a new agent" | The orchestrator doesn't implement. Spawn the agent. |

## Dynamic Context

- **Current branch**: !`git branch --show-current`
- **Working tree status**: !`git status --short`
- **Recent commits**: !`git log --oneline -5`

**Tip:** Start a fresh conversation before running this command. It reads all
context it needs from `.mantle/` — prior conversation history adds noise.

Use TaskCreate to create a task for each step:

1. "Step 1 — Check prerequisites"
2. "Step 2 — Select issue"
3. "Step 3 — Load context and stories"
4. "Step 4 — Select relevant context per story"
5. "Step 5 — Implement each story"
6. "Step 6 — Report results"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`. For Step 5, update the
task description with progress as each story completes (e.g., "Story 1/3
done").

**Step 1 — Check prerequisites**

Resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls must use `$MANTLE_DIR/...` in
place of `.mantle/...`.

Read `$MANTLE_DIR/state.md` and verify:
- `.mantle/` exists (if not, tell the user to run `mantle init`)
- Status is `planning` or `implementing`
- If status is earlier, tell the user the current status and suggest the
  appropriate next command

If git working tree is dirty (from the dynamic context above), warn the user
and ask whether to proceed or commit/stash first.

**Step 2 — Select issue**

If the user provided `$ARGUMENTS`, use that as the issue number.
Otherwise, read `$MANTLE_DIR/issues/` to show available issues and ask which
to implement.

Display:
> **Issue {NN}**: {title}
> **Stories**: {story_count} planned
> **Status**: {issue status}

After confirming, transition to implementing (idempotent):

    mantle transition-issue-implementing --issue {NN}

Record the start of the build run:

    mantle build-start --issue {NN}

This writes a stub build record to `.mantle/builds/`; safe to ignore outside
Claude Code. Confirm with the user before proceeding.

**Step 3 — Load context and stories**

Update skills for this issue:

```bash
mantle update-skills --issue {NN}
mantle compile --issue {NN}
```

Read:
- `$MANTLE_DIR/issues/issue-{NN}.md`
- `$MANTLE_DIR/system-design.md` (if it exists)
- `$MANTLE_DIR/product-design.md` (if it exists)
- `$MANTLE_DIR/stories/issue-{NN}-story-*.md`

For each story, note: story number, title, status (planned, in-progress,
completed, blocked). Determine implementation order; skip completed stories.

**Dependency analysis:** Read each story's `## Depends On` section. Group
into **waves** for parallel execution:

- **Wave 1**: Stories with no dependencies or that depend only on
  already-completed stories.
- **Wave 2**: Stories depending on Wave 1. And so on.

If no `## Depends On` section exists, fall back to sequential execution in
ascending story number order.

Display the execution plan:
> **Execution plan:**
> - Wave 1 (parallel): Story 1, Story 2
> - Wave 2 (sequential after Wave 1): Story 3

**Step 4 — Select relevant context per story**

Before spawning each story agent, select the most relevant context from the
project's accumulated knowledge. Goal: signal, not volume.

For each story, review and select only what's directly relevant:

- `$MANTLE_DIR/learnings/` — pick learnings whose recommendations, gotchas,
  or patterns apply to the specific technology, module, or pattern this story
  touches.
- `$MANTLE_DIR/decisions/` — pick decisions about architecture or technology
  choices that constrain how this story should be implemented.

Build a **context brief** — a focused summary including:
- Key patterns or conventions from relevant learnings
- Architectural constraints from relevant decisions
- Domain knowledge from relevant skills

For each item, note its age. If modified more than 2 days ago, prefix with:

> **[N days ago]** This context may reference code or patterns that have since
> changed. Verify against current code before acting on it.

**Bug-claim caveat:** If a learning asserts something is broken, unimplemented,
or "a known bug", prefix with:

> **Verify before applying:** the claim below may have been fixed, scoped
> incorrectly, or never applied to this code path. Grep or read the named
> module before treating the claim as fact.

If nothing is relevant (first story, empty project), skip this step.

**Skill context:** Skill knowledge flows into stories via their implementation
sections. Do not separately inject skill files.

## Verification Discipline

Before claiming ANY outcome (story completed, tests passed, story blocked):

1. **Identify** the verification command.
2. **Run it** fresh — do not rely on a previous run's output.
3. **Read the full output** — not just the exit code or summary line.
4. **Confirm** the output supports your claim before making it.

"I ran the tests and they passed" requires showing which command you ran and
its output.

**Step 5 — Implement each story**

Process stories wave by wave. Within each wave, launch independent stories in
parallel. Between waves, wait for all stories to complete before starting the
next.

**For each wave**, launch all stories simultaneously. For each story:

1. **Check for blockers**: If "blocked", stop — show the story number and
   failure_log.

2. **Mark in-progress**: `mantle update-story-status --issue {N} --story {S} --status in-progress`

3. **Spawn a story-implementer agent**: Use `subagent_type: "story-implementer"`.
   For waves with 2+ stories, use `isolation: "worktree"` on each agent.
   Single-story waves don't need worktree isolation.

   **Model selection:**
   - **`model: "opus"`** — Default. Use for most stories: multiple files,
     cross-module integration, design judgment, or ambiguous requirements.
   - **`model: "sonnet"`** — Simple stories only: single file, clear spec,
     no design judgment, follows an obvious existing pattern.

   When in doubt, use opus. Never use haiku for implementation.

   Provide the agent with:
   - The full story content (from the story file)
   - The issue context (from the issue file)
   - The system design (from `$MANTLE_DIR/system-design.md` if it exists)
   - The context brief from Step 4
   - Clear instruction: "Before starting, review your project memory for
     relevant patterns, conventions, or learnings from previous stories.
     Implement this story using test-driven development: write or update tests
     FIRST, watch them fail, THEN write the production code to make them pass.
     Never write production code without a failing test that demands it. Run
     the full test suite after implementation and fix any failures. Never claim
     tests pass without running them fresh — show the command and its output as
     evidence. After completing, report any patterns you discovered, gotchas
     you encountered, or conventions you established that future stories should
     know about."
   - Status code instruction: "End your response with exactly one of these
     status codes on its own line:
     - `STATUS: DONE` — implementation complete, tests pass, no concerns.
     - `STATUS: DONE_WITH_CONCERNS` — implementation complete and tests pass,
       but you have doubts or caveats. List each concern.
     - `STATUS: NEEDS_CONTEXT` — cannot proceed without additional information.
       Describe exactly what you need.
     - `STATUS: BLOCKED` — hit an issue you cannot resolve. Describe the
       blocker in detail."

4. **Handle agent status**:
   - **DONE**: Proceed to test verification (sub-step 5).
   - **DONE_WITH_CONCERNS**: Proceed to test verification (sub-step 5); record
     concerns for commit message and extracted learnings (sub-step 8).
   - **NEEDS_CONTEXT**: Do NOT retry blindly. Gather the missing context, then
     re-spawn with the original prompt plus the additional context. This counts
     as the first attempt.
   - **BLOCKED**: Mark blocked (sub-step 7, failure path). Do NOT retry —
     the agent already determined it cannot proceed.

5. **Verify tests**: Run the project's test command to independently verify.
   Check CLAUDE.md for the command (e.g. `uv run pytest`, `npm test`,
   `cargo test`, `go test ./...`). If none documented, ask the user.

6. **Retry on failure**: If tests fail, spawn one more story-implementer agent:
   "The previous implementation attempt failed tests. Here is the error output:
   {errors}. Read the existing code, diagnose the failure, fix the issues, and
   ensure all tests pass." Include the same status code instruction.
   Run tests again after retry.

7. **Handle outcome**:
   - **Tests pass**: Commit `feat(issue-{N}): {story title}`, then run
     `mantle update-story-status --issue {N} --story {S} --status completed`.
     Append DONE_WITH_CONCERNS details to the commit body if applicable.
   - **Tests fail after retry**: Run
     `mantle update-story-status --issue {N} --story {S} --status blocked --failure-log "{error summary}"`
     and stop.

8. **Extract learnings**: If the agent reported patterns, gotchas, or
   conventions, save them:

   ```bash
   mantle save-learning \
     --issue {N} \
     --title "story-{S}: {brief topic}" \
     --confidence-delta "+0" \
     --content "<structured learnings>" \
     --overwrite
   ```

   Keep under 100 words. Focus on what would change how a future story is
   implemented. Skip if nothing noteworthy.

   **CLI divergence caveat:** If the current issue changes `mantle` CLI
   behaviour, the globally installed `mantle` may still run pre-fix code.
   Skip this call if invoking it would re-trigger the bug being fixed.
   Capture learnings via `/mantle:retrospective` after releasing instead.

**Wave completion:** After all stories in a wave finish:
- If **any story is blocked**, stop — do not start the next wave.
- If **all stories completed**, proceed to the next wave.
- For worktree-based parallel stories: merge each completed story's changes
  into the main branch before starting the next wave.

**Step 6 — Report results**

Finalize the build telemetry report:

    mantle build-finish --issue {NN}

Mention the build report path (`.mantle/builds/build-{NN}-<timestamp>.md`).

## Output Format — Step 6

Summarise:
- Stories completed this run
- Stories skipped (already completed)
- Stories blocked (if any) — show the failure_log

Assess, then recommend one next step:

- `/mantle:verify` — all stories completed successfully.
- `/mantle:simplify` — all completed but implementation was complex.
- `/mantle:implement` — a blocked story was fixed and implementation should resume.

> **Recommended next step:** `/mantle:<command>` — [reason]
>
> Other options: [brief list with one-line descriptions]

No "I noticed", no restating the story list, no trailing summary paragraph.

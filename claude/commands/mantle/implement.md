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

**Tip:** For best results, start a fresh conversation before running this command. It reads all context it needs from `.mantle/` — prior conversation history just adds noise and slows things down.

Before starting, use TaskCreate to create a task for each step:

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

Read `.mantle/state.md` and verify:
- `.mantle/` exists (if not, tell the user to run `mantle init`)
- Status is `planning` or `implementing` (valid states for implementation)
- If status is earlier, tell the user the current status and suggest the appropriate next command

If git working tree is dirty (from the dynamic context above), warn the user and ask whether to proceed or commit/stash first.

**Step 2 — Select issue**

If the user provided `$ARGUMENTS`, use that as the issue number.
Otherwise, read `.mantle/issues/` to show available issues and ask the user which to implement.

Display:
> **Issue {NN}**: {title}
> **Stories**: {story_count} planned
> **Status**: {issue status}

Confirm with the user before proceeding.

**Step 3 — Load context and stories**

First, ensure skills are up to date for this issue:

```bash
mantle update-skills --issue {NN}
mantle compile
```

Then read all required context files:
- `.mantle/issues/issue-{NN}.md` — the issue specification
- `.mantle/system-design.md` — system architecture (if it exists)
- `.mantle/product-design.md` — product context (if it exists)
- `.mantle/stories/issue-{NN}-story-*.md` — all stories for this issue
- `.claude/skills/*/SKILL.md` — compiled vault skills (these provide domain-specific knowledge to story agents)

For each story, note:
- Story number, title, current status (planned, in-progress, completed, blocked)

Determine the implementation order. Skip stories already marked "completed".

**Dependency analysis:** Read each story's `## Depends On` section. Group
stories into **waves** for parallel execution:

- **Wave 1**: Stories with no dependencies (marked "None — independent") or
  that depend only on already-completed stories.
- **Wave 2**: Stories that depend on Wave 1 stories.
- **Wave 3**: Stories that depend on Wave 2 stories. And so on.

If no `## Depends On` section exists in the stories (older format), fall back
to sequential execution in ascending story number order.

Display the execution plan:
> **Execution plan:**
> - Wave 1 (parallel): Story 1, Story 2
> - Wave 2 (sequential after Wave 1): Story 3
> - Wave 3 (sequential after Wave 2): Story 4

**Step 4 — Select relevant context per story**

Before spawning each story agent, select the most relevant context from the
project's accumulated knowledge. This is a context engineering step — the goal
is signal, not volume.

For each story, review these sources and select only what's directly relevant
to that story's implementation:

- `.mantle/learnings/` — scan all learning files. Pick learnings whose
  recommendations, gotchas, or patterns apply to the specific technology,
  module, or pattern this story touches. Skip learnings about unrelated areas.
- `.mantle/decisions/` — scan decision files. Pick decisions about architecture
  or technology choices that constrain how this story should be implemented.
  Skip decisions about unrelated subsystems.
- `.claude/skills/*/SKILL.md` — scan compiled skill summaries. Pick skills
  whose domain matches this story's work. A story about database migrations
  doesn't need the WebSocket skill.

Build a **context brief** — a focused summary of the selected items (not the
full files). Include:
- Key patterns or conventions from relevant learnings
- Architectural constraints from relevant decisions
- Domain knowledge from relevant skills

For each item included, note its age. If a file was last modified more than
2 days ago, prefix it with a staleness caveat:

> **[5 days ago]** This context may reference code or patterns that have since
> changed. Verify against current code before acting on it.

This prevents agents from confidently following outdated advice — a learning
that says "use pattern X in module Y" is dangerous if module Y was refactored
last week.

If nothing is relevant (first story, empty project), skip this step.

## Verification Discipline

Before claiming ANY outcome (story completed, tests passed, story blocked), you
MUST have concrete evidence:

1. **Identify** the verification command (test suite, lint, etc.)
2. **Run it** fresh — do not rely on a previous run's output
3. **Read the full output** — not just the exit code or summary line
4. **Confirm** the output supports your claim before making it

"I ran the tests and they passed" requires showing which command you ran and
its output. "The implementation is correct" requires citing the test results
that prove it. Claims without evidence are not claims — they are guesses.

**Step 5 — Implement each story**

Process stories wave by wave. Within each wave, launch independent stories in
parallel using concurrent Agent calls. Between waves, wait for all stories in
the current wave to complete before starting the next.

**For each wave**, launch all stories in the wave simultaneously. For each
story in the wave, follow this sequence:

1. **Check for blockers**: If the story is "blocked", stop — do not attempt blocked stories. Tell the user which story is blocked and show the failure_log.

2. **Mark in-progress**: Run `mantle update-story-status --issue {N} --story {S} --status in-progress`

3. **Spawn a story-implementer agent**: Use the Agent tool with `subagent_type: "story-implementer"`. When a wave has multiple stories, launch all agents in the same message (concurrent tool calls). If the wave has 2+ stories, use `isolation: "worktree"` on each agent so they work on isolated copies of the repo without conflicting. Single-story waves don't need worktree isolation.

   Select the model based on story complexity:

   **Model selection:**
   - **`model: "opus"`** — Default. Use for most stories, especially those involving multiple files, cross-module integration, design judgment, or ambiguous requirements.
   - **`model: "sonnet"`** — Simple stories only: single file, clear spec, no design judgment, follows an obvious existing pattern (e.g., "add CLI flag mirroring existing one", "add test cases for existing function").

   When in doubt, use opus. Only downgrade to sonnet when the story is genuinely simple. Never use haiku for implementation.

   Provide the agent with:
   - The full story content (from the story file)
   - The issue context (from the issue file)
   - The system design (from `.mantle/system-design.md` if it exists)
   - The context brief from Step 4 (selected learnings, decisions, and skills relevant to this specific story)
   - Clear instruction: "Before starting, review your project memory for relevant patterns, conventions, or learnings from previous stories. Implement this story. Run tests after implementation and fix any failures. After completing, report any patterns you discovered, gotchas you encountered, or conventions you established that future stories should know about."
   - Status code instruction: "End your response with exactly one of these status codes on its own line:
     - `STATUS: DONE` — implementation complete, tests pass, no concerns.
     - `STATUS: DONE_WITH_CONCERNS` — implementation complete and tests pass, but you have doubts or caveats. List each concern.
     - `STATUS: NEEDS_CONTEXT` — you cannot proceed without additional information. Describe exactly what you need.
     - `STATUS: BLOCKED` — you hit an issue you cannot resolve. Describe the blocker in detail."

4. **Handle agent status**: Parse the status code from the agent's response and act accordingly:

   - **DONE**: Proceed to test verification (sub-step 5).
   - **DONE_WITH_CONCERNS**: Proceed to test verification (sub-step 5), but record the concerns. Include them in the story's commit message and in any extracted learnings (sub-step 9).
   - **NEEDS_CONTEXT**: Do NOT retry blindly. Read the agent's request, gather the missing context (from project files, the user, or other sources), then re-spawn the story-implementer agent with the original prompt PLUS the additional context. This counts as the first attempt, not a retry.
   - **BLOCKED**: Skip directly to marking the story blocked (sub-step 8, failure path). Do NOT retry — the agent already determined it cannot proceed. Retrying the same agent without changes is wasted effort.

5. **Verify tests**: After the agent completes with DONE or DONE_WITH_CONCERNS, run the project's test command to independently verify all tests pass. Check CLAUDE.md for the test command — common examples: `uv run pytest`, `npm test`, `cargo test`, `go test ./...`. If no test command is documented, ask the user.

6. **Retry on failure**: If tests fail, spawn one more story-implementer agent with the test error output:
   - "The previous implementation attempt failed tests. Here is the error output: {errors}. Read the existing code, diagnose the failure, fix the issues, and ensure all tests pass."
   - Include the same status code instruction from step 3.
   - Run tests again after the retry agent completes.

7. **Post-implementation review**: After tests pass, spawn a single review agent before committing. Use `subagent_type: "code-reviewer"` with `model: "sonnet"`.

   > Review the implementation of story {S} against both its specification and
   > the project's coding standards.
   >
   > **Story spec:** {full story content}
   > **Files changed:** {list of files the implementer touched}
   > **Project coding standards:** {from CLAUDE.md}
   >
   > **Part 1 — Spec compliance:**
   > - Does the implementation deliver exactly what the story specifies? Nothing more, nothing less.
   > - Are all test cases from the story spec covered?
   > - Does it match the approach described in the story?
   >
   > **Part 2 — Code quality:**
   > - Does the code follow the project's coding standards?
   > - Are there unnecessary abstractions, dead code, or over-engineering?
   > - Is test quality adequate — do tests verify behaviour, not implementation?
   > - Are there obvious bugs, edge cases, or error handling gaps?
   >
   > Report one of:
   > - `REVIEW: PASS` — spec compliance and code quality are both acceptable
   > - `REVIEW: ISSUES` — list each issue with category (spec/quality), file path, and description

   **Handling review results:**
   - **Pass**: Proceed to commit (sub-step 8).
   - **Issues found**: Spawn one more story-implementer agent with the review feedback: "The implementation passed tests but a code review found issues. Fix these: {issues}. Do not change any behaviour — only address the review feedback." Run tests again after fixes. Do NOT re-run the review — one round of feedback is enough.

8. **Handle outcome**:
   - **Tests pass (and review passed or issues fixed)**: Create an atomic git commit with message `feat(issue-{N}): {story title}`, then run `mantle update-story-status --issue {N} --story {S} --status completed`. If the agent reported DONE_WITH_CONCERNS, append the concerns to the commit body.
   - **Tests fail after retry**: Run `mantle update-story-status --issue {N} --story {S} --status blocked --failure-log "{error summary}"` and stop the loop (do not continue to the next story)

9. **Extract learnings**: After a story completes successfully, check whether
   the agent reported any patterns, gotchas, or conventions. If so, save them:

   ```bash
   mantle save-learning \
     --issue {N} \
     --title "story-{S}: {brief topic}" \
     --confidence-delta "+0" \
     --content "<structured learnings>" \
     --overwrite
   ```

   Keep extracted learnings concise (under 100 words). Focus on what would
   change how a future story is implemented — not a summary of what was built.
   Skip this step if the agent reported nothing noteworthy.

**Wave completion:** After all stories in a wave finish (sub-steps 1-9 for
each), check outcomes before proceeding to the next wave:

- If **any story in the wave is blocked**, stop the entire loop. Do not start
  the next wave.
- If **all stories completed**, proceed to the next wave.
- For worktree-based parallel stories: the Agent tool returns the worktree
  branch and path if changes were made. Merge each completed story's changes
  into the main branch before starting the next wave to ensure dependent
  stories see prior work.

**Step 6 — Report results**

After all stories are processed (or the loop stops), summarise:
- Stories completed this run
- Stories skipped (already completed)
- Stories blocked (if any) — show the failure_log

Then briefly assess before recommending next steps:

- Did all stories complete successfully?
- Were there blocked stories that need fixing?
- Was the implementation complex — lots of files touched, tricky logic, or workarounds?

**Valid next commands** (recommend the best fit, not all of them):

- `/mantle:verify` — default. Recommend when all stories completed successfully.
- `/mantle:simplify` — recommend when all stories completed but the implementation was complex and could benefit from a quality pass before verification.
- `/mantle:implement` — recommend when a blocked story was fixed and implementation should resume.

**Default:** `/mantle:verify` if all stories completed.

Present one clear recommendation with a reason, then mention alternatives briefly:

> **Recommended next step:** `/mantle:<command>` — [reason based on what you observed in this session]
>
> Other options: [brief list of alternatives with one-line descriptions]

---
description: Implement stories for a Mantle issue using dedicated story agents
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle update-story-status*), Bash(git add*), Bash(git commit*)
---

You are the implementation orchestrator for a Mantle project. You will implement stories for a given issue by spawning dedicated agents for each story.

## Dynamic Context

- **Current branch**: !`git branch --show-current`
- **Working tree status**: !`git status --short`
- **Recent commits**: !`git log --oneline -5`

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

Read all required context files:
- `.mantle/issues/issue-{NN}.md` — the issue specification
- `.mantle/system-design.md` — system architecture (if it exists)
- `.mantle/product-design.md` — product context (if it exists)
- `.mantle/stories/issue-{NN}-story-*.md` — all stories for this issue

For each story, note:
- Story number, title, current status (planned, in-progress, completed, blocked)

Determine the implementation order (ascending story number). Skip stories already marked "completed".

**Step 4 — Implement each story**

For each story that is not "completed", follow this sequence:

1. **Check for blockers**: If the story is "blocked", stop — do not attempt blocked stories. Tell the user which story is blocked and show the failure_log.

2. **Mark in-progress**: Run `mantle update-story-status --issue {N} --story {S} --status in-progress`

3. **Spawn a story-implementer agent**: Use the Agent tool with `subagent_type: "story-implementer"`. Provide the agent with:
   - The full story content (from the story file)
   - The issue context (from the issue file)
   - The system design (from `.mantle/system-design.md` if it exists)
   - Any learnings from `.mantle/learnings/` relevant to this issue
   - Clear instruction: "Implement this story. Run tests after implementation and fix any failures."

4. **Verify tests**: After the agent completes, run the project's test command to independently verify all tests pass. Check CLAUDE.md for the test command — common examples: `uv run pytest`, `npm test`, `cargo test`, `go test ./...`. If no test command is documented, ask the user.

5. **Retry on failure**: If tests fail, spawn one more story-implementer agent with the test error output:
   - "The previous implementation attempt failed tests. Here is the error output: {errors}. Read the existing code, diagnose the failure, fix the issues, and ensure all tests pass."
   - Run tests again after the retry agent completes.

6. **Handle outcome**:
   - **Tests pass**: Create an atomic git commit with message `feat(issue-{N}): {story title}`, then run `mantle update-story-status --issue {N} --story {S} --status completed`
   - **Tests fail after retry**: Run `mantle update-story-status --issue {N} --story {S} --status blocked --failure-log "{error summary}"` and stop the loop (do not continue to the next story)

**Step 5 — Report results**

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

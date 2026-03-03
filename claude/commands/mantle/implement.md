You are the implementation orchestrator for a Mantle project. You will implement stories for a given issue by spawning Agent subagents for each story.

**Step 1 — Check prerequisites**

Read `.mantle/state.md` and verify:
- `.mantle/` exists (if not, tell the user to run `mantle init`)
- Status is `planning` or `implementing` (valid states for implementation)
- If status is earlier, tell the user the current status and suggest the appropriate next command

**Step 2 — Select issue**

Ask the user which issue to implement. Read `.mantle/issues/` to show available issues.
If the user provided an issue number with the command, use that.

Display:
> **Issue {NN}**: {title}
> **Stories**: {story_count} planned
> **Status**: {issue status}

Confirm with the user before proceeding.

**Step 3 — Load stories**

Read all story files from `.mantle/stories/issue-{NN}-story-*.md` for the selected issue.

For each story, note:
- Story number
- Title
- Current status (planned, in-progress, completed, blocked)

Determine the implementation order (ascending story number). Skip stories already marked "completed".

**Step 4 — Implement each story**

For each story that is not "completed", follow this sequence:

1. **Mark in-progress**: Run `mantle update-story-status --issue {N} --story {S} --status in-progress`

2. **Spawn an Agent**: Use the Agent tool (subagent_type: "smart") to implement the story. Provide the agent with:
   - The full story content (from the story file)
   - The issue context (from the issue file)
   - The system design (from `.mantle/system-design.md` if it exists)
   - Clear instruction: "Implement this story. Follow all project conventions from CLAUDE.md. Run tests after implementation and fix any failures."

3. **Verify tests**: After the agent completes, run `uv run pytest` to verify all tests pass.

4. **Retry on failure**: If tests fail, spawn one more Agent with the test error output included:
   - "The previous implementation failed tests. Here is the error output: {errors}. Please read the existing code, diagnose the failure, fix the issues, and ensure all tests pass."
   - Run tests again after the retry agent completes.

5. **Handle outcome**:
   - **Tests pass**: Create an atomic git commit with message `feat(issue-{N}): {story title}`, then run `mantle update-story-status --issue {N} --story {S} --status completed`
   - **Tests fail after retry**: Run `mantle update-story-status --issue {N} --story {S} --status blocked --failure-log "{error summary}"` and stop the loop (do not continue to the next story)

6. **If the story was already "blocked"**: Stop — do not attempt blocked stories. Tell the user which story is blocked and show the failure_log.

**Step 5 — Report results**

After all stories are processed (or the loop stops), summarise:
- Stories completed this run
- Stories skipped (already completed)
- Stories blocked (if any) — show the failure_log
- Next steps: fix the blocked story and re-run `/mantle:implement`, or proceed to `/mantle:verify` if all stories are done

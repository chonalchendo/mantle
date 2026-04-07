---
issue: 40
title: Prompt updates — review.md save + fix.md command
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a developer whose code was flagged in review, I want an automated fix command that reads review feedback, spawns agents to fix issues, and re-verifies — so I don't manually orchestrate each step.

## Depends On

Story 1 — uses the save-review-result and load-review-result CLI commands created in story 1.

## Approach

Update the review.md prompt to save structured review results when needs-changes items are flagged. Create a new fix.md prompt file that reads saved review feedback, spawns implementation agents per flagged criterion, transitions issue status, and re-runs verification. This follows the prompt-orchestrates-AI-implements pattern from implement.md.

## Implementation

### claude/commands/mantle/review.md (modify)

Update Step 6 "needs changes" path (around line 139-153). After transitioning the issue back to implementing, add a call to save the review result:

Before the "Fix the flagged items" message, add:

```
Save the review feedback for automated consumption:
\`\`\`bash
mantle save-review-result --issue <N> --feedback "criterion 1|needs-changes|user comment" --feedback "criterion 2|approved|"
\`\`\`
Include ALL criteria (both approved and needs-changes) so the fix command has full context.
```

Also update the suggestion text at the end to mention /mantle:fix as an option:
> Fix the flagged items manually, or run `/mantle:fix` to have AI fix them automatically.
> Then re-run `/mantle:verify` followed by `/mantle:review`.

### claude/commands/mantle/fix.md (new file)

Create a new prompt file with this structure:

**Frontmatter:**
- argument-hint: [issue-number]
- allowed-tools: Read, Edit, Write, Bash(mantle *), Bash(uv run pytest*), Bash(git *)

**Purpose:** Read saved review feedback, spawn agents to fix flagged criteria, re-verify.

**Steps:**

1. **Check prerequisites** — read state.md, verify status is planning or implementing
2. **Select issue** — use $ARGUMENTS or ask. Read issue file, confirm status.
3. **Load review feedback** — run `mantle load-review-result --issue N`, parse the output to identify needs-changes criteria with comments
4. **Transition to implementing** — run `mantle transition-issue-implementing --issue N`
5. **Fix flagged criteria** — for each needs-changes criterion:
   - Read the relevant source files (use `mantle collect-issue-files --issue N` for context)
   - Make the fix directly (this is a focused fix, not a full story implementation)
   - Run tests after each fix to verify no regressions
6. **Commit fixes** — stage and commit all fixes with message "fix(issue-N): address review feedback"
7. **Transition to implemented** — run `mantle transition-issue-implemented --issue N`
8. **Re-verify** — run verification inline:
   - Read .mantle/config.md for verification strategy
   - Execute the strategy (run tests, lint, type checks)
   - Check each acceptance criterion
   - If all pass, transition to verified via `mantle transition-issue-verified --issue N`
   - Report results
9. **Summary** — report what was fixed, verification result, and recommend `/mantle:review` if verification passed

Key design decisions for fix.md:
- Fixes are applied directly by the orchestrating agent (no subagent spawn needed — these are targeted fixes, not full story implementations)
- One commit for all fixes (atomic — either all review feedback is addressed or none)
- Re-verification is inline (not a separate command invocation) to keep the loop tight
- The command reads saved review results, not conversation history — making it resumable across sessions

#### Design decisions

- **Direct fix, not subagent**: Review fixes are targeted corrections (not greenfield implementation), so the orchestrating agent handles them directly. This avoids the overhead of agent spawn for what are typically small, focused changes.
- **Single atomic commit**: All review feedback fixes go in one commit. This makes the fix reviewable as a unit and easy to revert if needed.
- **Inline re-verify**: Re-running verification within fix.md avoids requiring the user to run a separate command. The fix → verify loop is the core value proposition.

## Tests

No new test files needed — this story is prompt-only (claude-code slice). The core/CLI functionality is tested in story 1. The prompts are validated by running the pipeline end-to-end during verification (Step 8 of the build pipeline).
---
argument-hint: [issue-number]
allowed-tools: Read, Edit, Write, Bash(mantle *), Bash(uv run pytest*), Bash(just *), Bash(git add*), Bash(git commit*)
---

Read saved review feedback, fix flagged criteria, and re-verify. This command
automates the fix-and-verify loop after `/mantle:review` flags issues.

## Dynamic Context

- **Current branch**: !`git branch --show-current`
- **Working tree status**: !`git status --short`
- **Recent commits**: !`git log --oneline -5`

## Iron Laws

These rules are absolute. There are no exceptions.

1. **NO fix WITHOUT saved review feedback.** If `mantle load-review-result` returns nothing, stop and tell the user to run `/mantle:review` first.
2. **NO skipping criteria.** Every needs-changes criterion gets fixed. Every single one.
3. **NO commit WITHOUT passing tests.** Tests must pass after all fixes before committing.
4. **NO claiming fixed WITHOUT evidence.** Each fix must be verified by running tests or reading the corrected code.

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Check prerequisites"
2. "Step 2 — Select issue"
3. "Step 3 — Load review feedback"
4. "Step 4 — Transition to implementing"
5. "Step 5 — Fix flagged criteria"
6. "Step 6 — Commit fixes"
7. "Step 7 — Transition to implemented"
8. "Step 8 — Re-verify"
9. "Step 9 — Summary"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

## Step 1 — Check prerequisites

Read `.mantle/state.md` and verify:
- `.mantle/` exists (if not, tell the user to run `mantle init`)
- Status is `planning` or `implementing` (valid states for fixing)
- If status is earlier, tell the user the current status and suggest the
  appropriate next command

## Step 2 — Select issue

If the user provided `$ARGUMENTS`, use that as the issue number.
Otherwise, read `.mantle/issues/` to show available issues and ask the user
which issue to fix. Prefer issues with `implementing` status.

Display:
> **Issue {NN}**: {title}
> **Status**: {status}

Read the issue file to confirm the status and extract context.

## Step 3 — Load review feedback

Run:
```bash
mantle load-review-result --issue <N>
```

Parse the output to identify:
- Criteria with `needs-changes` status and their comments
- Criteria with `approved` status (for reference)

If no review result exists, stop and tell the user:
> No saved review feedback found for issue {N}. Run `/mantle:review` first
> to generate structured feedback, then re-run `/mantle:fix`.

Display the feedback summary:
> **Review feedback for issue {N}:**
>
> | # | Criterion | Status | Comment |
> |---|-----------|--------|---------|
> | 1 | {criterion} | needs-changes | {comment} |
> | 2 | {criterion} | approved | |
>
> **{count} criterion/criteria need fixes.**

## Step 4 — Transition to implementing

Transition the issue to implementing (idempotent — safe if already
implementing):

```bash
mantle transition-issue-implementing --issue <N>
```

## Step 5 — Fix flagged criteria

Gather context for the fixes:
```bash
mantle collect-issue-files --issue <N>
```

Read the relevant source files to understand the current implementation.

For each needs-changes criterion, apply a targeted fix:

1. Read the reviewer's comment to understand what needs to change
2. Read the relevant source files
3. Make the fix directly — this is a focused correction, not a full
   reimplementation
4. Run tests after each fix to verify no regressions:
   ```bash
   uv run pytest
   ```

If tests fail after a fix, diagnose and correct before moving to the next
criterion.

## Step 6 — Commit fixes

After all fixes are applied and tests pass, create an atomic commit:

```bash
git add <fixed-files>
git commit -m "fix(issue-<N>): address review feedback"
```

Stage only the files that were actually changed. Do not use `git add -A`.

## Step 7 — Transition to implemented

```bash
mantle transition-issue-implemented --issue <N>
```

## Step 8 — Re-verify

Run verification inline to keep the feedback loop tight.

1. Read `.mantle/config.md` for the verification strategy (look for the
   `verification_strategy` field in frontmatter).
2. Execute the strategy — run tests, lint, and type checks as configured:
   ```bash
   uv run pytest
   just check
   ```
3. Check each acceptance criterion from the issue file against the current
   implementation.
4. If all criteria pass, transition to verified:
   ```bash
   mantle transition-issue-verified --issue <N>
   ```
5. If any criteria fail, report which ones failed and stop. Do NOT transition.

## Step 9 — Summary

Report the outcome:

> ## Fix Summary — Issue {N}
>
> **Criteria fixed:** {list of fixed criteria}
> **Verification:** {PASSED | FAILED}
>
> {If PASSED:}
> All fixes verified. Issue {N} is now verified.
>
> **Recommended next step:** `/mantle:review` — run a follow-up review to
> confirm the fixes meet quality standards.
>
> {If FAILED:}
> {count} criterion/criteria failed re-verification. Review the failures
> above and fix manually, then re-run `/mantle:verify`.

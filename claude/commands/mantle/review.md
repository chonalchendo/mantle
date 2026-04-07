---
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle *)
---

Perform a checklist-based human review of acceptance criteria, using pass/fail
results from the most recent `/mantle:verify` run as a starting point. Present
each criterion, share the verification result, and let the human make the final
call.

## Scope

**review checks architectural quality** — does the implementation follow
project conventions, design principles, and structural patterns?

review is the authoritative quality gate. `/mantle:verify` checks functional
correctness against acceptance criteria; review checks everything else:

- **Convention adherence**: import style, docstring format, line length, type
  hints, naming — the rules in CLAUDE.md
- **Architectural consistency**: layer boundaries, module responsibilities,
  patterns established in system-design.md
- **Code quality patterns**: unnecessary abstractions, premature complexity,
  clarity and readability

When reviewing, look beyond "does it pass the criteria" to "does it belong in
this codebase."

## Dynamic Context

- **Current branch**: !`git branch --show-current`
- **Working tree status**: !`git status --short`
- **Recent commits**: !`git log --oneline -5`

Be clear, structured, and deferential to the human's judgement.

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Check prerequisites"
2. "Step 2 — Select issue"
3. "Step 3 — Load verification results"
4. "Step 4 — Present review checklist"
5. "Step 5 — Collect feedback"
6. "Step 6 — Handle outcome"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

## Step 1 — Check prerequisites

Check whether `.mantle/`, `.mantle/state.md` exist by reading them.

- If `.mantle/` does not exist, tell them to run `mantle init` first.
- Read `state.md` and verify the project exists. If the project is in an early
  phase (before implementing), tell the user the current status and what step
  to run next.

## Step 2 — Select issue

If the user provided `$ARGUMENTS`, use that as the issue number.
Otherwise, read `.mantle/issues/` to show available issues and ask the user
which issue to review. Prefer issues with `verified` status.

Display:
> **Issue {NN}**: {title}
> **Status**: {status}

Confirm with the user before proceeding.

## Step 3 — Load verification results

Read the issue file (`.mantle/issues/issue-{NN}.md`). Extract:

1. **Status** — confirm it is `verified` (or at least `implemented`). If the
   issue has not been verified yet, recommend running `/mantle:verify` first.
2. **Acceptance criteria** — from the issue body (typically under
   "## Acceptance Criteria" or as a checklist).
3. **Verification pass/fail** — if the issue status is `verified`, all criteria
   passed verification. Note this for each criterion.

## Step 4 — Present review checklist

Display each acceptance criterion with its verification result:

> ## Review Checklist — Issue {NN}
>
> **{issue title}**
>
> | # | Criterion | Verification | Review |
> |---|-----------|-------------|--------|
> | 1 | {criterion} | Pass | Pending |
> | 2 | {criterion} | Pass | Pending |

Then use AskUserQuestion to let the user choose:
- **Approve all** — approve every criterion in one go
- **Discuss** — go through each criterion one at a time

**If the user picks "Approve all":** skip Step 5 and go straight to
Step 6 with all criteria marked as approved.

**If the user picks "Discuss":** proceed to Step 5.

## Step 5 — Collect feedback (discuss mode)

For each criterion, present it and use AskUserQuestion for each criterion:
- **Approve** — this criterion is met
- **Needs changes** — ask what should change

> **Criterion {N}**: {criterion text}
> **Verification result**: Pass/Fail

Keep it brief — don't re-explain the options each time. If the user picks
"Needs changes", ask what should change. Record the response and move to the
next criterion.

## Step 6 — Handle outcome

**If all criteria are approved:**
1. Transition the issue to approved:
   ```bash
   mantle transition-issue-approved --issue <N>
   ```
2. Save the review feedback for the structured record:
   ```bash
   mantle save-review-result --issue <N> --feedback "criterion 1|approved|" --feedback "criterion 2|approved|"
   ```
   Include ALL criteria as approved.
3. Check `.mantle/learnings/` for whether a retrospective already exists for this issue.
4. Check `.mantle/issues/` for remaining unimplemented issues.

   **Valid next commands** (recommend the best fit, not all of them):
   - `/mantle:retrospective` — **always recommend first** if no learning exists for this issue. Retrospectives capture what went well and what was harder than expected, directly improving future planning.
   - `/mantle:shape-issue` — recommend after retrospective, when more unimplemented issues remain.
   - `/mantle:plan-issues` — recommend when all current issues are done but the project needs more work.

   **Default:** `/mantle:retrospective` — always do this before moving on.

   Present one clear recommendation:

   > **Recommended next step:** `/mantle:retrospective` — capture learnings from this issue before moving on. This takes 5 minutes and directly improves future planning.
   >
   > After that: `/mantle:shape-issue` to pick up the next issue (or `/mantle:plan-issues` if all current issues are done).

**If any criteria need changes:**
1. Transition the issue back to implementing:
   ```bash
   mantle transition-issue-implementing --issue <N>
   ```
2. Save the review feedback for automated consumption:
   ```bash
   mantle save-review-result --issue <N> --feedback "criterion 1|needs-changes|user comment" --feedback "criterion 2|approved|"
   ```
   Include ALL criteria (both approved and needs-changes) so the fix command has full context.
3. List the criteria that need changes with the user's comments.
4. Tell the user:
   > {count} criterion/criteria need changes. Issue {N} has been moved back
   > to implementing.
   >
   > **Items needing changes:**
   > - Criterion {N}: {user's comment}
   >
   > Fix the flagged items manually, or run `/mantle:fix` to have AI fix them automatically.
   > Then re-run `/mantle:verify` followed by `/mantle:review`.

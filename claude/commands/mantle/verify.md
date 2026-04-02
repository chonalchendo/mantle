---
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle *), Bash(uv run pytest*), Bash(npm test*), Bash(cargo test*), Bash(go test*)
---

Verify that an implemented issue meets its acceptance criteria using the project's
verification strategy.

## Dynamic Context

- **Current branch**: !`git branch --show-current`
- **Working tree status**: !`git status --short`
- **Recent commits**: !`git log --oneline -5`

Be methodical, precise, and honest. Verify systematically, report clearly, and
only sign off when every criterion passes. If something fails, say so clearly.

## Iron Laws

These rules are absolute. There are no exceptions.

1. **NO pass WITHOUT evidence.** Every "Pass" verdict must cite the specific test result, code location, or command output that proves it. "It looks correct" is not evidence.
2. **NO skipping criteria.** Every acceptance criterion gets checked. Every single one.
3. **NO partial pass.** A criterion either fully passes or it fails. "Mostly works" is a fail.
4. **NO transition WITHOUT all criteria passing.** If any criterion fails, the issue stays in its current state.

### Red Flags — thoughts that mean STOP

| Thought | Reality |
|---------|---------|
| "This criterion is obviously met, no need to check" | Check it anyway. Obvious things fail surprisingly often. |
| "The tests pass, so all criteria must be met" | Tests and acceptance criteria are different things. Verify each criterion independently. |
| "This is a minor criterion, I'll mark it pass" | Minor criteria fail builds. Check it properly. |
| "I already verified this in a previous step" | Verify it again now. State may have changed. |
| "The implementation looks correct from reading the code" | Run the verification command. Reading is not verifying. |

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Check prerequisites"
2. "Step 2 — Select issue"
3. "Step 3 — Load verification strategy"
4. "Step 4 — Check for per-issue override"
5. "Step 5 — Load acceptance criteria"
6. "Step 6 — Execute verification"
7. "Step 7 — Report results"
8. "Step 8 — Handle outcome"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

## Step 1 — Check prerequisites

Check whether `.mantle/`, `.mantle/state.md` exist by reading them.

- If `.mantle/` does not exist, tell them to run `mantle init` first.
- Read `state.md` and verify status is `implementing` or later. If the project
  is in an earlier phase, tell the user the current status and what step to run
  next.

## Step 2 — Select issue

If the user provided `$ARGUMENTS`, use that as the issue number.
Otherwise, read `.mantle/issues/` to show available issues and ask the user
which issue to verify. Prefer issues with `implementing` or `implemented` status.

Display:
> **Issue {NN}**: {title}
> **Status**: {status}

Confirm with the user before proceeding.

## Step 3 — Load verification strategy

Read `.mantle/config.md` directly and look for the `verification_strategy` field
in frontmatter.

**If no strategy is found (first-use flow):**
1. Tell the user no verification strategy is configured yet.
2. Explain that the strategy defines how acceptance criteria are checked (e.g.
   "run pytest and check coverage", "manual walkthrough of each criterion",
   "run the test suite then smoke-test the CLI").
3. Ask the user to describe their preferred verification strategy.
4. Once they provide it, persist via:
   ```bash
   mantle save-verification-strategy --strategy "<their strategy text>"
   ```
5. Confirm it was saved and continue.

**If a strategy is found**, display it and continue.

## Step 4 — Check for per-issue override

Read the issue file (`.mantle/issues/issue-{NN}.md`). Check if the `verification`
field is set in frontmatter.

- If set, use that instead of the project default. Tell the user:
  > Using per-issue verification override: {override text}
- If not set, use the project-wide strategy from Step 3.

## Step 5 — Load acceptance criteria

Extract the acceptance criteria from the issue file body. These are typically
in a section like "## Acceptance Criteria" or as a checklist in the issue body.

Display them:
> **Acceptance Criteria:**
> 1. {criterion 1}
> 2. {criterion 2}
> ...

## Verification Discipline

Before recording ANY criterion as "Pass", you MUST have concrete evidence:

1. **Identify** the verification action (run a command, read specific code, check a file)
2. **Execute it** fresh — do not rely on a previous step's output
3. **Read the full output** — not just the summary or exit code
4. **Cite the evidence** in the "Detail" column of the results table

A "Pass" without cited evidence is a guess, not a verification result. If you
cannot produce evidence for a criterion, it is a "Fail" with detail "Unable to
verify — no evidence found."

## Step 6 — Execute verification

Follow the loaded strategy to verify each acceptance criterion. This may involve:
- Running tests (`uv run pytest`, etc.)
- Reading implementation code to confirm behaviour
- Checking that files exist or contain expected content
- Running CLI commands to verify functionality

For each criterion, record:
- **Pass** or **Fail**
- Brief detail explaining the result

## Step 7 — Report results

Display a formatted verification report:

> ## Verification Report — Issue {NN}
>
> **{issue title}**
> **Strategy:** {project default | per-issue override}
>
> | # | Criterion | Result | Detail |
> |---|-----------|--------|--------|
> | 1 | {criterion} | Pass/Fail | {detail} |
> | 2 | ... | ... | ... |
>
> **Overall: {PASSED | FAILED}**

## Step 8 — Handle outcome

**If all criteria pass:**
1. Transition the issue to verified:
   ```bash
   mantle transition-issue-verified --issue <N>
   ```
2. Briefly assess before recommending next steps:
   - Was the implementation straightforward, or did verification reveal complexity?
   - Did you notice code that could benefit from simplification?

   **Valid next commands** (recommend the best fit, not all of them):
   - `/mantle:review` — default. Recommend in most cases for checklist-based human review.
   - `/mantle:simplify` — recommend when verification passed but you noticed code complexity, unnecessary abstractions, or bloat that should be addressed before review.

   **Default:** `/mantle:review` if nothing suggests otherwise.

   Present one clear recommendation:

   > **Recommended next step:** `/mantle:<command>` — [reason based on what you observed]
   >
   > Other options: [brief alternatives]

**If any criteria fail:**
1. List the failing criteria with details.
2. Suggest specific fixes for each failure.
3. Do NOT transition the issue status.
4. Tell the user:
   > {count} criterion/criteria failed. Fix the issues above and re-run
   > `/mantle:verify` to try again.

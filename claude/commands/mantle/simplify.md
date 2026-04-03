---
description: Use after implementation when AI-generated code needs bloat removal and quality cleanup
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle collect-*), Bash(uv run pytest*), Bash(npm test*), Bash(cargo test*), Bash(go test*), Bash(git add*), Bash(git commit*), Bash(git diff*), Bash(git stash*), Bash(git log*)
---

Identify and remove characteristic AI-generated code bloat while preserving all functionality.

## Iron Laws

These rules are absolute. There are no exceptions, no "just this once", no edge cases.

1. **NO behaviour changes.** Simplification changes HOW code works, never WHAT it does. If you're unsure whether a change alters behaviour, don't make it.
2. **NO claiming "nothing to simplify" without reviewing.** Every file in scope gets read and evaluated against the bloat checklist. "It looks fine" after a glance is not a review.
3. **NO committing without passing tests.** If tests fail after simplification, all changes are reverted. No exceptions, no "the failure is unrelated."
4. **NO removing code you haven't traced.** Before deleting a function or import, confirm it's unused — grep for callers, check re-exports, verify test references.

### Red Flags — thoughts that mean STOP

If you catch yourself thinking any of these, you are about to violate an Iron Law:

| Thought | Reality |
|---------|---------|
| "This function is probably unused, I'll remove it" | Grep for it first. "Probably" is not "confirmed." |
| "These tests are testing implementation details, I'll simplify them" | Simplify production code, not test assertions. Tests are the safety net. |
| "This abstraction is unnecessary but it's tested, so I'll leave it" | If it's unnecessary, remove it and update the tests. That's what simplification is. |
| "The test failure is from something else, not my changes" | Revert and investigate. You don't know that until you prove it. |
| "This file is small, no need to review it" | Small files can have bloat too. Every file gets the checklist. |

## Dynamic Context

- **Current branch**: !`git branch --show-current`
- **Working tree status**: !`git status --short`

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Check prerequisites"
2. "Step 2 — Determine scope"
3. "Step 3 — Run tests (baseline)"
4. "Step 4 — Simplify each file"
5. "Step 5 — Run tests (verification)"
6. "Step 6 — Commit and report"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

**Step 1 — Check prerequisites**

Read `.mantle/state.md` and verify:
- `.mantle/` exists (if not, tell the user to run `mantle init`)

If the working tree is dirty (from the dynamic context above) and in issue-scoped mode (arguments provided), warn the user and ask whether to proceed or commit/stash first.

**Step 2 — Determine scope**

If the user provided `$ARGUMENTS`, use that as the issue number (issue-scoped mode):
- Run `mantle collect-issue-files --issue {N}` to get the file list
- Display: "Simplifying {count} files from issue {N}"

If no arguments were provided (standalone mode):
- Run `mantle collect-changed-files` to get the file list
- Display: "Simplifying {count} changed files"

If no files are found, report "Nothing to simplify" and exit.

**Step 3 — Run tests (baseline)**

Read `CLAUDE.md` to detect the project's test command. Look for "Run tests:" or common patterns like `uv run pytest`, `npm test`, `cargo test`, `go test ./...`.

Run the test suite and record pass/fail as baseline.

If tests already fail, warn the user: "Tests are failing before simplification — proceed with caution (no test safety net)."

**Step 4 — Simplify each file**

For each file in the list:
- Skip non-code files (images, configs, lockfiles, `.md` files in `.mantle/`)
- Spawn an Agent (`subagent_type: "implementer"`) with this prompt:

> You are a code simplification specialist. Review the following file and simplify it.
>
> **Rules:**
> - NEVER change what the code does — only how it does it
> - Follow the project's coding standards from CLAUDE.md
> - Apply the LLM Bloat Pattern Checklist below
> - Prefer clarity over brevity — explicit is better than clever
> - Do NOT remove functions unless you are certain they are unused within this file
> - Do NOT change public interfaces (function signatures, class APIs, exports)
>
> **LLM Bloat Pattern Checklist:**
> 1. Unnecessary abstractions — helper functions/classes for one-time operations
> 2. Defensive over-engineering — excessive try-catch, redundant validation of internal data
> 3. Code duplication — repeated logic within a file
> 4. Unnecessary conditionals — redundant else blocks, conditions that can't fail
> 5. Dead code — unused imports, variables, unreachable branches
> 6. Comment noise — comments restating what code already says
> 7. Slop scaffolding — boilerplate wrapping trivial logic
> 8. Over-parameterisation — configuration for things that never vary
>
> **File to simplify:** {file_path}
>
> Read the file, apply simplifications, and edit the file directly. If no simplifications are needed, make no changes.

**Step 5 — Run tests (verification)**

Run the same test command from Step 3.

- If tests pass: proceed to commit.
- If tests fail: run `git checkout -- .` to revert all simplification changes, report which files were being simplified, and suggest the user review manually.

**Step 6 — Commit and report**

If in issue-scoped mode: `git add` changed files, commit as `refactor(issue-{N}): simplify implementation`.

If in standalone mode: `git add` changed files, commit as `refactor: simplify code`.

Display summary:
- **Files reviewed**: {count}
- **Files simplified**: {count with actual changes}
- **Files unchanged**: {count}
- **Tests**: pass/fail
- **Next**: suggest `/mantle:verify {N}` if issue-scoped

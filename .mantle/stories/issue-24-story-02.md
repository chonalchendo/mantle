---
issue: 24
title: Claude Code simplify command — orchestrator prompt
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want to run /mantle:simplify after implementation to have AI agents review and clean up each changed file, so that characteristic LLM bloat is removed before verification.

## Approach

Follows the implement.md orchestrator pattern — a static Claude Code command (markdown prompt) that spawns per-file agents. No new core logic needed beyond story 1's utilities. The command calls `mantle collect-issue-files` or `mantle collect-changed-files` via Bash, then spawns an agent per file with the bloat checklist. Tests run before and after. This is the user-facing story that ties everything together.

## Implementation

### claude/commands/mantle/simplify.md (new file)

Frontmatter:
```yaml
---
description: Simplify AI-generated code by removing bloat patterns
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle collect-*), Bash(uv run pytest*), Bash(npm test*), Bash(cargo test*), Bash(go test*), Bash(git add*), Bash(git commit*), Bash(git diff*), Bash(git stash*), Bash(git log*)
---
```

Prompt structure (step-by-step orchestrator):

**Step 1 — Check prerequisites**
- Read `.mantle/state.md` — verify `.mantle/` exists
- Dynamic context: `!git branch --show-current`, `!git status --short`
- If working tree is dirty and in issue-scoped mode, warn user

**Step 2 — Determine scope**
- If `$ARGUMENTS` provided: issue-scoped mode
  - Run `mantle collect-issue-files --issue {N}` to get file list
  - Display: "Simplifying {count} files from issue {N}"
- If no arguments: standalone mode
  - Run `mantle collect-changed-files` to get file list
  - Display: "Simplifying {count} changed files"
- If no files found, report "Nothing to simplify" and exit

**Step 3 — Run tests (baseline)**
- Detect test command from CLAUDE.md (look for "Run tests:" or common patterns)
- Run the test suite and record pass/fail as baseline
- If tests already fail, warn user: "Tests are failing before simplification — proceed with caution (no test safety net)"

**Step 4 — Simplify each file**
- For each file in the list:
  - Skip non-code files (images, configs, lockfiles, .md files in .mantle/)
  - Spawn an Agent (subagent_type: "implementer") with prompt:
    ```
    You are a code simplification specialist. Review the following file and simplify it.

    **Rules:**
    - NEVER change what the code does — only how it does it
    - Follow the project's coding standards from CLAUDE.md
    - Apply the LLM Bloat Pattern Checklist below
    - Prefer clarity over brevity — explicit is better than clever
    - Do NOT remove functions unless you are certain they are unused within this file
    - Do NOT change public interfaces (function signatures, class APIs, exports)

    **LLM Bloat Pattern Checklist:**
    1. Unnecessary abstractions — helper functions/classes for one-time operations
    2. Defensive over-engineering — excessive try-catch, redundant validation of internal data
    3. Code duplication — repeated logic within a file
    4. Unnecessary conditionals — redundant else blocks, conditions that can't fail
    5. Dead code — unused imports, variables, unreachable branches
    6. Comment noise — comments restating what code already says
    7. Slop scaffolding — boilerplate wrapping trivial logic
    8. Over-parameterisation — configuration for things that never vary

    **File to simplify:** {file_path}
    Read the file, apply simplifications, and edit the file directly. If no simplifications are needed, make no changes.
    ```

**Step 5 — Run tests (verification)**
- Run the same test command from Step 3
- If tests pass: proceed to commit
- If tests fail: run `git stash` to revert all simplification changes, report which files were being simplified, and suggest the user review manually

**Step 6 — Commit and report**
- If in issue-scoped mode: `git add` changed files, commit as `refactor(issue-{N}): simplify implementation`
- If in standalone mode: `git add` changed files, commit as `refactor: simplify code`
- Display summary:
  - Files reviewed: {count}
  - Files simplified: {count with actual changes}
  - Files unchanged: {count}
  - Tests: pass/fail
  - Next: suggest `/mantle:verify {N}` if issue-scoped

## Tests

No pytest tests for this story — it is a static markdown command file (prompt-only orchestration, same as implement.md). Verification is manual: install the command and run it.
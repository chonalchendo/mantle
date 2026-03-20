---
issue: 15
title: CLI wiring + verify.md command — first-use flow, verification execution, status
  transition
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want to run `/mantle:verify` and have it load my verification strategy (prompting me to define one on first use), execute verification steps against acceptance criteria, and transition the issue to "verified" on success, so that I can confirm my implementation meets requirements.

## Approach

Follows the CLI wiring pattern of `cli/shaping.py` — thin `run_*()` functions wrapping core calls. The `verify.md` command file follows the pattern of `shape-issue.md` and `implement.md` — a static prompt that guides the AI through the verification workflow step by step. The command invokes CLI commands via Bash for state mutations (saving strategy, transitioning issue status). Builds on story 1's core functions.

## Implementation

### src/mantle/cli/verify.py (new file)

- **`run_save_verification_strategy(*, strategy: str, project_dir: Path | None = None) -> None`** — wraps `verify.save_strategy()`. Defaults `project_dir` to `Path.cwd()`. Prints confirmation via Rich console.
- **`run_transition_to_verified(*, issue: int, project_dir: Path | None = None) -> None`** — wraps `issues.transition_to_verified()`. Catches `InvalidTransitionError` and prints user-friendly error. Prints confirmation on success.

### src/mantle/cli/main.py (modify)

- Import `verify` in the cli imports block
- Add `@app.command(name="save-verification-strategy")` wired to `verify.run_save_verification_strategy()`
- Add `@app.command(name="transition-issue-verified")` wired to `verify.run_transition_to_verified()`

### claude/commands/mantle/verify.md (new file)

Static command file with these steps:
1. **Prerequisites** — read `.mantle/state.md`, verify project is in `implementing` or later
2. **Select issue** — ask user which issue to verify (or use argument)
3. **Load strategy** — read config.md directly for verification_strategy. If no strategy found, enter first-use flow: prompt user to define their verification strategy, then persist via `mantle save-verification-strategy --strategy "<strategy>"`
4. **Check per-issue override** — read the issue file, check if `verification` field is set. If so, use that instead of project default.
5. **Load acceptance criteria** — extract acceptance criteria from the issue file
6. **Execute verification** — follow the strategy to verify each acceptance criterion. Run tests, check outputs, etc. Record pass/fail for each criterion.
7. **Report** — display formatted report with pass/fail per criterion
8. **On all pass** — transition issue to verified via `mantle transition-issue-verified --issue <N>`, suggest running `/mantle:review`
9. **On any fail** — list failures, suggest fixes, do NOT transition status

### claude/commands/mantle/help.md (modify)

- Add `/mantle:verify` to the Verification & Review section (if not already present)

#### Design decisions

- **Strategy loading in command, not CLI**: The command reads config.md and issue files directly (AI can read files). The CLI command `save-verification-strategy` is only needed for persistence. This keeps CLI thin.
- **First-use flow in command prompt**: Prompting the user is naturally done by the AI in the command, not by Python code.
- **Separate transition command**: `transition-issue-verified` is its own CLI command so the verify.md prompt can call it after confirming all criteria pass. Clean separation of concerns.

## Tests

### tests/cli/test_verify.py (new file)

- **test_save_verification_strategy_cli**: Subprocess call to `mantle save-verification-strategy --strategy "run pytest"`, verify config.md updated
- **test_transition_issue_verified_cli**: Set up issue with `implemented` status, subprocess call to `mantle transition-issue-verified --issue 1`, verify issue status is `verified`
- **test_transition_issue_verified_invalid**: Issue with `planned` status, subprocess call, verify non-zero exit and error message

Fixtures: `tmp_path` with `.mantle/` directory, config.md, issue files, state.md.
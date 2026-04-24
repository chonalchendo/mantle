---
description: Use when code has architectural debt or design problems that need structured refactoring
argument-hint: <scope — file, module, or package path>
allowed-tools: Read, Edit, Write, Bash(mantle *), Bash(uv run pytest*), Bash(npm test*), Bash(cargo test*), Bash(go test*), Bash(git add*), Bash(git commit*), Bash(git diff*), Bash(git stash*), Bash(git log*), Bash(git status*), Agent, Grep, Glob, AskUserQuestion
---

Analyse a target scope, diagnose structural issues, generate radically different
refactoring approaches, and implement the user's chosen approach.

Be collaborative and concrete. Show real code, not abstract descriptions. The
user makes the final call on which approach to take.

## Dynamic Context

- **Current branch**: !`git branch --show-current`
- **Working tree status**: !`git status --short`
- **Recent commits**: !`git log --oneline -5`

## Step 1 — Determine scope

Record the stage:

    mantle stage-begin refactor

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Determine scope"
2. "Step 2 — Analyse the target"
3. "Step 3 — Select and load skills"
4. "Step 4 — Generate approaches"
5. "Step 5 — Compare and choose"
6. "Step 6 — Baseline tests"
7. "Step 7 — Implement"
8. "Step 8 — Verify and commit"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

If the user provided `$ARGUMENTS`, use that as the target scope (file path,
module, or package directory).

If no arguments were provided, ask the user:

> What do you want to refactor? Provide a file path, module, or package
> directory. Optionally describe the problem you're seeing (e.g., "too much
> duplication", "hard to add new features", "module is doing too many things").

If the working tree is dirty, warn and ask whether to commit/stash first.

## Step 2 — Analyse the target

Spawn an Agent (`subagent_type: "codebase-analyst"`) to analyse the target scope:

> Analyse the code at: {scope}
>
> Read ALL source files in the target scope. For each file, identify:
> 1. What it does (one sentence)
> 2. What it depends on and what depends on it
> 3. Structural issues — duplication, shallow abstractions, information leakage,
>    pass-through methods, tight coupling, unclear boundaries
>
> Report:
> - A dependency map (which modules import which)
> - Ranked list of structural issues with specific file paths and line numbers
> - What would break or get harder when extending this code

Record the analysis output — this is the diagnostic context for all subsequent
steps.

## Analysis scratchpad

Before synthesising findings, choosing approaches, or making recommendations,
use `<analysis>` blocks to organise your thinking. These blocks are internal
scratchpad — do NOT show them to the user. Strip them from any saved output.

```
<analysis>
- What are the most impactful structural issues from the analysis?
- Which issues are independent vs interconnected?
- What's the minimum change that would unlock extensibility?
- What constraints does the existing test suite impose on migration order?
</analysis>
```

Use `<analysis>` whenever you need to weigh competing approaches or draft a
synthesis before presenting it.

## Step 3 — Select and load skills

Run `mantle list-skills` to get the available skill catalog.

Based on the analysis from Step 2 and the user's problem description, select
the skills most relevant to this refactoring. Use `<analysis>` to reason about
which skills match the diagnosed issues — do not hardcode mappings.

Load each selected skill by running:

```bash
mantle compile
```

Then read the compiled skill files in `.claude/skills/*/SKILL.md`.

State which skills you loaded and why:

> **Skills loaded:**
> - `{skill-name}` — {why this skill is relevant to the diagnosed issues}
> - `{skill-name}` — {why}

## Step 4 — Generate approaches

Using the analysis and loaded skills, generate 2-3 **radically different**
refactoring approaches. Each approach must be a genuinely different strategy,
not a variation on the same idea.

For each approach, present:

1. **Name** — short, memorable label
2. **Strategy** — what structural change this makes (e.g., "extract Protocol",
   "merge modules", "introduce composition")
3. **Before/After sketch** — show the key interface or structure change
   concretely with code snippets, not prose
4. **Migration path** — what changes in what order to keep tests green at each
   step
5. **Blast radius** — which files change, what callers need updating
6. **Tradeoffs** — what you gain, what you give up

Present approaches one at a time. Discuss each with the user before moving to
the next.

## Step 5 — Compare and choose

Present a side-by-side comparison:

| | Approach A | Approach B | Approach C |
|---|---|---|---|
| Files changed | ... | ... | ... |
| Key benefit | ... | ... | ... |
| Key risk | ... | ... | ... |
| Migration complexity | ... | ... | ... |

Use AskUserQuestion to let the user choose which approach to implement.
Ask if they want to modify any aspect of the chosen approach before proceeding.

## Step 6 — Baseline tests

Read `CLAUDE.md` to detect the project's test command. Look for "Run tests:" or
common patterns like `uv run pytest`, `npm test`, `cargo test`, `go test ./...`.

Run the test suite and record pass/fail as baseline.

If tests already fail, warn: "Tests are failing before refactoring — proceed
with caution (no test safety net)."

## Step 7 — Implement

Implement the chosen approach following its migration path. Work incrementally:

1. Make one structural change at a time
2. After each change, run the test suite
3. If tests fail, fix before moving to the next change
4. If a change cannot be made without breaking tests, ask the user before
   proceeding

For large refactors spanning many files, use Agent
(`subagent_type: "implementer"`) for independent file changes that can be
parallelised.

**Retry on failure**: If tests fail after a change, attempt one fix. If the fix
also fails, stop and ask the user whether to revert the last change
(`git checkout -- {files}`) or debug further.

## Step 8 — Verify and commit

Run the full test suite one final time.

- **If tests pass**: `git add` changed files, commit as
  `refactor: {short description of the structural change}`
- **If tests fail**: report which tests broke and why. Ask the user whether to
  fix, revert (`git checkout -- .`), or commit anyway.

Display summary:

> ## Refactor Complete
>
> | | |
> |---|---|
> | **Approach** | {name} |
> | **Files changed** | {count} |
> | **Tests** | pass/fail |
> | **Key change** | {one sentence} |

Then briefly assess before recommending next steps:

- Was the refactoring straightforward, or were there surprises?
- Are there related areas that would benefit from similar treatment?
- Did the refactoring reveal other structural issues?

**Valid next commands** (recommend the best fit, not all of them):

- `/mantle:refactor` — recommend when the refactoring revealed related areas
  that need similar treatment.
- `/mantle:verify` — recommend when the refactoring was part of an active issue.
- `/mantle:simplify` — recommend when the refactoring introduced new code that
  could benefit from a bloat check.

Present one clear recommendation with a reason, then mention alternatives
briefly:

> **Recommended next step:** `/mantle:<command>` — [reason based on what you
> observed in this session]
>
> Other options: [brief list of alternatives with one-line descriptions]

## Output Format

One row per key result field in the Refactor Complete summary:

- **Approach**: <name> — **Files changed**: <count> — **Tests**: pass / fail — **Key change**: <one sentence>

Anti-patterns:
- No "I noticed" / "I'll do X next" framing
- No restating the diagnostic analysis already presented
- No trailing narrative paragraph after the summary table
- No emoji

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "refactor"

Keep the log under ~200 words following the session log format (Summary, What
Was Done, Decisions Made, What's Next, Open Questions).

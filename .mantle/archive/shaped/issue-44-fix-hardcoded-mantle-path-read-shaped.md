---
issue: 44
title: Fix hardcoded .mantle/ path reads in Claude Code prompts
approaches:
- A — mantle where CLI + prompt sweep
- B — CLI owns all file reads
- C — Symlink on storage-mode transition (ruled out by global-mode constraint)
chosen_approach: A — mantle where CLI + prompt sweep
appetite: medium batch
open_questions: []
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-09'
updated: '2026-04-09'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Problem

Issue 43 added global `.mantle/` storage mode (state lives at `~/.mantle/projects/<identity>/`). The CLI was migrated to route all path access through `core/project.resolve_mantle_dir()`, but the 22 Claude Code prompt files under `claude/commands/mantle/*.md` were never swept. They still use the `Read` tool with literal paths like `.mantle/state.md`, `.mantle/issues/issue-NN.md`, `.mantle/learnings/`. In global mode the project directory has no local `.mantle/`, so those reads fail or mislead — silently breaking the entire global-mode workflow for Claude Code users, which was the whole point of issue 43.

A grep audit found 22 prompt files containing ~95 hardcoded `.mantle/` references (mix of read calls and intentional doc mentions).

## Approaches considered

### Approach A — `mantle where` CLI + prompt sweep (CHOSEN)

A new thin CLI command prints `project.resolve_mantle_dir(cwd)` as an absolute path. Each affected prompt adds a "resolve path" step at the top of Step 1 that captures `MANTLE_DIR=$(mantle where)` via Bash, then uses `$MANTLE_DIR/...` in every subsequent `Read`-tool call.

**Appetite:** medium batch (3-5 days).

**Tradeoffs:** explicit, debuggable, cross-platform; resolver already exists in core; prompts stay idiomatic (Read tool for content, Bash for state queries). Cost: 22 files need mechanical edits, one Bash round-trip per session per prompt.

**Rabbit holes:** prompts that pass paths to subagents must pass the resolved path; help-text mentions of `.mantle/` should be left alone (they are docs, not reads); `build.md` orchestrates sub-commands and may inherit resolution from children.

**No-gos:** does not change `mantle install`, does not touch `~/.mantle/projects/<identity>/` migration, does not add per-file read subcommands.

### Approach B — CLI owns all file reads (rejected)

Add ~15 new `mantle read state`, `mantle read product-design`, `mantle read issue --number N`, `mantle list learnings`, etc. Prompts only use Bash output. **Rejected:** massive CLI surface explosion, loses Read tool rendering affordances (line numbers, markdown preview), breaks directory-glob patterns like `plan-stories` reading `learnings/*.md`, violates "one command, one job" principle.

### Approach C — Symlink on storage-mode transition (rejected)

`mantle storage --mode global` creates `./.mantle` as a symlink to `~/.mantle/projects/<identity>/`, gitignored. Prompts read `.mantle/state.md` and the filesystem resolves transparently. **Rejected:** the original motivation for global mode is "I cannot have ANY `.mantle/` artifact in this work repo" — even a gitignored symlink shows up in `ls` and the file explorer, violating the constraint. Also: spooky action at a distance, Windows symlink limitations.

## Why Approach A

1. Matches how the rest of Mantle's prompt/CLI contract already works — prompts call `mantle <subcommand>` for structured state operations and use the `Read` tool for content.
2. Claude's `Read` tool has rendering affordances (line numbers, markdown preview, caching) that Bash output cannot replicate.
3. The resolver function already exists; this is a thin wrapper, not new core logic.
4. Issue 43's learning explicitly flagged the prompt sweep as deferred out-of-scope; this issue is the documented follow-up. Issue author already chose this direction.

## Code Design

### Strategy

**New CLI command** (`src/mantle/cli/main.py`):

```python
@app.command(name=\"where\")
def where_command(
    path: Annotated[Path | None, Parameter(name=\"--path\", ...)] = None,
) -> None:
    \"\"\"Print the resolved .mantle/ directory absolute path.\"\"\"
    storage.run_where(project_dir=path)
```

**Thin CLI wrapper** (`src/mantle/cli/storage.py` — co-located with other storage concerns since path resolution is the read-side counterpart to `run_storage` and `run_migrate_storage`):

```python
def run_where(*, project_dir: Path | None = None) -> None:
    \"\"\"Print the resolved .mantle/ absolute path to stdout.\"\"\"
    if project_dir is None:
        project_dir = Path.cwd()
    resolved = project.resolve_mantle_dir(project_dir).resolve()
    print(resolved)
```

Key choices:
- **Plain `print()`, not `console.print()`** — Rich adds ANSI codes that pollute Bash captures. Output must be plumbing-grade clean.
- **`.resolve()`** to guarantee an absolute path even if `resolve_mantle_dir` returns a relative `./.mantle/`.
- **No side effects, no directory creation, no existence check** — pure read-only resolver. Each prompt that consumes the output handles missing-state messaging itself.

**Prompt sweep pattern.** Each affected prompt gets the same edit at the top of Step 1:

```markdown
First, resolve the .mantle/ directory absolute path:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` tool calls in this prompt must use `\$MANTLE_DIR/...`
in place of `.mantle/...`.
```

Then every literal `.mantle/state.md`, `.mantle/issues/issue-NN.md`, `.mantle/learnings/` becomes `\$MANTLE_DIR/state.md`, `\$MANTLE_DIR/issues/issue-NN.md`, `\$MANTLE_DIR/learnings/`. Help text and example mentions are left alone — they are documentation, not reads.

### Story decomposition (per issue 43 learning, max ~7 files per story)

- **Story 1** — Add `mantle where` CLI command. Implement `run_where` in `cli/storage.py`, register in `main.py`, unit tests in `tests/cli/test_storage.py` covering: prints correct path in local mode, prints correct path in global mode, custom `--path` flag, single-line output with no ANSI.
- **Story 2** — Sweep prompts batch 1 (7 files): `adopt.md`, `add-issue.md`, `add-skill.md`, `brainstorm.md`, `bug.md`, `build.md`, `design-product.md`.
- **Story 3** — Sweep prompts batch 2 (7 files): `design-system.md`, `fix.md`, `implement.md`, `plan-issues.md`, `plan-stories.md`, `retrospective.md`, `review.md`.
- **Story 4** — Sweep prompts batch 3 (6 files): `revise-product.md`, `revise-system.md`, `scout.md`, `shape-issue.md`, `simplify.md`, `verify.md`.
- **Story 5** — Integration test + grep audit. Test initialises a project in global mode, calls `mantle where`, verifies returned path is under `~/.mantle/projects/`, confirms a sample file written there is readable. Final grep audit confirms zero remaining hardcoded `.mantle/` Read-tool references.

Tests use `tmp_path` and a synthesised `HOME` to avoid touching real `~/.mantle/`.

### Fits architecture by

- Honours the `cli/ → core/` boundary — `run_where` lives in `cli/storage.py` and calls `project.resolve_mantle_dir()` from core. No new core code is needed.
- Follows the \"one command, one job\" principle (product design §7).
- Reuses the existing `storage.py` CLI module — read-side counterpart to `run_storage` (writes mode) and `run_migrate_storage` (moves files).
- Plugs into the prompt → CLI invocation pattern from system design (\"Claude Code commands invoke mantle CLI commands via Bash tool when they need runtime operations\").
- Closes the gap explicitly flagged in issue 43's learning note as deferred out-of-scope.

### Does not

- Does not add a `mantle read <kind>` family of subcommands. Prompts continue to use the Read tool for content.
- Does not change `project.resolve_mantle_dir()` or any other core code. Pure additive change in `cli/`.
- Does not modify how `mantle install` delivers commands to `~/.claude/commands/mantle/`. Prompts remain static markdown.
- Does not introduce per-project compiled prompts. `resume.md` and `status.md` remain the only compiled commands.
- Does not touch help-text or example mentions of `.mantle/` in prompt bodies (documentation, not file reads).
- Does not validate that `.mantle/` exists at the resolved path — each prompt handles missing-state messaging itself.
- Does not migrate any state, config, or files between local and global storage.
- Does not add `--global`, `--type config`, or other shaped output options to `mantle where` (YAGNI; one job).
- Does not change `introspect-project` or fold path resolution into it — separate concern (test/lint detection).
- Does not handle Windows-specific path quoting in the prompt sweep (Mantle is currently macOS/Linux-focused per existing CI).
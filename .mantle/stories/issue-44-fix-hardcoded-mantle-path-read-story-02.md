---
issue: 44
title: Sweep prompts batch 1 (adopt, add-issue, add-skill, brainstorm, bug, build,
  challenge)
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle user running prompts in global storage mode, I want `/mantle:adopt`, `/mantle:add-issue`, `/mantle:add-skill`, `/mantle:brainstorm`, `/mantle:bug`, `/mantle:build`, and `/mantle:challenge` to find the right `.mantle/` directory automatically so the workflow does not silently break.

## Depends On

Story 1 (the `mantle where` CLI command must exist before prompts can call it).

May run in parallel with Story 3, Story 4 (independent file sets).

## Approach

Mechanical sweep of 7 Claude Code prompt files. For each file, insert a "resolve path" instruction at the top of Step 1, then replace every literal `.mantle/...` Read-tool target with `$MANTLE_DIR/...`. Help-text mentions and example references are left alone (they are documentation, not file reads).

## Implementation

### Universal pattern (apply to every file in this story)

At the top of Step 1 (before any `.mantle/` Read calls), insert:

```markdown
First, resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls in this prompt must use
`$MANTLE_DIR/...` in place of `.mantle/...`.
```

Then within the prompt body:

- Replace `Read .mantle/state.md` → `Read $MANTLE_DIR/state.md`
- Replace `Read .mantle/product-design.md` → `Read $MANTLE_DIR/product-design.md`
- Replace `Read .mantle/issues/...` → `Read $MANTLE_DIR/issues/...`
- Replace `.mantle/learnings/`, `.mantle/shaped/`, `.mantle/stories/`, `.mantle/sessions/`, `.mantle/decisions.md`, etc. wherever they appear as actual read/glob targets.
- Leave alone: any `.mantle/` mention inside backticks that is purely descriptive (e.g., "saves to `.mantle/idea.md`"), inside the front-matter description, or referring to file paths inside `mantle save-*` flag values.
- Leave alone: `mkdir` / `mantle init` instruction text that references `.mantle/` as a concept.

### claude/commands/mantle/adopt.md (modify)

Sweep all hardcoded `.mantle/` Read targets. Notable lines (verify by grep — line numbers drift):
- The Step 1 / Step 2 prelude that reads `.mantle/`, `.mantle/state.md`, `.mantle/product-design.md`, `.mantle/system-design.md` to detect adoption state.
- Any later steps that re-read state or write design docs (write paths via `mantle save-*` CLI calls do not need updating — only Read tool targets do).

### claude/commands/mantle/add-issue.md (modify)

Sweep all `.mantle/issues/`, `.mantle/state.md`, `.mantle/product-design.md`, `.mantle/system-design.md` Read targets.

### claude/commands/mantle/add-skill.md (modify)

Sweep all `.mantle/state.md`, `.mantle/issues/`, and any vault-skill directory Read references.

### claude/commands/mantle/brainstorm.md (modify)

Sweep all `.mantle/state.md`, `.mantle/product-design.md`, `.mantle/idea.md`, `.mantle/brainstorms/` Read targets.

### claude/commands/mantle/bug.md (modify)

Sweep all `.mantle/state.md`, `.mantle/bugs/` Read targets.

### claude/commands/mantle/build.md (modify)

Sweep all `.mantle/state.md`, `.mantle/product-design.md`, `.mantle/system-design.md`, `.mantle/issues/`, `.mantle/shaped/`, `.mantle/stories/` Read targets. Note: `build.md` orchestrates sub-prompts (`shape-issue.md`, `plan-stories.md`, `implement.md`, etc.) — those sub-prompts will be swept in their own batches, so when `build.md` reads "follow Steps X-Y of `claude/commands/mantle/foo.md`", no path substitution is needed. Only direct `.mantle/` Reads inside `build.md` itself are in scope.

### claude/commands/mantle/challenge.md (modify)

Sweep all `.mantle/state.md`, `.mantle/idea.md`, `.mantle/challenges/`, `.mantle/research/` Read targets.

#### Design decisions

- **Single batch per story**: 7 files is at the edge of what one agent session handles cleanly per the issue 36 retrospective; no more.
- **Idempotent prelude**: The "resolve path" snippet is identical across every file so future readers can recognise it instantly and so a future migration is grep-replaceable.
- **No frontmatter changes**: Every Mantle prompt already declares `Bash(mantle *)` in `allowed-tools` (verified for adopt.md, idea.md, distill.md), so the `mantle where` invocation is already permitted.

## Tests

### tests/test_prompt_sweep.py (new file)

A single `test_batch_1_no_hardcoded_mantle_reads` test that uses `pathlib` and a regex to walk these 7 files and assert there are no remaining `Read .mantle/` or `Read \`.mantle/` references. The check is intentionally narrow — it only flags Read-tool targets, not documentation mentions. Pattern:

```python
import re
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent / "claude" / "commands" / "mantle"
BATCH_1_FILES = (
    "adopt.md",
    "add-issue.md",
    "add-skill.md",
    "brainstorm.md",
    "bug.md",
    "build.md",
    "challenge.md",
)
# Match "Read `.mantle/...`" or "Read .mantle/..." — Read-tool calls only
HARDCODED_READ_RE = re.compile(r"Read[^\n]*\\.mantle/")


def test_batch_1_no_hardcoded_mantle_reads() -> None:
    offenders = []
    for name in BATCH_1_FILES:
        text = (PROMPTS_DIR / name).read_text()
        for match in HARDCODED_READ_RE.finditer(text):
            offenders.append(f"{name}: {match.group(0)}")
    assert not offenders, "\n".join(offenders)
```

- **test_batch_1_includes_resolve_prelude**: Walks the same 7 files and asserts each contains the substring `MANTLE_DIR=$(mantle where)` (the universal prelude).

The test file is shared across the sweep stories — Story 3 and Story 4 will append additional batch tests to the same file, and Story 5 finalises it with the integration test and full audit.

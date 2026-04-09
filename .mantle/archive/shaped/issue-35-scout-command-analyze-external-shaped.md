---
issue: 35
title: Scout command — analyze external repos through project context lens
approaches:
- Prompt-only orchestrator — prompt handles clone/analyze/synthesize, core/scout.py
  handles only report CRUD
- Python-managed cloning — core/scout.py handles clone/cleanup via subprocess/tempfile,
  prompt handles analysis
- Full Python orchestrator — Python manages entire pipeline including agent dispatch
chosen_approach: Prompt-only orchestrator
appetite: medium batch
open_questions:
- None
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-07'
updated: '2026-04-07'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Chosen Approach: Prompt-only orchestrator

### Rationale

Follows Mantle's established pattern: prompt orchestrates, Python persists. The scout command is a prompt file (`scout.md`) that uses Bash tool for `git clone` to a temp dir, compiles project context inline, spawns parallel Agent subagents for analysis dimensions, synthesizes results, and saves via `mantle save-scout`. The core module (`core/scout.py`) handles only report CRUD (save/load/list) — exactly like `brainstorm.py`, `research.py`, and `learning.py`.

### Why not Python-managed cloning?

`git clone <url> <tmpdir>` via Bash tool is one command. Python subprocess management would duplicate what the prompt already does trivially, adding complexity without benefit. The temp dir lifecycle is simple: create before analysis, delete after save.

### Why not full Python orchestrator?

Agent dispatch lives in prompts (Mantle design principle #7). Python orchestration would fight the architecture.

## Code Design

### Strategy

**New modules:**
- `core/scout.py` — Report CRUD: `save_scout()`, `load_scout()`, `list_scouts()`. Pydantic model `ScoutReport` with frontmatter (date, author, repo_url, repo_name, tags). Follows `brainstorm.py` pattern exactly.
- `cli/scout.py` — CLI wiring: `save-scout` subcommand exposing `core/scout.py` functions.
- `claude/commands/mantle/scout.md` — Prompt orchestrator: clone → compile context → spawn parallel analysis agents → synthesize → save via CLI.

**Data model (`ScoutReport`):**
```python
class ScoutReport(pydantic.BaseModel, frozen=True):
    date: date
    author: str
    repo_url: str
    repo_name: str
    dimensions: tuple[str, ...]  # e.g. ("architecture", "patterns", "testing", "cli-design")
    tags: tuple[str, ...] = ("type/scout",)
```

**Report storage:** `.mantle/scouts/<date>-<repo-name>.md` with auto-increment for same-day collisions (established pattern).

**Analysis dimensions (prompt-defined):**
- Architecture (module structure, dependency direction, layering)
- Patterns & conventions (naming, error handling, testing style)
- Testing approach (framework, coverage strategy, fixture patterns)
- CLI design (command structure, argument patterns, help text)
- Domain-specific (derived from product design — what's relevant to our project?)

Each dimension agent receives: the cloned repo path + compiled project context (product design, system design, backlog, learnings, skills).

### Fits architecture by

- `core/scout.py` follows the thin-module pattern (like `brainstorm.py`, `research.py`) — CRUD only, no orchestration
- `cli/scout.py` is thin CLI wiring calling `core/scout.py` (cli/ → core/ dependency direction)
- `scout.md` prompt uses Agent subagents for parallel analysis (same pattern as `implement.md`)
- Reports in `.mantle/scouts/` follow the established directory-per-artifact pattern
- YAML frontmatter with Pydantic validation (project convention)
- State.md update after save (established pattern)

### Does not

- Does not manage git authentication — assumes the user can clone the repo (public or pre-authed)
- Does not persist the cloned repo — temp dir is cleaned up after analysis
- Does not integrate with knowledge engine queries (future enhancement, not in AC)
- Does not validate repo URL format — git clone will fail naturally with a clear error
- Does not handle private repo auth flows — out of scope per AC
- Does not implement custom dimension configuration — dimensions are prompt-defined, not user-configurable
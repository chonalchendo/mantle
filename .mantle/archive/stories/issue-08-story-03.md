---
issue: 8
title: Compiler engine (core/compiler.py) and status template
status: done
failure_log: null
tags:
  - type/story
  - status/done
---

## Implementation

Create `src/mantle/core/compiler.py` — the compilation engine that reads vault state, builds a context dict, renders Jinja2 templates, and writes compiled markdown commands to the target directory. Also create `claude/commands/mantle/status.md.j2` — the first compiled template.

### src/mantle/core/compiler.py

```python
"""Compile vault context into concrete markdown commands via Jinja2."""
```

#### Functions

- `collect_context(project_dir: Path) -> dict[str, Any]` — Read vault state and build a context dict for template rendering. Reads `state.md` frontmatter fields (`project`, `status`, `confidence`, `current_issue`, `current_story`, `skills_required`) and body sections (`summary`, `current_focus`, `blockers`, `recent_decisions`, `next_steps`). Returns a flat dict with all fields. Body sections are extracted via `_parse_body_sections()`. Missing optional files (idea.md, product-design.md) are silently skipped — the template handles absent values with Jinja2 conditionals.

- `source_paths(project_dir: Path) -> list[Path]` — Return all vault files that affect compilation output. Always includes `state.md`. Includes `idea.md`, `product-design.md`, `system-design.md` if they exist. Includes all `.j2` template files from the bundled template directory. Used by staleness detection to know what to hash.

- `template_dir() -> Path` — Resolve the bundled template directory inside the installed package. Uses `importlib.resources.files("mantle").joinpath("claude/commands/mantle")` (same pattern as `install.py`'s `_locate_bundled_claude_dir`). Returns only the `commands/mantle/` subdirectory since that's where `.j2` files live.

- `compile(project_dir: Path, target_dir: Path | None = None) -> list[str]` — Full compilation. Default `target_dir` to `~/.claude/commands/mantle/`. Collect context, find all `.j2` templates, render each via `templates.render_template()`, write output to `target_dir` (stripping `.j2` extension), save compilation manifest, return list of compiled template names.

- `compile_if_stale(project_dir: Path, target_dir: Path | None = None) -> list[str] | None` — Check staleness first. Hash current source paths via `manifest.hash_paths()`, compare against stored manifest via `manifest.is_compilation_stale()`. If stale, call `compile()` and return compiled names. If up to date, return `None`.

#### Internal helpers

- `_parse_body_sections(body: str) -> dict[str, str]` — Parse a markdown body into a dict of `section_name -> content`. Splits on `## ` headings. Keys are lowercased with spaces replaced by underscores (e.g., `"Current Focus"` → `"current_focus"`, `"Recent Decisions"` → `"recent_decisions"`). Values are the content between headings, stripped of leading/trailing whitespace.

- `_default_target_dir() -> Path` — Returns `Path.home() / ".claude" / "commands" / "mantle"`.

- `_manifest_path(project_dir: Path) -> Path` — Returns `project_dir / ".mantle" / ".compile-manifest.json"`.

#### Imports

```python
from importlib import resources
from typing import Any, TYPE_CHECKING

from mantle.core import manifest, state, templates

if TYPE_CHECKING:
    from pathlib import Path
```

#### Design decisions

- **Flat context dict.** State frontmatter fields and body sections are merged into one dict. Templates reference `{{ project }}`, `{{ status }}`, `{{ current_focus }}` directly — no nested `{{ state.project }}`. Simpler templates, simpler context.
- **Body section parsing, not raw body pass-through.** The status template needs individual sections (current focus, blockers, etc.), not a raw markdown blob. Parsing `## ` headings is robust — it's the same format every module writes.
- **Missing files are skipped, not errored.** A project at `idea` status won't have product-design.md yet. Compilation should still work — the template uses `{% if %}` guards for optional content.
- **Manifest path inside `.mantle/`.** The compilation manifest tracks vault file hashes, so it belongs with the vault. It's gitignored (prefixed with `.`).
- **Target dir defaults to `~/.claude/commands/mantle/`.** This is where Claude Code looks for commands. The compiler writes directly there.

### claude/commands/mantle/status.md.j2 (new file)

Jinja2 template that renders project status. Output fits within ~2-3K tokens.

```jinja2
# Project Status

**Project**: {{ project }}
**Status**: {{ status }}
**Confidence**: {{ confidence }}
{% if current_issue %}**Current Issue**: {{ current_issue }}{% endif %}
{% if current_story %}**Current Story**: {{ current_story }}{% endif %}

## Summary

{{ summary }}

## Current Focus

{{ current_focus }}

## Blockers

{{ blockers }}

## Recent Decisions

{{ recent_decisions }}

## Next Steps

{{ next_steps }}
{% if skills_required %}
## Skills Required

{% for skill in skills_required %}- {{ skill }}
{% endfor %}{% endif %}
```

The exact template formatting may be adjusted during implementation, but the structure covers all acceptance criteria fields: project name, status, current focus, blockers, recent decisions, next steps.

### .mantle/.gitignore (modify via project.py)

Update `GITIGNORE_CONTENT` in `src/mantle/core/project.py` to add `.compile-manifest.json`:

```
# Compilation manifest
.compile-manifest.json
```

This only affects newly-created projects. Existing projects (like mantle itself) need a manual `.gitignore` update.

## Tests

### tests/core/test_compiler.py

Test fixtures create a `tmp_path` with `.mantle/` directory, `state.md`, and optionally `product-design.md`. Mock `state.resolve_git_identity()` to return a fixed email. Create a temporary template directory with a test `.j2` template.

- **collect_context**: returns dict with state frontmatter fields (project, status, confidence)
- **collect_context**: returns dict with parsed body sections (summary, current_focus, blockers, recent_decisions, next_steps)
- **collect_context**: body section keys are lowercased with underscores
- **collect_context**: handles state.md with placeholder body content
- **source_paths**: includes state.md
- **source_paths**: includes product-design.md when it exists
- **source_paths**: excludes product-design.md when it doesn't exist
- **source_paths**: includes `.j2` template files
- **template_dir**: returns a directory that exists
- **template_dir**: returned directory contains `.j2` files (after status.md.j2 is added)
- **compile**: renders template and writes output to target_dir
- **compile**: output file has `.j2` extension stripped
- **compile**: saves compilation manifest
- **compile**: returns list of compiled template names
- **compile**: creates target_dir if it doesn't exist
- **compile_if_stale**: compiles when no manifest exists (first run)
- **compile_if_stale**: returns None when sources unchanged
- **compile_if_stale**: recompiles when a source file changes
- **_parse_body_sections**: parses standard state.md body into sections
- **_parse_body_sections**: handles body with single section
- **_parse_body_sections**: handles empty body

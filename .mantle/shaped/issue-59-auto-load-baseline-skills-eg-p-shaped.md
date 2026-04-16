---
issue: 59
title: Auto-load baseline skills (e.g. python-314) based on project constraints
approaches:
- Inline helper in core/skills.py
- New core/baseline.py module with pure mapping
- State-backed baseline_skills in state.md seeded by mantle init
chosen_approach: New core/baseline.py module with pure mapping
appetite: small batch
open_questions:
- Should baseline resolution also scan src/ imports (e.g. detect pydantic usage) or
  is pyproject.toml-only enough for v1?
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-16'
updated: '2026-04-16'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approaches

### A — Inline helper in core/skills.py
Tiny `_resolve_baseline_skills()` function added directly to `skills.py`.
`auto_update_skills` and `compile_skills` union baseline with detected skills.

- **Tradeoffs**: Smallest diff; keeps logic near usage. But `skills.py` is already large (1200+ lines) and the baseline concept is distinct enough to deserve its own home.
- **Rabbit holes**: Temptation to keep adding baseline-related helpers into `skills.py`.
- **No-gos**: No schema changes; no state persistence.

### B — New core/baseline.py module (CHOSEN)
Create `src/mantle/core/baseline.py` with a pure mapping function and a public `resolve_baseline_skills(project_dir)` that reads `pyproject.toml` via `tomllib`, parses `requires-python`, and returns matching baseline skill names.

- **Tradeoffs**: One extra module but single responsibility; easy to unit-test the mapping in isolation; obvious extension point (framework baselines, language baselines) without bloating `skills.py`.
- **Rabbit holes**: Over-engineering a registry before we have more baselines.
- **No-gos**: Not a plug-in registry — just a flat mapping function.

### C — State-backed baseline_skills in state.md
Add a `baseline_skills:` list field to `state.md`, seeded by `mantle init` after detecting project constraints. `update-skills` unions this list with detected matches.

- **Tradeoffs**: User-editable, persistent, inspectable via raw markdown. But larger change: state schema update, migration of existing projects, init-time detection logic.
- **Rabbit holes**: Migration of existing `.mantle/` directories; handling the case where user edits `baseline_skills` but then `requires-python` changes.
- **No-gos**: Not needed for AC; acceptance criteria only require resolution-time computation.

## Comparison

| | A (inline) | B (new module) | C (state-backed) |
|---|---|---|---|
| Appetite | small batch | small batch | medium batch |
| Key benefit | smallest diff | clean separation | user-editable |
| Key risk | bloats skills.py | one more module | schema+migration |
| Complexity | low | low | medium |

## Chosen: Approach B

Baseline-skill resolution is its own concept and deserves its own module. `skills.py` handles vault CRUD and detection; `baseline.py` handles project-constraint → baseline-set resolution. Both are small, but B keeps future growth (framework baselines, language baselines) out of `skills.py`. Issue body explicitly mentions 'a small config module' as an option.

**Appetite**: small batch (1-2 sessions).

## Strategy

New module `src/mantle/core/baseline.py`:

```python
def resolve_baseline_skills(project_dir: Path) -> tuple[str, ...]:
    """Return baseline skill names for project constraints."""
    # Parse pyproject.toml requires-python, map to skill names,
    # gate each on skill_exists() in vault. Emit warnings.warn for
    # missing vault entries. Return empty tuple on any failure.

def _python_baseline_for_version(requires_python: str) -> tuple[str, ...]:
    """Pure mapping: 'requires-python' string -> baseline skill names."""
    # 3.14+ -> ('python-314',)
```

Modifications to `core/skills.py`:

- `auto_update_skills(project_dir, issue_number)` — compute `baseline = resolve_baseline_skills(project_dir)`, union with `detected`, merge into state + issue frontmatter. Return type changes to `tuple[list[str], list[str]]` — `(baseline, detected_new)` — so CLI can split reporting.
- `compile_skills(project_dir, issue=N)` — union `resolve_baseline_skills(project_dir)` into the effective `skills_filter` so baselines are compiled to `.claude/skills/` even if an issue's frontmatter predates baseline support.

Modifications to `cli/main.py::update_skills_command`:

- Split report into two groups: `Baseline skills (always loaded): python-314` and `Issue-matched skills (from body scan): ...`. Both printed to stderr per cli-design-best-practices (stdout stays clean for piping).

## Fits architecture by

- `core/` never imports from `cli/` — baseline.py stays in core.
- Uses `tomllib` (3.14 stdlib) per python-314 skill (this project targets 3.14+, no third-party TOML parser needed).
- Vault-absence is soft: follows the same `warnings.warn` + continue pattern as `compile_skills` for missing skills (skills.py:1024-1027).
- Matches one-module-one-job rule (system-design.md 'One command, one job' — generalises to modules).

## Does not

- Does not add a `baseline_skills` field to `state.md` schema (out of scope; AC doesn't require persistence).
- Does not seed anything during `mantle init` (no init-time constraint detection; baseline is computed lazily at update-skills/compile time).
- Does not handle non-Python manifests (package.json, Cargo.toml) — mantle is a single-language project.
- Does not migrate existing `.mantle/` directories — baseline is computed, not stored.
- Does not introduce a plug-in or entry-point registry — the mapping is a flat, local function.
- Does not modify `core/state.py` — existing `update_skills_required(additive=True)` is sufficient.
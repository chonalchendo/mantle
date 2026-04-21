---
issue: 84
title: Cost-policy template + mantle init drops it in
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a Mantle maintainer, I want one authoritative policy doc naming default models per stage, so cost choices are visible and revisable in one place rather than scattered across prompts.

## Depends On

None — independent (first in the chain).

## Approach

Follows the existing `vault-templates/*.md` pattern: ship a bundled template and copy it into new projects at `mantle init` time, same way `config.md` and `tags.md` are dropped in by `core.project.init_project`. The template carries a YAML frontmatter `presets:` map so downstream Python (story 2) can parse it without prose parsing. No active migration for existing projects — story 2's loader falls back to a hardcoded balanced preset when `cost-policy.md` is absent.

## Implementation

### vault-templates/cost-policy.md (new file)

New template matching the 3-preset structure from the shaped doc. Frontmatter is machine-readable; body is one paragraph of rationale per preset plus a "how to use" section.

```yaml
---
presets:
  budget:
    shape: sonnet
    plan_stories: sonnet
    implement: haiku
    simplify: haiku
    verify: sonnet
    review: haiku
    retrospective: haiku
  balanced:
    shape: opus
    plan_stories: sonnet
    implement: sonnet
    simplify: sonnet
    verify: sonnet
    review: haiku
    retrospective: haiku
  quality:
    shape: opus
    plan_stories: opus
    implement: opus
    simplify: sonnet
    verify: sonnet
    review: sonnet
    retrospective: sonnet
tags:
  - type/config
---

## Cost Policy

Per-stage model defaults for `/mantle:build`. Three presets:

- **budget** — cheapest viable path. Sonnet for shape/plan/verify; Haiku for mechanical stages.
- **balanced** (default) — Opus where reasoning compounds (shape), Sonnet everywhere else, Haiku on the trivially-mechanical end.
- **quality** — Opus on everything that writes code or makes design decisions. Sonnet only on mechanical finish-line stages.

## How to use

Select a preset in `.mantle/config.md` frontmatter under a `models:` block:

    models:
      preset: balanced
      overrides:
        implement: opus    # escape hatch for a specific stage

Overrides beat preset beat hardcoded fallback.
```

### src/mantle/core/project.py (modify)

1. Import `resources` from `importlib` (mirrors `cli/install.py:_locate_bundled_claude_dir`).
2. Add a new module-level constant `COST_POLICY_FILENAME = "cost-policy.md"`.
3. In `init_project`, after `config.md` and `tags.md` are written but before `state.create_initial_state`, copy the bundled template to `mantle_path / COST_POLICY_FILENAME`. Implementation:

   ```python
   template = resources.files("mantle").joinpath(
       "vault-templates", "cost-policy.md"
   )
   (mantle_path / COST_POLICY_FILENAME).write_text(
       template.read_text(encoding="utf-8"), encoding="utf-8"
   )
   ```

   Use `write_text` directly (not `vault.write_note`) because the template is pre-rendered — no frontmatter synthesis needed.

#### Design decisions

- **Template lives in vault-templates/, not inlined in project.py.** The existing bundled-template pattern (idea/issue/story/etc.) uses `vault-templates/`. Keeping cost-policy.md there means one convention, one place to edit the defaults. `pyproject.toml` already force-includes `vault-templates` into the wheel (line 30), so no build-system change needed.
- **No idempotent re-copy on existing projects.** Legacy projects without `cost-policy.md` rely on story 2's hardcoded `_FALLBACK_STAGE_MODELS` — not a silent migration. This avoids the open question about `mantle install` side-effects on a given project.
- **Write via write_text, not write_note.** The template is pre-rendered with its own frontmatter. Running it through `vault.write_note`'s Pydantic-model pathway would require a schema we don't otherwise need.

## Tests

### tests/core/test_project.py (modify)

Extend `TestInitProject` with:

- **test_creates_cost_policy_md**: `init_project(tmp_path, "test-project")` → `(tmp_path / ".mantle" / "cost-policy.md").exists()`.
- **test_cost_policy_has_preset_frontmatter**: After init, the file parses as frontmatter (via `_read_frontmatter_and_body`) and has a `presets` key with `budget`, `balanced`, `quality` entries, each with all 7 stage fields (`shape`, `plan_stories`, `implement`, `simplify`, `verify`, `review`, `retrospective`).
- **test_cost_policy_preserves_template_body**: After init, the file body contains the substrings `balanced` and `How to use` (light sanity check that the rendered body was copied verbatim).

Also: add a module-level constant test under `TestTemplateConstants` — import and reference `COST_POLICY_FILENAME` so the new constant is covered.

Fixtures: none new — existing `_mock_git` autouse fixture is sufficient.

---
issue: 29
title: Improve verification strategy — structured first-use and prompted evolution
approaches:
- Prompt-only — structured template
- Core introspection + prompt updates
- Minimal core helper + prompt-driven structure
chosen_approach: Minimal core helper + prompt-driven structure
appetite: small batch
open_questions:
- none
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-04'
updated: '2026-04-04'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approach C: Minimal core helper + prompt-driven structure

Add a small introspect_project() function to core/verify.py that reads key project files and returns detected commands. Keep strategy as a plain string with markdown sections. Update verify.md prompt for structured first-use and evolution. Add CLI mantle introspect-project for prompt access. Build pipeline calls mantle introspect-project then mantle save-verification-strategy.

### Strategy

- Add introspect_project(project_root) -> dict to core/verify.py — reads CLAUDE.md, pyproject.toml, Justfile/Makefile. Returns {test_command, lint_command, check_command}.
- Add generate_structured_strategy(introspection: dict) -> str to core/verify.py — renders a markdown-formatted strategy string from introspection results.
- Add CLI command mantle introspect-project in cli/verify.py — calls core function, prints JSON.
- Update verify.md Step 3 first-use flow — call mantle introspect-project, propose structured strategy, confirm.
- Add evolution prompt after Step 7 in verify.md — detect corrections, offer to update.
- Update build.md verify override — call mantle introspect-project + mantle save-verification-strategy when none exists.

### Fits architecture by

- Core function in core/verify.py — extends existing module.
- CLI wrapper in cli/verify.py — thin routing.
- Prompt changes in verify.md — follows existing prompt patterns.
- core/ reads filesystem only, no imports from cli/.

### Does not

- Add structured pydantic model for strategy sections (string is sufficient)
- Support non-Python project detection (package.json, Cargo.toml)
- Parse CI config files
- Silently overwrite existing strategies (AC 7)
- Migrate existing strategy format
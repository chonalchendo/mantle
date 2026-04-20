---
issue: 78
title: 'story-1: import-linter Python API entry point and INI config'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-20'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

Use `importlinter.cli.lint_imports` (returns int exit code, bootstraps configuration at import time), NOT `importlinter.application.use_cases.lint_imports` — the latter requires a manual `importlinter.configuration.configure()` first, otherwise raises `KeyError: 'USER_OPTION_READERS'`. The CLI entry point is the supported integration surface as of import-linter 2.11. INI config (`[importlinter]` + `[importlinter:contract:<id>]` flat sections) parses fine in 2.11 — no need to switch to TOML for ad-hoc test fixtures.
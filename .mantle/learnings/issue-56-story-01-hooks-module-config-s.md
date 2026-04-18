---
issue: 56
title: 'story-01: hooks module + config schema'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-18'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

Patterns from story 01 that later stories should carry: (1) project.init_project(path, name) requires BOTH args — use a throwaway project name in tests. (2) project.resolve_mantle_dir(tmp_path) works without git stubbing when tmp_path isn't a repo. (3) caplog + custom logger: set_level with logger= kwarg targets the hooks module directly. (4) YAML frontmatter parsing via the private _load_hooks_env bypasses vault.read_note so malformed configs don't break the seam. (5) Tests use real bash scripts, not subprocess mocks — catches argv-order bugs.
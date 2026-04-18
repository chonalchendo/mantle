---
issue: 56
title: 'story-02: transition+shaping dispatch'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-18'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

Patterns from story 02 for story 03: (1) existing shaping tests use @patch('mantle.core.shaping.state.resolve_git_identity', ...) as a decorator — necessary because save_shaped_issue reads git config. (2) shaping does NOT transition issue status — issue stays at its prior status (e.g. 'planned'), shaped doc is purely additive. (3) the seed helper in test_issues.py is _write_issue_direct(project_dir, issue_number, *, status) with title=f'Issue {N}' — not _seed_project_with_issue. (4) monkeypatch target 'mantle.core.issues.hooks.dispatch' works because issues.py uses 'from mantle.core import hooks'.
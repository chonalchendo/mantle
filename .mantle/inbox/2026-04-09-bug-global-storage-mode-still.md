---
date: '2026-04-09'
author: 110059232+chonalchendo@users.noreply.github.com
title: 'BUG: global storage mode still leaves a stub .mantle/config.md in project
  dir'
source: ai
status: open
tags:
- type/inbox
- status/open
---

Issue 44's shape doc and issue text claim global mode means 'work repos cannot have ANY .mantle/ artifact'. But src/mantle/core/migration.py::migrate_to_global (line 48-57) intentionally rebuilds a stub .mantle/config.md with storage_mode:global after copying. This is load-bearing — resolve_mantle_dir reads it to discover the storage mode — so the resolver requires the stub to exist. That contradicts the global-mode user's stated constraint. Options: (a) move storage_mode detection to a project-root marker that is not inside .mantle/ (maybe ~/.mantle/projects_index.json keyed by project identity), (b) detect global mode from existence of ~/.mantle/projects/<identity>/ alone, (c) document and accept the stub (update issue 43/44 messaging). Discovered during issue 44 story 5 when the integration test had to be adjusted to match actual behavior.
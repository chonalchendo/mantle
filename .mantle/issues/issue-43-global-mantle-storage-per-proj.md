---
title: Global .mantle/ storage — per-project folders under ~/.mantle/ instead of in-repo
status: planned
slice:
- core
- cli
- tests
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

In workplace environments where modifying .gitignore isn't desirable (shared repos, strict git policies), storing .mantle/ in the repo root creates friction. Users either have to modify .gitignore (which shows up in diffs) or risk accidentally committing .mantle/ contents. A global storage option would store project context at ~/.mantle/<project-hash>/ instead of in the repo root.

## What to build

An alternative storage mode where .mantle/ context lives at ~/.mantle/<project>/ rather than in the repo root. This requires:

1. A project identity mechanism (hash of repo root path or git remote URL)
2. A configuration option to opt into global storage (per-project or global default)
3. All core functions that read/write .mantle/ must resolve the actual path through a single function
4. Migration tooling to move existing in-repo .mantle/ to global storage

## Acceptance criteria

- As a user, I can configure Mantle to store context at ~/.mantle/ instead of in-repo
- All existing commands work identically regardless of storage location
- A migration command moves existing .mantle/ to global storage
- Project identity is stable (doesn't change if repo is moved on disk, based on git remote)
- Default behavior is unchanged (in-repo .mantle/) for backwards compatibility